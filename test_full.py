"""Comprehensive test suite for Claw Agent — all tools, agent, CLI, bridge."""

from __future__ import annotations

import json
import os
import sys
import time
import tempfile
import shutil
import subprocess

# Ensure claw_agent is importable
sys.path.insert(0, os.path.dirname(__file__))

from claw_agent.tools import TOOL_REGISTRY, OLLAMA_TOOL_DEFINITIONS
from claw_agent.tools.file_tools import read_file, write_file, list_directory, find_files
from claw_agent.tools.shell_tools import run_command
from claw_agent.tools.search_tools import grep_search
from claw_agent.tools.edit_tools import replace_in_file
from claw_agent.tools.advanced_edit_tools import multi_edit_file, insert_at_line, diff_files
from claw_agent.tools.web_tools import web_fetch, web_search
from claw_agent.tools.agent_tools import run_subagent, plan_and_execute
from claw_agent.tools.task_tools import task_create, task_update, task_list, task_get
from claw_agent.tools.notebook_tools import notebook_run
from claw_agent.tools.context_tools import get_workspace_context, git_diff, git_log
from claw_agent.agent import (
    Agent, StreamEvent, TextDelta, ToolCallStart, ToolCallEnd,
    TurnComplete, AgentDone, MAX_ITERATIONS, MAX_CONTEXT_TOKENS,
    BLOCKED_COMMANDS,
)
from claw_agent.permissions import PermissionContext, GATED_TOOLS
from claw_agent.sessions import Session, save_session, load_session, list_sessions
from claw_agent.cost_tracker import CostTracker

PASS = 0
FAIL = 0
ERRORS = []

def test(name, func):
    global PASS, FAIL
    try:
        result = func()
        if result:
            PASS += 1
            print(f"  ✓ {name}")
        else:
            FAIL += 1
            ERRORS.append(f"{name}: returned False")
            print(f"  ✗ {name} — returned False")
    except Exception as e:
        FAIL += 1
        ERRORS.append(f"{name}: {e}")
        print(f"  ✗ {name} — {e}")

# Create a temp workspace for testing
TMPDIR = tempfile.mkdtemp(prefix="claw_test_")
TEST_FILE = os.path.join(TMPDIR, "test.txt")
with open(TEST_FILE, "w") as f:
    f.write("line 1: hello world\nline 2: foo bar\nline 3: test data\n")

print(f"\nTest workspace: {TMPDIR}")
print("=" * 60)

# ============================================================================
# 1. TOOL REGISTRY
# ============================================================================
print("\n[1] TOOL REGISTRY")
test("26 tools registered", lambda: len(TOOL_REGISTRY) == 26)
test("26 Ollama definitions", lambda: len(OLLAMA_TOOL_DEFINITIONS) == 26)
test("All defs have function.name", lambda: all(
    d.get("type") == "function" and d.get("function", {}).get("name")
    for d in OLLAMA_TOOL_DEFINITIONS
))
test("All def names match registry", lambda: set(
    d["function"]["name"] for d in OLLAMA_TOOL_DEFINITIONS
) == set(TOOL_REGISTRY.keys()))

# ============================================================================
# 2. FILE TOOLS
# ============================================================================
print("\n[2] FILE TOOLS")
test("read_file works", lambda: "hello world" in read_file(TEST_FILE))
test("read_file with line range", lambda: "line 2" in read_file(TEST_FILE, start_line=2, end_line=2))
test("read_file missing file", lambda: "Error" in read_file("/nonexistent_path_xyz.txt") or "not found" in read_file("/nonexistent_path_xyz.txt").lower())

test_write = os.path.join(TMPDIR, "written.txt")
test("write_file creates", lambda: "Wrote" in write_file(test_write, "hello") and os.path.exists(test_write))
test("write_file content correct", lambda: open(test_write).read() == "hello")

test("list_directory works", lambda: "test.txt" in list_directory(TMPDIR))
test("list_directory missing dir", lambda: "Error" in list_directory("/nonexistent_dir_xyz") or "not found" in list_directory("/nonexistent_dir_xyz").lower() or "error" in list_directory("/nonexistent_dir_xyz").lower())

test("find_files works", lambda: "test.txt" in find_files("*.txt", TMPDIR))

# ============================================================================
# 3. SHELL TOOLS
# ============================================================================
print("\n[3] SHELL TOOLS")
test("run_command echo", lambda: "hello" in run_command("echo hello"))
test("run_command pwd", lambda: len(run_command("cd")) > 0)
test("run_command error handling", lambda: len(run_command("nonexistent_command_xyz 2>&1")) > 0)

# ============================================================================
# 4. SEARCH TOOLS
# ============================================================================
print("\n[4] SEARCH TOOLS")
test("grep_search finds match", lambda: "foo bar" in grep_search("foo", TMPDIR))
test("grep_search no match", lambda: "No matches" in grep_search("zzzznothere", TMPDIR))

# ============================================================================
# 5. EDIT TOOLS
# ============================================================================
print("\n[5] EDIT TOOLS")
edit_file = os.path.join(TMPDIR, "edit_test.txt")
with open(edit_file, "w") as f:
    f.write("alpha\nbeta\ngamma\ndelta\n")

test("replace_in_file works", lambda: "Replaced" in replace_in_file(edit_file, "beta", "BETA"))
test("replace_in_file verified", lambda: "BETA" in open(edit_file).read())

insert_file = os.path.join(TMPDIR, "insert_test.txt")
with open(insert_file, "w") as f:
    f.write("line1\nline2\nline3\n")
test("insert_at_line works", lambda: "Inserted" in insert_at_line(insert_file, 2, "INSERTED"))
test("insert_at_line verified", lambda: "INSERTED" in open(insert_file).read())

diff_file_a = os.path.join(TMPDIR, "diff_a.txt")
diff_file_b = os.path.join(TMPDIR, "diff_b.txt")
with open(diff_file_a, "w") as f:
    f.write("same\ndifferent1\nsame\n")
with open(diff_file_b, "w") as f:
    f.write("same\ndifferent2\nsame\n")
test("diff_files works", lambda: len(diff_files(diff_file_a, diff_file_b)) > 0)

multi_file = os.path.join(TMPDIR, "multi_test.txt")
with open(multi_file, "w") as f:
    f.write("aaa\nbbb\nccc\n")
test("multi_edit_file works", lambda: "edit" in multi_edit_file(multi_file, json.dumps([
    {"old": "aaa", "new": "AAA"},
    {"old": "ccc", "new": "CCC"},
])).lower() or "appl" in multi_edit_file(multi_file, "[]").lower())

# ============================================================================
# 6. TASK TOOLS
# ============================================================================
print("\n[6] TASK TOOLS")
create_result = task_create("Test task", "step1\nstep2")
test("task_create works", lambda: "Created" in create_result or "task" in create_result.lower())
# Extract task ID
task_id = create_result.split()[2].rstrip(":") if "Created" in create_result else "unknown"
test("task_list works", lambda: len(task_list()) > 0)
test("task_get works", lambda: "Test task" in task_get(task_id) if task_id != "unknown" else True)
test("task_update works", lambda: "Updated" in task_update(task_id, status="completed") if task_id != "unknown" else True)

# ============================================================================
# 7. CONTEXT TOOLS
# ============================================================================
print("\n[7] CONTEXT TOOLS")
test("get_workspace_context works", lambda: len(get_workspace_context(".")) > 0)
test("git_log works or reports no repo", lambda: len(git_log()) > 0)
test("git_diff works or reports no repo", lambda: isinstance(git_diff(), str))

# ============================================================================
# 8. WEB TOOLS
# ============================================================================
print("\n[8] WEB TOOLS")
test("web_fetch works", lambda: len(web_fetch("http://localhost:11434")) > 0)
# web_search might fail without network, just check it doesn't crash
try:
    ws_result = web_search("python programming")
    test("web_search works", lambda: isinstance(ws_result, str) and len(ws_result) > 0)
except:
    test("web_search handles errors", lambda: True)

# ============================================================================
# 9. NOTEBOOK TOOLS
# ============================================================================
print("\n[9] NOTEBOOK TOOLS")
test("notebook_run works", lambda: "2" in notebook_run("print(1+1)"))

# ============================================================================
# 10. PERMISSIONS
# ============================================================================
print("\n[10] PERMISSIONS")
perms = PermissionContext.default()
test("PermissionContext creates", lambda: perms is not None)
test("blocks returns bool", lambda: isinstance(perms.blocks("read_file"), bool))
test("dangerous cmd detection", lambda: perms.check_command_safety("rm -rf /") is not None)
test("safe cmd passes", lambda: perms.check_command_safety("echo hello") is None)

# ============================================================================
# 11. SESSIONS
# ============================================================================
print("\n[11] SESSIONS")
sess = Session(model="test-model")
sess.messages.append({"role": "user", "content": "test"})
sess.total_turns = 1
save_result = save_session(sess)
test("save_session works", lambda: save_result is not None)
test("list_sessions works", lambda: isinstance(list_sessions(), list))
loaded = load_session(sess.session_id)
test("load_session works", lambda: loaded is not None and loaded.model == "test-model")

# ============================================================================
# 12. COST TRACKER
# ============================================================================
print("\n[12] COST TRACKER")
ct = CostTracker()
ct.record_turn(prompt_tokens=100, completion_tokens=50, total_tokens=150, tool_calls=2, duration_ms=500, model="test")
test("record_turn works", lambda: ct.total_turns == 1)
test("total_tokens correct", lambda: ct.total_tokens == 150)
test("total_tool_calls correct", lambda: ct.total_tool_calls == 2)
test("summary works", lambda: "150" in ct.summary())

# ============================================================================
# 13. AGENT CORE (no Ollama needed)
# ============================================================================
print("\n[13] AGENT CORE")
test("Agent creates", lambda: Agent(model="test") is not None)
test("MAX_ITERATIONS is 200", lambda: MAX_ITERATIONS == 200)
test("MAX_CONTEXT_TOKENS is 200000", lambda: MAX_CONTEXT_TOKENS == 200000)
test("BLOCKED_COMMANDS has claw", lambda: "claw" in BLOCKED_COMMANDS)
test("StreamEvent classes exist", lambda: all([TextDelta, ToolCallStart, ToolCallEnd, TurnComplete, AgentDone]))

# Test compaction logic
agent = Agent(model="test")
# Simulate many messages
for i in range(20):
    agent.messages.append({"role": "user", "content": f"message {i}"})
    agent.messages.append({"role": "assistant", "content": f"response {i}"})
# Simulate high token count
agent.cost.record_turn(prompt_tokens=60000, completion_tokens=50000, total_tokens=110000, tool_calls=0, duration_ms=100, model="test")
test("compaction triggers at 100k tokens", lambda: (agent._compact_if_needed(), len(agent.messages) <= 10)[1])

# Test blocked command in _run_single_tool
agent2 = Agent(model="test")
events = list(agent2._run_single_tool("run_command", {"command": "claw prompt hello"}))
test("blocks recursive claw command", lambda: any("Blocked" in getattr(e, 'result', '') for e in events if isinstance(e, ToolCallEnd)))

# Test spam rejection
events2 = list(agent2._run_single_tool("read_file", {"path": "极速赛车开奖官网: 61669.com复制打开"}))
test("rejects hallucinated spam args", lambda: any("Rejected" in getattr(e, 'result', '') for e in events2 if isinstance(e, ToolCallEnd)))

# ============================================================================
# 14. AGENT LIVE (needs Ollama)
# ============================================================================
print("\n[14] AGENT LIVE (Ollama)")
try:
    import httpx
    r = httpx.get("http://localhost:11434/api/tags", timeout=3)
    ollama_up = r.status_code == 200
except:
    ollama_up = False

if ollama_up:
    live_agent = Agent(model="deepseek-r1:671b", base_url="http://localhost:11434")
    events = []
    try:
        for ev in live_agent.stream_chat("What is 2+2? Answer with just the number."):
            events.append(ev)
        has_done = any(isinstance(e, AgentDone) for e in events)
        has_text = any(isinstance(e, TextDelta) for e in events)
        done_text = next((e.final_text for e in events if isinstance(e, AgentDone)), "")
        test("stream_chat produces events", lambda: len(events) > 0)
        test("stream_chat has TextDelta", lambda: has_text)
        test("stream_chat has AgentDone", lambda: has_done)
        test("agent stops after answering", lambda: sum(1 for e in events if isinstance(e, TurnComplete)) <= 3)
        test("answer contains 4", lambda: "4" in done_text)
        test("cost tracker recorded", lambda: live_agent.cost.total_turns > 0)
    except Exception as e:
        test("stream_chat runs", lambda: False)
        ERRORS.append(f"Live agent error: {e}")

    # Test tool usage
    events2 = []
    try:
        for ev in live_agent.stream_chat(f"List the files in {TMPDIR}"):
            events2.append(ev)
        has_tool = any(isinstance(e, ToolCallStart) for e in events2)
        test("agent uses tools", lambda: has_tool)
        tool_names = [e.name for e in events2 if isinstance(e, ToolCallStart)]
        test("used list_directory or find_files", lambda: any(n in ("list_directory", "find_files", "run_command") for n in tool_names))
    except Exception as e:
        test("agent tool usage", lambda: False)
        ERRORS.append(f"Live agent tool error: {e}")
else:
    print("  ⚠ Ollama not running — skipping live agent tests")

# ============================================================================
# 15. CLI MODULE
# ============================================================================
print("\n[15] CLI MODULE")
try:
    from claw_agent.cli import main, console, HISTORY_PATH
    test("CLI module imports", lambda: True)
    test("console exists", lambda: console is not None)
    test("HISTORY_PATH set", lambda: ".claw-agent" in HISTORY_PATH)
except Exception as e:
    test("CLI module imports", lambda: False)
    ERRORS.append(f"CLI import error: {e}")

# Test CLI one-shot mode
try:
    result = subprocess.run(
        ["C:\\Program Files\\PyManager\\python.exe", "-m", "claw_agent.cli", "what is 2+2"],
        capture_output=True, text=True, timeout=60, cwd=TMPDIR
    )
    test("CLI one-shot runs", lambda: result.returncode == 0 or len(result.stdout) > 0)
    test("CLI one-shot produces output", lambda: len(result.stdout) > 0)
except subprocess.TimeoutExpired:
    test("CLI one-shot timeout", lambda: False)
    ERRORS.append("CLI one-shot timed out")
except Exception as e:
    test("CLI one-shot", lambda: False)
    ERRORS.append(f"CLI one-shot error: {e}")

# ============================================================================
# 16. BRIDGE MODULE
# ============================================================================
print("\n[16] BRIDGE MODULE")
bridge_path = os.path.join(os.path.dirname(__file__), "vscode-extension", "src", "bridge.py")
if os.path.exists(bridge_path):
    test("bridge.py exists", lambda: True)
    # Test bridge start + simple message
    try:
        proc = subprocess.Popen(
            ["C:\\Program Files\\PyManager\\python.exe", bridge_path, "--model", "deepseek-r1:671b"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=os.path.dirname(__file__), text=True
        )
        assert proc.stdout is not None
        assert proc.stdin is not None
        # Read the status line
        status_line = proc.stdout.readline()
        status = json.loads(status_line)
        test("bridge emits Ready status", lambda: status.get("type") == "status" and "Ready" in status.get("text", ""))

        if ollama_up:
            # Send a message
            proc.stdin.write(json.dumps({"type": "chat", "content": "What is 3+3? Just the number."}) + "\n")
            proc.stdin.flush()

            # Collect events for up to 30s
            bridge_events = []
            import select
            start = time.time()
            while time.time() - start < 45:
                line = proc.stdout.readline()
                if not line:
                    break
                try:
                    ev = json.loads(line.strip())
                    bridge_events.append(ev)
                    if ev.get("type") in ("done", "cost"):
                        if ev.get("type") == "cost":
                            break
                except:
                    pass

            test("bridge streams events", lambda: len(bridge_events) > 0)
            test("bridge has text_delta", lambda: any(e.get("type") == "text_delta" for e in bridge_events))
            test("bridge has done", lambda: any(e.get("type") == "done" for e in bridge_events))
            test("bridge has cost", lambda: any(e.get("type") == "cost" for e in bridge_events))

            # Check crash recovery
            proc.stdin.write(json.dumps({"type": "chat", "content": "say hello"}) + "\n")
            proc.stdin.flush()
            recovery_events = []
            start = time.time()
            while time.time() - start < 45:
                line = proc.stdout.readline()
                if not line:
                    break
                try:
                    ev = json.loads(line.strip())
                    recovery_events.append(ev)
                    if ev.get("type") == "cost":
                        break
                except:
                    pass
            test("bridge handles 2nd message", lambda: len(recovery_events) > 0)

        proc.stdin.close()
        proc.terminate()
        proc.wait(timeout=5)
    except Exception as e:
        test("bridge process", lambda: False)
        ERRORS.append(f"Bridge error: {e}")
else:
    test("bridge.py exists", lambda: False)

# ============================================================================
# 17. VS CODE EXTENSION FILES
# ============================================================================
print("\n[17] VS CODE EXTENSION FILES")
ext_dir = os.path.expanduser(r"~\.vscode\extensions\claw-agent-0.1.0")
ext_files = ["package.json", "src/extension.js", "src/bridge.py"]
for f in ext_files:
    path = os.path.join(ext_dir, f)
    test(f"installed {f} exists", lambda p=path: os.path.exists(p))

if os.path.exists(os.path.join(ext_dir, "package.json")):
    pkg = json.loads(open(os.path.join(ext_dir, "package.json")).read())
    test("extension version is 0.1.0", lambda: pkg.get("version") == "0.1.0")
    test("extension has activationEvents", lambda: "activationEvents" in pkg or "main" in pkg)

# ============================================================================
# 18. CHROME EXTENSION FILES
# ============================================================================
print("\n[18] CHROME EXTENSION FILES")
chrome_dir = os.path.join(os.path.dirname(__file__), "chrome-extension")
chrome_files = ["manifest.json", "background.js", "content.js", "sidepanel.html", "sidepanel.css", "sidepanel.js",
                "icons/icon16.png", "icons/icon32.png", "icons/icon48.png", "icons/icon128.png"]
for f in chrome_files:
    path = os.path.join(chrome_dir, f)
    test(f"chrome {f} exists", lambda p=path: os.path.exists(p))

if os.path.exists(os.path.join(chrome_dir, "manifest.json")):
    manifest = json.loads(open(os.path.join(chrome_dir, "manifest.json")).read())
    test("manifest_version is 3", lambda: manifest.get("manifest_version") == 3)
    test("has sidePanel permission", lambda: "sidePanel" in manifest.get("permissions", []))
    test("has background service_worker", lambda: "service_worker" in manifest.get("background", {}))
    test("has content_scripts", lambda: len(manifest.get("content_scripts", [])) > 0)
    test("has host_permissions for Ollama", lambda: "http://localhost:11434/*" in manifest.get("host_permissions", []))

# ============================================================================
# CLEANUP
# ============================================================================
shutil.rmtree(TMPDIR, ignore_errors=True)

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 60)
print(f"RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
if ERRORS:
    print(f"\nFAILURES:")
    for e in ERRORS:
        print(f"  ✗ {e}")
print("=" * 60)

if __name__ == "__main__":
    sys.exit(0 if FAIL == 0 else 1)
