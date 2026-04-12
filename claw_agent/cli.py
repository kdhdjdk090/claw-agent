"""Claude Code-style interactive CLI for Claw Agent.

Features: streaming responses, inline tool call display, status bar,
one-shot prompt mode, session management.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from .agent import (
    Agent, StreamEvent, TextDelta, ToolCallStart, ToolCallEnd,
    TurnComplete, AgentDone, MAX_ITERATIONS, MAX_CONTEXT_TOKENS,
    COMPACT_KEEP_RECENT, BLOCKED_COMMANDS,
)
from .permissions import PermissionContext
from .sessions import Session, save_session, load_session, list_sessions, delete_session
from .cost_tracker import CostTracker
from .tools import TOOL_REGISTRY

# --- Theme (Claude Code-inspired) ---
THEME = Theme({
    "claw.prompt": "bold bright_white",
    "claw.model": "dim magenta",
    "claw.tool": "bold bright_magenta",
    "claw.tool_result": "dim white",
    "claw.error": "bold red",
    "claw.dim": "dim",
    "claw.success": "bold green",
    "claw.info": "bright_blue",
    "claw.accent": "bold bright_magenta",
    "claw.muted": "dim white",
})

console = Console(theme=THEME)

HISTORY_PATH = os.path.expanduser("~/.claw-agent/history.txt")
os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)

# --- Helpers ---

def check_ollama() -> bool:
    import httpx
    try:
        r = httpx.get("http://localhost:11434/api/tags", timeout=5)
        r.raise_for_status()
        return True
    except Exception:
        return False


def list_models() -> list[str]:
    import httpx
    try:
        r = httpx.get("http://localhost:11434/api/tags", timeout=5)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


def pick_model(models: list[str]) -> str:
    preferred = [
        "deepseek-v3.1:671b-cloud", "deepseek-v3.1",
        "deepseek-r1:671b", "deepseek-r1:32b", "deepseek-r1:14b", "deepseek-r1:8b",
        "deepseek-v3:671b", "deepseek-v3",
        "deepseek-coder:6.7b", "deepseek-coder",
        "gemma4:latest", "gemma4",
        "qwen2.5:14b", "qwen2.5:7b",
        "mistral:latest", "mistral",
        "llama3:latest", "llama3.1:8b", "llama3",
    ]
    for p in preferred:
        if any(p in m for m in models):
            return next(m for m in models if p in m)
    return models[0] if models else "deepseek-v3.1:671b-cloud"


def _cli_confirm() -> bool:
    """Ask user for Y/N confirmation for gated/dangerous tool calls."""
    try:
        answer = console.input("[bold bright_magenta]\u276f Allow?[/bold bright_magenta] [dim](y/n)[/dim] ").strip().lower()
        return answer in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        return False


def make_agent(model: str, session: Session | None = None, permissions: PermissionContext | None = None) -> Agent:
    return Agent(
        model=model,
        permissions=permissions or PermissionContext.default(),
        session=session or Session(model=model),
        confirm_fn=_cli_confirm,
    )


def format_tool_args(args: dict) -> str:
    """Compact arg display like Claude Code."""
    parts = []
    for k, v in args.items():
        sv = str(v)
        if len(sv) > 80:
            sv = sv[:77] + "..."
        parts.append(f"{k}={sv}")
    return ", ".join(parts)


def _tool_display_name(name: str, args: dict) -> str:
    """Map tool names to Claude Code-style display: Read(file), Write(file), Bash(cmd)."""
    if name == "read_file":
        return f"Read({args.get('path', args.get('file', ''))})"  
    if name == "write_file":
        return f"Write({args.get('path', args.get('file', ''))})"
    if name in ("replace_in_file", "multi_edit_file", "insert_at_line"):
        return f"Edit({args.get('path', args.get('file', ''))})"
    if name == "run_command":
        cmd = str(args.get('command', ''))
        if len(cmd) > 60:
            cmd = cmd[:57] + "..."
        return f"Bash({cmd})"
    if name == "list_directory":
        return f"LS({args.get('path', '.')})"
    if name == "grep_search":
        return f"Grep({args.get('pattern', '')})"
    if name == "find_files":
        return f"Find({args.get('pattern', args.get('glob', ''))})"
    if name == "web_fetch":
        return f"Fetch({args.get('url', '')})"
    if name == "web_search":
        return f"Search({args.get('query', '')})"
    # Fallback
    return f"{name}({format_tool_args(args)})" if args else name


def print_banner(model: str, models: list[str]):
    cwd = os.getcwd()
    width = 60
    console.print()
    console.print(f"[bold bright_magenta]╭{'─' * width}╮[/bold bright_magenta]")
    console.print(f"[bold bright_magenta]│[/bold bright_magenta] [bold bright_white]\u2728 Claw Agent[/bold bright_white] [dim]v0.1.0[/dim]{' ' * (width - 22)}[bold bright_magenta]│[/bold bright_magenta]")
    console.print(f"[bold bright_magenta]│[/bold bright_magenta]{' ' * width}[bold bright_magenta]│[/bold bright_magenta]")
    # Working directory
    cwd_display = cwd if len(cwd) <= width - 4 else "\u2026" + cwd[-(width - 5):]
    cwd_pad = width - len(cwd_display) - 2
    console.print(f"[bold bright_magenta]│[/bold bright_magenta] [dim]{cwd_display}[/dim]{' ' * cwd_pad}[bold bright_magenta]│[/bold bright_magenta]")
    # Model
    model_str = f"Model: {model}"
    model_pad = width - len(model_str) - 2
    console.print(f"[bold bright_magenta]│[/bold bright_magenta] [dim magenta]{model_str}[/dim magenta]{' ' * model_pad}[bold bright_magenta]│[/bold bright_magenta]")
    # Tools
    tools_str = f"{len(TOOL_REGISTRY)} tools available"
    tools_pad = width - len(tools_str) - 2
    console.print(f"[bold bright_magenta]│[/bold bright_magenta] [dim]{tools_str}[/dim]{' ' * tools_pad}[bold bright_magenta]│[/bold bright_magenta]")
    console.print(f"[bold bright_magenta]│[/bold bright_magenta]{' ' * width}[bold bright_magenta]│[/bold bright_magenta]")
    tip_str = "Type /help for commands"
    tip_pad = width - len(tip_str) - 2
    console.print(f"[bold bright_magenta]│[/bold bright_magenta] [dim]{tip_str}[/dim]{' ' * tip_pad}[bold bright_magenta]│[/bold bright_magenta]")
    console.print(f"[bold bright_magenta]╰{'─' * width}╯[/bold bright_magenta]")
    console.print()


def print_help():
    console.print()
    console.print("[bold bright_white]  Slash Commands[/bold bright_white]")
    console.print()

    def _section(title: str, items: list[tuple[str, str]]):
        console.print(f"  [bold bright_magenta]{title}[/bold bright_magenta]")
        for cmd, desc in items:
            console.print(f"    [bold white]{cmd:<24}[/bold white] [dim]{desc}[/dim]")
        console.print()

    _section("Core", [
        ("/help", "Show this help"),
        ("/model <name>", "Switch model"),
        ("/models", "List available models"),
        ("/tools", f"List all {len(TOOL_REGISTRY)} tools"),
        ("/cost", "Token usage & timing stats"),
        ("/compact", "Compress conversation history"),
    ])
    _section("Sessions", [
        ("/save", "Save current session"),
        ("/sessions", "List saved sessions"),
        ("/resume <id>", "Resume a saved session"),
        ("/continue", "Quick-resume most recent session"),
        ("/delete <id>", "Delete a saved session"),
        ("/export", "Export conversation to markdown"),
    ])
    _section("Workspace", [
        ("/diff", "Show what the agent changed (git diff)"),
        ("/status", "Workspace status, git, project info"),
        ("/config", "Show current agent configuration"),
        ("/permissions [mode]", "Show/switch permissions"),
        ("/memory", "Context window usage"),
        ("/undo", "Undo last file write (git checkout)"),
        ("/init", "Generate .claw config for this project"),
    ])
    _section("Debug", [
        ("/version", "Show Claw Agent version"),
        ("/doctor", "Diagnose Ollama, tools, connectivity"),
        ("/bug", "Report a bug / show debug info"),
    ])
    _section("Control", [
        ("/clear", "Clear conversation"),
        ("/quit", "Exit (or /exit, /q)"),
    ])


# --- Streaming display ---





def stream_response_enhanced(agent: Agent, user_input: str):
    """Claude Code-style streaming with tool call display."""
    streamed_any_text = False
    active_tool = False

    console.print()

    for event in agent.stream_chat(user_input):
        if isinstance(event, TextDelta):
            if not active_tool:
                sys.stdout.write(event.text)
                sys.stdout.flush()
                streamed_any_text = True

        elif isinstance(event, ToolCallStart):
            if streamed_any_text:
                sys.stdout.write("\n\n")
                streamed_any_text = False

            active_tool = True
            display = _tool_display_name(event.name, event.arguments)
            console.print(
                f"  [bold bright_magenta]\u25cf {display}[/bold bright_magenta]"
            )

        elif isinstance(event, ToolCallEnd):
            active_tool = False
            result_lines = event.result.strip().split("\n")
            preview = result_lines[0] if result_lines else ""
            if len(preview) > 120:
                preview = preview[:117] + "\u2026"
            extra = f" (+{len(result_lines)-1} lines)" if len(result_lines) > 1 else ""

            console.print(
                f"  [green]\u2713[/green] [dim]{event.name}[/dim]"
                f" [dim]{event.duration_ms:.0f}ms[/dim]"
                f" [dim]{preview}{extra}[/dim]"
            )

        elif isinstance(event, AgentDone):
            if streamed_any_text:
                sys.stdout.write("\n")
            # Show system messages (iteration limit, circuit breakers)
            if event.final_text and event.final_text.startswith("["):
                console.print(f"  [dim]{event.final_text}[/dim]")
            break

    console.print()


# --- Slash commands ---

def cmd_tools():
    cats = {
        "read_file": "File", "write_file": "File", "list_directory": "File",
        "find_files": "File", "run_command": "Shell", "grep_search": "Search",
        "replace_in_file": "Edit", "multi_edit_file": "Edit",
        "insert_at_line": "Edit", "diff_files": "Edit",
        "web_fetch": "Web", "web_search": "Web",
        "run_subagent": "Agent", "plan_and_execute": "Agent",
        "task_create": "Task", "task_update": "Task",
        "task_list": "Task", "task_get": "Task",
        "notebook_run": "Code",
        "get_workspace_context": "Context", "git_diff": "Context",
        "git_log": "Context",
    }
    from .permissions import ALWAYS_ALLOWED, GATED_TOOLS
    console.print()
    console.print(f"  [bold bright_white]Tools ({len(TOOL_REGISTRY)})[/bold bright_white]")
    console.print()
    # Group by category
    by_cat: dict[str, list[str]] = {}
    for name in sorted(TOOL_REGISTRY.keys()):
        cat = cats.get(name, "Other")
        by_cat.setdefault(cat, []).append(name)
    for cat in ["File", "Shell", "Search", "Edit", "Web", "Agent", "Task", "Code", "Context", "Other"]:
        tools = by_cat.get(cat)
        if not tools:
            continue
        console.print(f"  [bold bright_magenta]{cat}[/bold bright_magenta]")
        for t in tools:
            perm = "✓" if t in ALWAYS_ALLOWED else "⚡" if t in GATED_TOOLS else " "
            perm_style = "green" if t in ALWAYS_ALLOWED else "yellow" if t in GATED_TOOLS else "dim"
            console.print(f"    [{perm_style}]{perm}[/{perm_style}] [white]{t}[/white]")
    console.print()
    console.print("  [dim]✓ = always allowed  ⚡ = needs permission[/dim]")


def cmd_cost(agent: Agent):
    if agent.cost.total_turns == 0:
        console.print("[dim]No stats yet.[/dim]")
        return
    console.print(f"\n{agent.cost.summary()}\n")


def cmd_sessions():
    sessions = list_sessions()
    if not sessions:
        console.print("[dim]No saved sessions.[/dim]")
        return
    import datetime
    for s in sessions:
        # created_at can be float (epoch) or string
        if isinstance(s.created_at, (int, float)):
            ts = datetime.datetime.fromtimestamp(s.created_at).strftime("%Y-%m-%d %H:%M:%S")
        else:
            ts = str(s.created_at)[:19]
        title = s.title or s.auto_title()
        console.print(
            f"  [cyan]{s.session_id[:12]}[/cyan]  "
            f"{s.model}  {s.total_turns} turns  "
            f"[dim]{ts}[/dim]  {title[:40]}"
        )


def cmd_save(agent: Agent):
    save_session(agent.session)
    console.print(f"  [claw.success]Saved:[/claw.success] {agent.session.session_id[:12]}")


def cmd_resume(args: str, model: str) -> Agent | None:
    prefix = args.strip()
    sessions = list_sessions()
    if not prefix:
        # Filter out empty/untitled sessions with 0 turns
        meaningful = [s for s in sessions if s.total_turns > 0]
        if not meaningful:
            meaningful = sessions  # fallback to all if no meaningful ones
        if not meaningful:
            console.print("[dim]No saved sessions.[/dim]")
            return None
        import datetime
        # Show at most 20 recent meaningful sessions
        display = meaningful[:20]
        console.print("[bold]Available sessions:[/bold]")
        for i, s in enumerate(display, 1):
            if isinstance(s.created_at, (int, float)):
                ts = datetime.datetime.fromtimestamp(s.created_at).strftime("%Y-%m-%d %H:%M:%S")
            else:
                ts = str(s.created_at)[:19]
            title = s.title or s.auto_title()
            console.print(
                f"  [cyan]{i}.[/cyan] [cyan]{s.session_id[:12]}[/cyan]  "
                f"{s.model}  {s.total_turns} turns  "
                f"[dim]{ts}[/dim]  {title[:40]}"
            )
        if len(meaningful) > 20:
            console.print(f"  [dim]... and {len(meaningful) - 20} more (use /sessions to see all)[/dim]")
        try:
            choice = console.input("\n[bold]Enter number or session-id prefix:[/bold] ").strip()
        except (KeyboardInterrupt, EOFError):
            return None
        if not choice:
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(display):
            match = [display[int(choice) - 1]]
        else:
            match = [s for s in sessions if s.session_id.startswith(choice)]
    else:
        match = [s for s in sessions if s.session_id.startswith(prefix)]
    if not match:
        console.print(f"[claw.error]No session matching '{prefix or choice}'[/claw.error]")
        return None
    sess = match[0]
    agent = make_agent(sess.model, session=sess)
    agent.messages = [agent.messages[0]] + sess.messages
    console.print(f"  [claw.success]Resumed {sess.session_id[:12]} ({sess.total_turns} turns, model: {sess.model})[/claw.success]")
    # Show conversation context so the user knows what they're continuing
    if sess.messages:
        console.print()
        console.print("[bold]Session context:[/bold]")
        # Show last few messages (skip tool results, keep user/assistant)
        context_msgs = [m for m in sess.messages if m.get("role") in ("user", "assistant")]
        for msg in context_msgs[-4:]:
            role = msg.get("role", "?")
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                preview = content.strip()[:120]
                if len(content.strip()) > 120:
                    preview += "..."
                color = "green" if role == "user" else "blue"
                label = "You" if role == "user" else "Claw"
                console.print(f"  [{color}]{label}:[/{color}] {preview}")
        console.print()
    return agent


def cmd_export(agent: Agent):
    lines = [f"# Claw Agent Session\n\nModel: {agent.model}\n"]
    for msg in agent.session.messages:
        role = msg.get("role", "?").upper()
        content = msg.get("content", "")
        lines.append(f"## {role}\n\n{content}\n")
    filename = f"claw-export-{agent.session.session_id[:8]}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    console.print(f"  [claw.success]Exported → {filename}[/claw.success]")


def cmd_compact(agent: Agent):
    if len(agent.messages) <= COMPACT_KEEP_RECENT + 1:
        console.print("[dim]Too short to compact.[/dim]")
        return
    system = agent.messages[0]
    old = agent.messages[1:-COMPACT_KEEP_RECENT]
    recent = agent.messages[-COMPACT_KEEP_RECENT:]
    snippets = []
    for m in old:
        if m.get("content") and m.get("role") in ("user", "assistant"):
            snippets.append(f"{m['role']}: {m['content'][:200]}")
    compact = {"role": "system", "content": f"[Summary]\n" + "\n".join(snippets[-20:]) + "\n[/Summary]"}
    agent.messages = [system, compact] + recent
    console.print(f"  [claw.success]Compacted {len(old)} messages → summary[/claw.success]")


def cmd_continue(model: str) -> Agent | None:
    """Quick-resume the most recent session with >0 turns."""
    sessions = list_sessions()
    meaningful = [s for s in sessions if s.total_turns > 0]
    if not meaningful:
        console.print("[dim]No sessions to continue.[/dim]")
        return None
    sess = meaningful[0]  # most recent by mtime
    agent = make_agent(sess.model, session=sess)
    agent.messages = [agent.messages[0]] + sess.messages
    console.print(f"  [claw.success]Continued {sess.session_id[:12]} ({sess.total_turns} turns)[/claw.success]")
    title = sess.title or sess.auto_title()
    if title:
        console.print(f"  [dim]{title}[/dim]")
    return agent


def cmd_diff():
    """Show git diff of recent changes."""
    from .tools.context_tools import git_diff
    result = git_diff()
    if not result.strip() or "Error" in result or "not a git" in result.lower():
        console.print("[dim]No changes detected (or not a git repo).[/dim]")
    else:
        console.print(Panel(result[:3000], title="Git Diff", border_style="yellow"))


def cmd_status():
    """Show workspace status."""
    from .tools.context_tools import get_workspace_context
    ctx = get_workspace_context()
    console.print(Panel(ctx[:2000], title="Workspace Status", border_style="cyan"))


def cmd_config(agent: Agent):
    """Show current agent configuration."""
    console.print()
    table = Table(title="Configuration", border_style="dim")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Model", agent.model)
    table.add_row("Base URL", agent.base_url)
    table.add_row("Max Iterations", str(MAX_ITERATIONS))
    table.add_row("Max Context Tokens", f"{MAX_CONTEXT_TOKENS:,}")
    table.add_row("Compact Keep Recent", str(COMPACT_KEEP_RECENT))
    table.add_row("Tools Available", str(len(TOOL_REGISTRY)))
    table.add_row("Working Directory", os.getcwd())
    table.add_row("Session ID", agent.session.session_id[:12])
    table.add_row("Messages in Context", str(len(agent.messages)))
    table.add_row("Auto Approve", str(agent.permissions.auto_approve))
    console.print(table)
    console.print()


def cmd_version():
    """Show version info."""
    console.print()
    console.print("[bold bright_magenta]\u2728 Claw Agent[/bold bright_magenta] [dim]v0.1.0[/dim]")
    console.print(f"  Python: {sys.version.split()[0]}")
    console.print(f"  Platform: {sys.platform}")
    import httpx
    try:
        r = httpx.get("http://localhost:11434/api/version", timeout=5)
        ver = r.json().get("version", "unknown")
        console.print(f"  Ollama: {ver}")
    except Exception:
        console.print("  Ollama: [red]not reachable[/red]")
    console.print()


def cmd_doctor():
    """Diagnose connectivity, tools, and model availability."""
    console.print()
    console.print("[bold]Running diagnostics...[/bold]\n")
    checks = []

    # 1. Python
    checks.append(("Python", True, sys.version.split()[0]))

    # 2. Ollama connectivity
    import httpx
    try:
        r = httpx.get("http://localhost:11434/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        checks.append(("Ollama Connection", True, f"{len(models)} models available"))
    except Exception as e:
        checks.append(("Ollama Connection", False, str(e)))
        models = []

    # 3. Default model
    if models:
        preferred = "deepseek-v3.1:671b-cloud"
        has_preferred = any(preferred in m for m in models)
        checks.append(("Default Model", has_preferred, preferred if has_preferred else f"Not found — using {models[0]}"))
    else:
        checks.append(("Default Model", False, "No models available"))

    # 4. Tools
    checks.append(("Tool Registry", len(TOOL_REGISTRY) >= 22, f"{len(TOOL_REGISTRY)} tools loaded"))

    # 5. Session directory
    from .sessions import DEFAULT_SESSION_DIR
    checks.append(("Sessions Dir", DEFAULT_SESSION_DIR.exists(), str(DEFAULT_SESSION_DIR)))

    # 6. httpx
    try:
        import httpx as _h
        checks.append(("httpx", True, _h.__version__))
    except ImportError:
        checks.append(("httpx", False, "not installed"))

    # 7. rich
    try:
        from importlib.metadata import version as _pkg_version
        _rich_ver = _pkg_version("rich")
        checks.append(("rich", True, _rich_ver))
    except Exception:
        checks.append(("rich", False, "not installed"))

    # 8. Git
    import subprocess
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
        checks.append(("Git", result.returncode == 0, result.stdout.strip()))
    except Exception:
        checks.append(("Git", False, "not found"))

    for name, ok, detail in checks:
        icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
        console.print(f"  {icon} {name}: {detail}")
    console.print()


def cmd_permissions(agent: Agent, sub_arg: str = ""):
    """Show or switch permission mode.

    /permissions              — show current status
    /permissions allow-all    — enable yolo mode (auto-approve everything)
    /permissions default      — restore default gated permissions
    /permissions deny <tool>  — block a specific tool
    /permissions undeny <tool>— unblock a previously denied tool
    """
    from .permissions import GATED_TOOLS, ALWAYS_ALLOWED, DANGEROUS_PATTERNS

    sub = sub_arg.strip().lower()

    if sub in ("allow-all", "yolo"):
        agent.permissions.auto_approve = True
        console.print("  [bold yellow]⚠ Yolo mode ON — all tool calls auto-approved[/bold yellow]")
        return

    if sub in ("default", "reset"):
        agent.permissions.auto_approve = False
        agent.permissions = PermissionContext.default()
        console.print("  [claw.success]Permissions reset to default (gated)[/claw.success]")
        return

    if sub.startswith("deny "):
        tool = sub[5:].strip()
        if tool:
            agent.permissions.deny_names = agent.permissions.deny_names | frozenset({tool})
            console.print(f"  [claw.success]Blocked tool: {tool}[/claw.success]")
        return

    if sub.startswith("undeny ") or sub.startswith("unblock "):
        tool = sub.split(" ", 1)[1].strip()
        if tool:
            agent.permissions.deny_names = agent.permissions.deny_names - frozenset({tool})
            console.print(f"  [claw.success]Unblocked tool: {tool}[/claw.success]")
        return

    # Default: show summary
    console.print(agent.permissions.summary())
    mode_label = "[bold yellow]allow-all (yolo)[/bold yellow]" if agent.permissions.auto_approve else "default (gated)"
    console.print(f"\n  Mode: {mode_label}")
    console.print(f"  Auto-approve: {agent.permissions.auto_approve}")
    console.print(f"  Blocked tools: {agent.permissions.deny_names or 'none'}")
    console.print(f"  Gated tools: {', '.join(sorted(GATED_TOOLS))}")
    console.print(f"  Always allowed: {', '.join(sorted(ALWAYS_ALLOWED))}")
    console.print(f"  Dangerous patterns: {len(DANGEROUS_PATTERNS)} patterns")
    console.print()
    console.print("  [dim]Usage: /permissions allow-all | default | deny <tool> | undeny <tool>[/dim]")


def cmd_memory(agent: Agent):
    """Show context window usage."""
    console.print()
    total_chars = sum(len(str(m.get("content", ""))) for m in agent.messages)
    est_tokens = total_chars // 4  # rough estimate
    msg_count = len(agent.messages)
    console.print(f"  Messages: {msg_count}")
    console.print(f"  Estimated context: ~{est_tokens:,} tokens")
    console.print(f"  Tracked tokens: {agent.cost.total_tokens:,}")
    console.print(f"  Max context: {MAX_CONTEXT_TOKENS:,}")
    pct = (agent.cost.total_tokens / MAX_CONTEXT_TOKENS * 100) if MAX_CONTEXT_TOKENS else 0
    bar_filled = int(pct / 5)
    bar = "█" * bar_filled + "░" * (20 - bar_filled)
    console.print(f"  Usage: [{bar}] {pct:.1f}%")
    console.print()


def cmd_undo():
    """Undo file changes using git checkout. Reverts ALL changed files."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"], capture_output=True, text=True, timeout=10
        )
        changed = result.stdout.strip().split("\n")
        changed = [f for f in changed if f.strip()]
        if not changed:
            console.print("[dim]No changed files to undo.[/dim]")
            return
        console.print(f"  Changed files: {', '.join(changed[:10])}")
        if len(changed) > 10:
            console.print(f"  ... and {len(changed) - 10} more")
        try:
            confirm = console.input(f"[bold]Revert all {len(changed)} file(s)? (y/n):[/bold] ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            return
        if confirm not in ("y", "yes"):
            console.print("  [dim]Cancelled.[/dim]")
            return
        subprocess.run(["git", "checkout", "--"] + changed, capture_output=True, timeout=10)
        console.print(f"  [claw.success]Reverted {len(changed)} file(s)[/claw.success]")
    except Exception as e:
        console.print(f"  [claw.error]Undo failed: {e}[/claw.error]")


def cmd_init():
    """Create a .claw config file for the project."""
    config_path = os.path.join(os.getcwd(), ".claw")
    if os.path.exists(config_path):
        console.print(f"  [dim].claw already exists[/dim]")
        content = open(config_path).read()
        console.print(Panel(content, title=".claw", border_style="cyan"))
        return
    # Auto-detect project
    config = {
        "model": "deepseek-v3.1:671b-cloud",
        "auto_approve": False,
        "max_iterations": 200,
        "blocked_commands": list(BLOCKED_COMMANDS),
        "notes": "Auto-generated by /init",
    }
    import json
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    console.print(f"  [claw.success]Created .claw config in {os.getcwd()}[/claw.success]")


def cmd_bug(agent: Agent):
    """Show debug info for bug reports."""
    console.print()
    console.print("[bold]Debug Info[/bold]\n")
    console.print(f"  Version: 0.1.0")
    console.print(f"  Python: {sys.version}")
    console.print(f"  Platform: {sys.platform}")
    console.print(f"  CWD: {os.getcwd()}")
    console.print(f"  Model: {agent.model}")
    console.print(f"  Messages: {len(agent.messages)}")
    console.print(f"  Total tokens: {agent.cost.total_tokens:,}")
    console.print(f"  Tool calls: {agent.cost.total_tool_calls}")
    console.print(f"  Turns: {agent.cost.total_turns}")
    console.print(f"  Session ID: {agent.session.session_id}")
    console.print()


def cmd_delete(args: str):
    """Delete a saved session. Use 'purge' to delete all 0-turn sessions."""
    prefix = args.strip()
    sessions = list_sessions()

    # Special: /delete purge — remove all 0-turn empty sessions
    if prefix == "purge":
        empty = [s for s in sessions if s.total_turns == 0]
        if not empty:
            console.print("[dim]No empty sessions to purge.[/dim]")
            return
        try:
            confirm = console.input(f"[bold]Delete {len(empty)} empty (0-turn) sessions? (y/n):[/bold] ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            return
        if confirm in ("y", "yes"):
            for s in empty:
                delete_session(s.session_id)
            console.print(f"  [claw.success]Purged {len(empty)} empty sessions[/claw.success]")
        return

    if not prefix:
        if not sessions:
            console.print("[dim]No saved sessions.[/dim]")
            return
        import datetime
        console.print("[bold]Sessions (use '/delete purge' to remove all empty ones):[/bold]")
        display = sessions[:30]
        for i, s in enumerate(display, 1):
            if isinstance(s.created_at, (int, float)):
                ts = datetime.datetime.fromtimestamp(s.created_at).strftime("%Y-%m-%d %H:%M:%S")
            else:
                ts = str(s.created_at)[:19]
            title = s.title or s.auto_title()
            console.print(
                f"  [cyan]{i}.[/cyan] [cyan]{s.session_id[:12]}[/cyan]  "
                f"{s.model}  {s.total_turns} turns  "
                f"[dim]{ts}[/dim]  {title[:40]}"
            )
        if len(sessions) > 30:
            console.print(f"  [dim]... and {len(sessions) - 30} more[/dim]")
        try:
            choice = console.input("\n[bold]Enter number or session-id prefix:[/bold] ").strip()
        except (KeyboardInterrupt, EOFError):
            return
        if not choice:
            return
        if choice.isdigit() and 1 <= int(choice) <= len(display):
            match = [display[int(choice) - 1]]
        else:
            match = [s for s in sessions if s.session_id.startswith(choice)]
    else:
        match = [s for s in sessions if s.session_id.startswith(prefix)]
    if not match:
        console.print(f"[claw.error]No session matching '{prefix}'[/claw.error]")
        return
    sess = match[0]
    delete_session(sess.session_id)
    console.print(f"  [claw.success]Deleted session {sess.session_id[:12]}[/claw.success]")


# --- One-shot mode ---

def oneshot(model: str, prompt: str):
    """Run a single prompt, print result, exit."""
    agent = make_agent(model)
    console.print(f"[dim]Model: {model}[/dim]\n")
    stream_response_enhanced(agent, prompt)


def oneshot_print(model: str, prompt: str):
    """Print-only mode: no tools, just stream text from the model."""
    import httpx as _hx
    console.print(f"[dim]Model: {model} (print mode — no tools)[/dim]\n")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are Claw, a helpful AI coding assistant. Answer concisely."},
            {"role": "user", "content": prompt},
        ],
        "stream": True,
    }
    try:
        with _hx.Client(timeout=300).stream(
            "POST", f"http://localhost:11434/api/chat", json=payload, timeout=300
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                delta = chunk.get("message", {}).get("content", "")
                if delta:
                    sys.stdout.write(delta)
                    sys.stdout.flush()
                if chunk.get("done"):
                    break
        sys.stdout.write("\n")
    except Exception as e:
        console.print(f"[claw.error]Error: {e}[/claw.error]")


# --- Main REPL ---

def main():
    parser = argparse.ArgumentParser(
        prog="claw",
        description="Claw Agent — local AI coding agent",
    )
    parser.add_argument("prompt", nargs="*", help="One-shot prompt (non-interactive)")
    parser.add_argument("--model", "-m", default=None, help="Model to use")
    parser.add_argument("--print", "-p", action="store_true", help="Print-only mode (no tools)")
    parser.add_argument(
        "--dangerously-skip-permissions", "--yolo",
        action="store_true", default=False,
        help="Skip all permission checks (auto-approve everything)",
    )
    parser.add_argument(
        "--max-turns", type=int, default=None,
        help="Max agent loop iterations per turn (default: 200)",
    )
    args = parser.parse_args()

    # Auto-detect: Use DeepSeek API if key is set, otherwise require Ollama
    from .agent import DEEPSEEK_API_KEY, DEFAULT_MODEL, DEFAULT_BASE_URL
    use_cloud = bool(DEEPSEEK_API_KEY)

    if use_cloud:
        # Cloud mode - no Ollama needed
        model = args.model or DEFAULT_MODEL
        console.print("[bold green]✓ Cloud Mode[/bold green] [dim](using DeepSeek API)[/dim]")
    else:
        # Local mode - check Ollama
        if not check_ollama():
            console.print(Panel(
                "[claw.error]Ollama is not running![/claw.error]\n\n"
                "  1. Install: [cyan]https://ollama.com/download[/cyan]\n"
                "  2. Start:   [cyan]ollama serve[/cyan]\n"
                "  3. Pull:    [cyan]ollama pull deepseek-v3.1:671b-cloud[/cyan]\n\n"
                "  Or set DEEPSEEK_API_KEY environment variable to use cloud mode instead.",
                title="Setup Required", border_style="red",
            ))
            sys.exit(1)
        models = list_models()
        model = args.model or pick_model(models)

    # Permission mode from CLI
    if getattr(args, 'dangerously_skip_permissions', False):
        permissions = PermissionContext.permissive()
        console.print("[bold yellow]⚠ Yolo mode: all permissions auto-approved[/bold yellow]")
    else:
        permissions = PermissionContext.default()

    # One-shot mode
    if args.prompt:
        if getattr(args, 'print', False):
            # Print-only mode: no tools, just text response
            oneshot_print(model, " ".join(args.prompt))
        else:
            oneshot(model, " ".join(args.prompt))
        sys.exit(0)

    # Interactive REPL
    print_banner(model, models)
    agent = make_agent(model, permissions=permissions)
    # Apply --max-turns override
    if args.max_turns is not None:
        agent._max_iterations = max(1, args.max_turns)
    prompt_session: PromptSession = PromptSession(
        history=FileHistory(HISTORY_PATH),
    )

    # Token counter state
    total_tokens = 0

    while True:
        try:
            # Claude Code-style prompt with ❯
            cwd_short = os.path.basename(os.getcwd())
            prompt_html = HTML(
                f'<style fg="ansibrightmagenta"><b>{cwd_short}</b></style>'
                f' <style fg="ansibrightmagenta">\u276f</style> '
            )
            user_input = prompt_session.prompt(prompt_html).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]\u2500 Goodbye![/dim]")
            break

        if not user_input:
            continue

        # Slash commands
        if user_input.startswith("/"):
            cmd_parts = user_input.split(maxsplit=1)
            cmd = cmd_parts[0].lower()
            cmd_arg = cmd_parts[1] if len(cmd_parts) > 1 else ""

            if cmd in ("/quit", "/exit", "/q"):
                console.print("[dim]\u2500 Goodbye![/dim]")
                break
            elif cmd == "/help":
                print_help()
            elif cmd == "/tools":
                cmd_tools()
            elif cmd == "/cost":
                cmd_cost(agent)
            elif cmd == "/model":
                if cmd_arg:
                    model = cmd_arg.strip()
                    agent = make_agent(model, session=agent.session)
                    console.print(f"  [dim]Model → {model}[/dim]")
                else:
                    for m in models:
                        marker = " *" if m == agent.model else ""
                        console.print(f"  [cyan]{m}[/cyan]{marker}")
            elif cmd == "/models":
                models = list_models()
                for m in models:
                    marker = " [claw.success]*[/claw.success]" if m == agent.model else ""
                    console.print(f"  [cyan]{m}[/cyan]{marker}")
            elif cmd == "/clear":
                agent = make_agent(agent.model)
                console.print("  [dim]Cleared.[/dim]")
            elif cmd == "/save":
                cmd_save(agent)
            elif cmd == "/sessions":
                cmd_sessions()
            elif cmd == "/resume":
                new_agent = cmd_resume(cmd_arg, model)
                if new_agent:
                    agent = new_agent
            elif cmd == "/continue":
                new_agent = cmd_continue(model)
                if new_agent:
                    agent = new_agent
            elif cmd == "/export":
                cmd_export(agent)
            elif cmd == "/compact":
                cmd_compact(agent)
            elif cmd == "/diff":
                cmd_diff()
            elif cmd == "/status":
                cmd_status()
            elif cmd == "/config":
                cmd_config(agent)
            elif cmd == "/version":
                cmd_version()
            elif cmd == "/doctor":
                cmd_doctor()
            elif cmd == "/permissions":
                cmd_permissions(agent, cmd_arg)
            elif cmd == "/memory":
                cmd_memory(agent)
            elif cmd == "/undo":
                cmd_undo()
            elif cmd == "/init":
                cmd_init()
            elif cmd == "/bug":
                cmd_bug(agent)
            elif cmd == "/delete":
                cmd_delete(cmd_arg)
            else:
                console.print(f"  [dim]Unknown: {cmd} — try /help[/dim]")
            continue

        # --- Run agent with streaming ---
        try:
            stream_response_enhanced(agent, user_input)
        except KeyboardInterrupt:
            console.print("\n  [dim]Interrupted.[/dim]")
            # M13: Auto-save on Ctrl+C so work isn't lost
            try:
                agent.session.title = agent.session.title or agent.session.auto_title()
                save_session(agent.session)
            except Exception:
                pass
        except Exception as e:
            console.print(f"  [claw.error]Error: {e}[/claw.error]")

        # Auto-save session after each turn (silent, never crashes the REPL)
        try:
            agent.session.title = agent.session.title or agent.session.auto_title()
            save_session(agent.session)
        except Exception:
            pass

        # Show compact cost line after each turn (Claude Code style)
        c = agent.cost
        if c.total_turns > 0:
            last = c.turns[-1]
            console.print(
                f"[dim]{c.total_tokens:,} tokens[/dim]"
                f" [dim]·[/dim] [dim]{last.duration_ms:.0f}ms[/dim]"
                f" [dim]·[/dim] [dim]{c.total_tool_calls} tool calls[/dim]"
                f" [dim]·[/dim] [dim]turn {c.total_turns}[/dim]"
            )


if __name__ == "__main__":
    main()
