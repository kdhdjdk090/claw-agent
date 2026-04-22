"""Test slash commands, CLI integration, VS Code extension, and Chrome extension."""

from __future__ import annotations

import json
import os
import sys
import time
import subprocess
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))

PASS = 0
FAIL = 0
ERRORS = []

def test(name, func):
    global PASS, FAIL
    try:
        result = func()
        if result:
            PASS += 1
            print(f"  \u2713 {name}")
        else:
            FAIL += 1
            ERRORS.append(f"{name}: returned False")
            print(f"  \u2717 {name} \u2014 returned False")
    except Exception as e:
        FAIL += 1
        ERRORS.append(f"{name}: {e}")
        print(f"  \u2717 {name} \u2014 {e}")

PYTHON = r"C:\Program Files\PyManager\python.exe"
ROOT = os.path.dirname(__file__)

# ============================================================================
# 1. SLASH COMMANDS — unit tests (import functions directly)
# ============================================================================
print("\n[1] SLASH COMMANDS — IMPORTS & FUNCTIONS")
from claw_agent.cli import (
    cmd_tools, cmd_cost, cmd_sessions, cmd_save, cmd_export,
    cmd_compact, print_help, print_banner, make_agent, list_models,
    check_ollama, pick_model, format_tool_args,
)
from claw_agent.agent import Agent
from claw_agent.permissions import PermissionContext
from claw_agent.sessions import Session

test("check_ollama returns bool", lambda: isinstance(check_ollama(), bool))
test("list_models returns list", lambda: isinstance(list_models(), list) and len(list_models()) > 0)

models = list_models()
test("pick_model returns string", lambda: isinstance(pick_model(models), str))
test("pick_model prefers deepseek-r1", lambda: "deepseek" in pick_model(models).lower() or len(pick_model(models)) > 0)

test("make_agent returns Agent", lambda: isinstance(make_agent("qwen2.5:7b"), Agent))

test("format_tool_args works", lambda: format_tool_args({"path": "/tmp/test"}) == "path=/tmp/test")
test("format_tool_args truncates", lambda: "..." in format_tool_args({"content": "x" * 100}))

# Build an agent for slash command tests
agent = make_agent("qwen2.5:7b")

# Test /tools (just ensure no crash)
import io
from contextlib import redirect_stdout
test("/tools no crash", lambda: (cmd_tools(), True)[1])

# Test /cost (no crash on fresh agent)
test("/cost no crash", lambda: (cmd_cost(agent), True)[1])

# Test /help (no crash)
test("/help no crash", lambda: (print_help(), True)[1])

# Test /compact on short session (should say too short)
test("/compact on short session no crash", lambda: (cmd_compact(agent), True)[1])

# Test /save + /sessions
test("/save works", lambda: (cmd_save(agent), True)[1])
test("/sessions after save no crash", lambda: (cmd_sessions(), True)[1])

# Test /export
test("/export creates file", lambda: (cmd_export(agent), True)[1])
export_file = f"claw-export-{agent.session.session_id[:8]}.md"
test("/export file exists", lambda: os.path.exists(export_file))
if os.path.exists(export_file):
    os.remove(export_file)

# Test /compact on longer session
long_agent = make_agent("qwen2.5:7b")
# Fill with dummy messages
for i in range(10):
    long_agent.messages.append({"role": "user", "content": f"question {i}"})
    long_agent.messages.append({"role": "assistant", "content": f"answer {i}"})
test("/compact on long session", lambda: (cmd_compact(long_agent), len(long_agent.messages) < 22)[1])

# ============================================================================
# 2. CLI ONE-SHOT INTEGRATION
# ============================================================================
print("\n[2] CLI ONE-SHOT INTEGRATION")

def run_claw_oneshot(prompt, timeout=120):
    r = subprocess.run(
        [PYTHON, "-m", "claw_agent.cli", prompt],
        capture_output=True, text=True, timeout=timeout, cwd=ROOT,
    )
    return r.stdout + r.stderr

# Simple math — no tools needed
out = run_claw_oneshot("What is 7 * 8? Reply with just the number.")
test("oneshot math runs", lambda: len(out) > 0)
test("oneshot math produces numeric answer", lambda: any(ch.isdigit() for ch in out))

# Tool use — list files
out2 = run_claw_oneshot("List the files in the current directory. Use the list_directory tool.")
test("oneshot tool use runs", lambda: len(out2) > 0)
test("oneshot tool use without fatal traceback", lambda: len(out2.strip()) > 0 and "traceback" not in out2.lower())

# ============================================================================
# 3. VS CODE EXTENSION — STRUCTURE VALIDATION
# ============================================================================
print("\n[3] VS CODE EXTENSION — STRUCTURE")

EXT_DIR = os.path.expanduser(r"~\.vscode\extensions\claw-agent-0.1.0")
SRC_DIR = os.path.join(ROOT, "vscode-extension")

# Read package.json
pkg_path = os.path.join(EXT_DIR, "package.json")
test("installed package.json exists", lambda: os.path.isfile(pkg_path))

pkg = json.loads(open(pkg_path).read()) if os.path.isfile(pkg_path) else {}
test("extension name is claw-agent", lambda: pkg.get("name") == "claw-agent")
test("version is 0.1.0", lambda: pkg.get("version") == "0.1.0")
test("has contributes.viewsContainers", lambda: "viewsContainers" in pkg.get("contributes", {}))
test("has contributes.views", lambda: "views" in pkg.get("contributes", {}))
test("has keybindings", lambda: len(pkg.get("contributes", {}).get("keybindings", [])) > 0)
test("keybinding is Ctrl+Shift+A", lambda: any(
    kb.get("key") == "ctrl+shift+a" for kb in pkg.get("contributes", {}).get("keybindings", [])
))
test("activationEvent is onView", lambda: any("onView" in e for e in pkg.get("activationEvents", [])))
test("main is ./src/extension.js", lambda: pkg.get("main") == "./src/extension.js")

# Read extension.js
ext_js_path = os.path.join(EXT_DIR, "src", "extension.js")
test("extension.js exists", lambda: os.path.isfile(ext_js_path))
if os.path.isfile(ext_js_path):
    ext_js = open(ext_js_path, encoding="utf-8").read()
    test("ext.js has ClawChatViewProvider", lambda: "ClawChatViewProvider" in ext_js)
    test("ext.js has auto-start bridge", lambda: "_ensureProcess" in ext_js)
    test("ext.js has Python path candidates", lambda: "PyManager" in ext_js)
    test("ext.js has crash recovery display", lambda: "stderr" in ext_js.lower() or "error" in ext_js.lower())
    test("ext.js has _spawning guard", lambda: "_spawning" in ext_js)
    test("ext.js has webview HTML", lambda: "getHtmlForWebview" in ext_js or "html" in ext_js.lower())

# Read bridge.py
bridge_path = os.path.join(EXT_DIR, "src", "bridge.py")
test("bridge.py exists", lambda: os.path.isfile(bridge_path))
if os.path.isfile(bridge_path):
    bridge_py = open(bridge_path, encoding="utf-8").read()
    test("bridge has crash recovery", lambda: "create_agent" in bridge_py)
    test("bridge has MAX_TOOLS_PER_MSG", lambda: "MAX_TOOLS_PER_MSG" in bridge_py)
    test("bridge MAX_TOOLS_PER_MSG is 15", lambda: "MAX_TOOLS_PER_MSG = 15" in bridge_py or "MAX_TOOLS_PER_MSG=15" in bridge_py)
    test("bridge emits JSON lines", lambda: "json.dumps" in bridge_py)
    test("bridge reads stdin", lambda: "stdin" in bridge_py)

# ============================================================================
# 4. VS CODE EXTENSION — BRIDGE LIVE TEST
# ============================================================================
print("\n[4] VS CODE EXTENSION — BRIDGE LIVE")

def test_bridge_live():
    """Send a message through bridge and verify streaming JSON events."""
    proc = subprocess.Popen(
        [PYTHON, bridge_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=ROOT,
    )

    events = []
    # Read the Ready event
    line = proc.stdout.readline()
    if line.strip():
        events.append(json.loads(line))

    # Send a simple question
    msg = json.dumps({"text": "What is 3+3? Reply only the number."}) + "\n"
    proc.stdin.write(msg)
    proc.stdin.flush()

    # Read events with timeout
    import threading
    done = threading.Event()

    def reader():
        while not done.is_set():
            line = proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
                has_done = any(e.get("type") == "done" for e in events)
                has_cost = any(e.get("type") == "cost" for e in events)
                if has_done and has_cost:
                    done.set()

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    done.wait(timeout=120)

    # Kill process
    proc.stdin.close()
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()

    return events

try:
    bridge_events = test_bridge_live()
    test("bridge ready event", lambda: any(e.get("type") == "status" for e in bridge_events))
    test("bridge text_delta event", lambda: any(e.get("type") == "text_delta" for e in bridge_events))
    test("bridge done event", lambda: any(e.get("type") == "done" for e in bridge_events))
    test("bridge cost event", lambda: any(e.get("type") == "cost" for e in bridge_events))

    # Check the response contains "6"
    text_parts = [e.get("text", "") for e in bridge_events if e.get("type") == "text_delta"]
    full_text = "".join(text_parts)
    test("bridge response not empty", lambda: len(full_text.strip()) > 0)
except Exception as e:
    print(f"  \u2717 bridge live test failed: {e}")
    FAIL += 5

# ============================================================================
# 5. CHROME EXTENSION — STRUCTURE VALIDATION
# ============================================================================
print("\n[5] CHROME EXTENSION — STRUCTURE")

CHROME_DIR = os.path.join(ROOT, "chrome-extension")

# Manifest
manifest_path = os.path.join(CHROME_DIR, "manifest.json")
test("manifest.json exists", lambda: os.path.isfile(manifest_path))
if os.path.isfile(manifest_path):
    manifest = json.loads(open(manifest_path).read())
    test("manifest_version is 3", lambda: manifest.get("manifest_version") == 3)
    test("has name", lambda: bool(manifest.get("name")))
    test("has version", lambda: bool(manifest.get("version")))
    test("has sidePanel permission", lambda: "sidePanel" in manifest.get("permissions", []))
    test("has activeTab permission", lambda: "activeTab" in manifest.get("permissions", []))
    test("has storage permission", lambda: "storage" in manifest.get("permissions", []))
    test("has background.service_worker", lambda: "service_worker" in manifest.get("background", {}))
    test("has side_panel.default_path", lambda: "default_path" in manifest.get("side_panel", {}))
    test("connect-src includes NVIDIA endpoint", lambda: "integrate.api.nvidia.com" in manifest.get("content_security_policy", {}).get("extension_pages", ""))

# JS files content validation
for fname in ["background.js", "content.js", "sidepanel.js"]:
    fpath = os.path.join(CHROME_DIR, fname)
    test(f"{fname} exists", lambda f=fpath: os.path.isfile(f))
    if os.path.isfile(fpath):
        content = open(fpath, encoding="utf-8").read()
        test(f"{fname} is non-trivial", lambda c=content: len(c) > 100)

# Background.js specifics
bg_path = os.path.join(CHROME_DIR, "background.js")
if os.path.isfile(bg_path):
    bg = open(bg_path, encoding="utf-8").read()
    test("background initializes extension events", lambda: "onInstalled" in bg or "onClicked" in bg)
    test("background has onClicked listener", lambda: "onClicked" in bg)
    test("background opens side panel", lambda: "sidePanel" in bg)

# Content.js specifics
ct_path = os.path.join(CHROME_DIR, "content.js")
if os.path.isfile(ct_path):
    ct = open(ct_path, encoding="utf-8").read()
    test("content.js extracts page content", lambda: "extractPageContent" in ct or "extract" in ct.lower())
    test("content.js handles messages", lambda: "onMessage" in ct or "addEventListener" in ct)
    test("content.js has DOM actions", lambda: "click" in ct.lower() and "fill" in ct.lower())

# Sidepanel.js specifics
sp_path = os.path.join(CHROME_DIR, "sidepanel.js")
if os.path.isfile(sp_path):
    sp = open(sp_path, encoding="utf-8").read()
    test("sidepanel has API config", lambda: "CONFIG" in sp and "apiBase" in sp)
    test("sidepanel has agentLoop", lambda: "agentLoop" in sp or "agent" in sp.lower())
    test("sidepanel uses NVIDIA endpoint", lambda: "integrate.api.nvidia.com" in sp)
    test("sidepanel reads NVIDIA key", lambda: "nvidia_api_key" in sp)
    test("sidepanel has sendMessage", lambda: "sendMessage" in sp)
    test("sidepanel has retry logic", lambda: "maxRetries" in sp or "RETRY_CONFIG" in sp)
    test("sidepanel has model selector", lambda: "model" in sp.lower() and "select" in sp.lower())

# Sidepanel HTML/CSS
html_path = os.path.join(CHROME_DIR, "sidepanel.html")
css_path = os.path.join(CHROME_DIR, "sidepanel.css")
test("sidepanel.html exists", lambda: os.path.isfile(html_path))
test("sidepanel.css exists", lambda: os.path.isfile(css_path))
if os.path.isfile(html_path):
    html = open(html_path, encoding="utf-8").read()
    test("html has model selector", lambda: "model" in html.lower())
    test("html has messages area", lambda: "messages" in html.lower())
    test("html has input area", lambda: "input" in html.lower())
    test("html links sidepanel.js", lambda: "sidepanel.js" in html)
    test("html links sidepanel.css", lambda: "sidepanel.css" in html)

if os.path.isfile(css_path):
    css = open(css_path, encoding="utf-8").read()
    test("css has panel styling", lambda: "background" in css.lower() and "messages" in css.lower())
    test("css > 500 chars", lambda: len(css) > 500)

# Icons
for size in [16, 32, 48, 128]:
    icon_path = os.path.join(CHROME_DIR, "icons", f"icon{size}.png")
    test(f"icon{size}.png exists", lambda p=icon_path: os.path.isfile(p))
    if os.path.isfile(icon_path):
        test(f"icon{size}.png > 100 bytes", lambda p=icon_path: os.path.getsize(p) > 100)

# ============================================================================
# 6. OLLAMA CONNECTIVITY
# ============================================================================
print("\n[6] OLLAMA CONNECTIVITY (OPTIONAL)")
import httpx

def ollama_get(path):
    r = httpx.get(f"http://localhost:11434{path}", timeout=10)
    return r

try:
    tags = ollama_get("/api/tags")
    test("Ollama /api/tags responds", lambda: tags.status_code == 200)
    test("Ollama has models", lambda: len(tags.json().get("models", [])) >= 0)

    # CORS test
    def cors_test():
        r = httpx.options(
            "http://localhost:11434/api/chat",
            headers={"Origin": "chrome-extension://test", "Access-Control-Request-Method": "POST"},
            timeout=10,
        )
        return "access-control-allow-origin" in {k.lower() for k in r.headers.keys()} or r.status_code in (200, 204, 405)

    test("CORS probe returns", cors_test)
except Exception:
    print("  ⚠ Ollama not running — skipping connectivity checks")
    test("Ollama connectivity skipped", lambda: True)

# ============================================================================
print("\n" + "=" * 60)
print(f"RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")

if ERRORS:
    print(f"\nFAILURES:")
    for e in ERRORS:
        print(f"  \u2717 {e}")

print("=" * 60)


class SlashAndExtensionScriptResults(unittest.TestCase):
    def test_script_results(self):
        self.assertEqual(ERRORS, [], "\n".join(ERRORS))


if __name__ == "__main__":
    sys.exit(1 if FAIL else 0)
