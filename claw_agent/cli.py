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
    # Get local Ollama models
    local_models = []
    try:
        r = httpx.get("http://localhost:11434/api/tags", timeout=5)
        r.raise_for_status()
        local_models = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    
    # FIX: Add cloud/OpenRouter models when in cloud mode
    from .agent import DEEPSEEK_API_KEY, OPENROUTER_API_KEY, USE_COUNCIL
    from .ll_council import DEFAULT_COUNCIL_MODELS
    
    cloud_models = []
    if USE_COUNCIL and OPENROUTER_API_KEY:
        cloud_models = DEFAULT_COUNCIL_MODELS
    elif DEEPSEEK_API_KEY:
        cloud_models = ["deepseek-reasoner", "deepseek-chat", "deepseek-coder"]
    
    return local_models + cloud_models


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


def _cli_ask_user(question: str, options: list[str]) -> str:
    """Interactive ask_user callback for the CLI — prompts the user and returns their answer."""
    console.print()
    console.print(f"  [bold bright_yellow]❓ {question}[/bold bright_yellow]")
    if options:
        for i, opt in enumerate(options, 1):
            console.print(f"     [cyan]{i}.[/cyan] {opt}")
    try:
        raw = console.input("  [bold]Your answer:[/bold] ").strip()
    except (KeyboardInterrupt, EOFError):
        return "(user cancelled)"
    if not raw:
        return "(no answer provided)"
    # If user typed a number and there are options, return the option text
    if options and raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(options):
            return options[idx]
    return raw


def make_agent(model: str, session: Session | None = None, permissions: PermissionContext | None = None) -> Agent:
    return Agent(
        model=model,
        permissions=permissions or PermissionContext.default(),
        session=session or Session(model=model),
        confirm_fn=_cli_confirm,
        ask_fn=_cli_ask_user,
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

    # Detect mode type
    from .agent import DEEPSEEK_API_KEY, OPENROUTER_API_KEY, USE_COUNCIL
    is_council = USE_COUNCIL and OPENROUTER_API_KEY
    is_cloud = bool(DEEPSEEK_API_KEY) and not is_council
    
    if is_council:
        mode_icon = "🏛️"
        mode_text = "Council"
        model_display = f"{len(models)} models via OpenRouter"
    elif is_cloud:
        mode_icon = "☁️"
        mode_text = "Cloud"
        model_display = model
    else:
        mode_icon = "💻"
        mode_text = "Local"
        model_display = model

    console.print()
    console.print(f"[bold cyan]╭{'─' * 58}╮[/bold cyan]")
    console.print(f"[bold cyan]│[/bold cyan] [bold]🦞 Claw AI[/bold] [dim]v2.0 - Multi-Model Council[/dim]{' ' * 14}[bold cyan]│[/bold cyan]")
    console.print(f"[bold cyan]│[/bold cyan]{' ' * 58}[bold cyan]│[/bold cyan]")

    # Working directory
    cwd_display = cwd if len(cwd) <= 54 else "…" + cwd[-53:]
    cwd_pad = 58 - len(cwd_display) - 2
    console.print(f"[bold cyan]│[/bold cyan] [dim]{cwd_display}[/dim]{' ' * cwd_pad}[bold cyan]│[/bold cyan]")

    # Mode & Model
    mode_model = f"{mode_icon} {mode_text} • {model_display}"
    if len(mode_model) > 56:
        mode_model = mode_model[:53] + "..."
    mode_pad = 58 - len(mode_model) - 2
    console.print(f"[bold cyan]│[/bold cyan] [bold green]{mode_model}[/bold green]{' ' * mode_pad}[bold cyan]│[/bold cyan]")

    # Tools
    tools_str = f"{len(TOOL_REGISTRY)} tools available"
    tools_pad = 58 - len(tools_str) - 2
    console.print(f"[bold cyan]│[/bold cyan] [dim]{tools_str}[/dim]{' ' * tools_pad}[bold cyan]│[/bold cyan]")
    console.print(f"[bold cyan]│[/bold cyan]{' ' * 58}[bold cyan]│[/bold cyan]")

    # Quick tips
    console.print(f"[bold cyan]│[/bold cyan] [dim]💡 Type[/dim] [bold white]/help[/bold white] [dim]for commands[/dim]{' ' * 21}[bold cyan]│[/bold cyan]")
    console.print(f"[bold cyan]│[/bold cyan] [dim] Try:[/dim] [bold white]Write a Python function[/bold white]{' ' * 26}[bold cyan]│[/bold cyan]")
    console.print(f"[bold cyan]╰{'─' * 58}╯[/bold cyan]")
    console.print()


def print_help():
    from .agent import DEEPSEEK_API_KEY
    is_cloud = bool(DEEPSEEK_API_KEY)
    
    console.print()
    console.print(Panel.fit(
        "[bold]🦞 Claw AI v2.0 - Available Commands[/bold]\n"
        "[dim]Type any command below to execute it[/dim]",
        border_style="cyan",
        padding=(1, 2)
    ))
    console.print()

    # Detect active mode for footer
    from .agent import DEEPSEEK_API_KEY, OPENROUTER_API_KEY, USE_COUNCIL
    if USE_COUNCIL and OPENROUTER_API_KEY:
        mode_footer = "🏛️ Council Mode (14 models via OpenRouter + Alibaba)"
    elif DEEPSEEK_API_KEY:
        mode_footer = "☁️ Cloud Mode (DeepSeek API)"
    else:
        mode_footer = "💻 Local Mode (Ollama)"

    def _section(title: str, icon: str, items: list[tuple[str, str]]):
        console.print(f"  [bold cyan]{icon} [bold]{title}[/bold][/bold cyan]")
        for cmd, desc in items:
            console.print(f"    [bold white]{cmd:<28}[/bold white] [dim]{desc}[/dim]")
        console.print()

    _section("Core", "⚡", [
        ("/help", "Show this help message"),
        ("/model <name>", "Switch AI model (e.g., gpt-4o-mini)"),
        ("/models", "List all 14 council models"),
        ("/tools", f"List all {len(TOOL_REGISTRY)} available tools"),
        ("/cost", "Token usage & timing statistics"),
        ("/compact", "Compress conversation history"),
    ])
    
    _section("Sessions", "💾", [
        ("/save", "Save current session"),
        ("/sessions", "List saved sessions"),
        ("/resume <id>", "Resume session by ID"),
        ("/continue", "Quick-resume last session"),
        ("/delete <id>", "Delete a session"),
        ("/export", "Export to markdown"),
    ])
    
    _section("Workspace", "📁", [
        ("/status", "Workspace & project info"),
        ("/config", "Agent configuration"),
        ("/permissions [mode]", "Permission mode"),
        ("/memory", "Context window usage"),
        ("/undo", "Undo last file write"),
        ("/init", "Generate .claw config"),
    ])
    
    _section("Diagnostics", "🔧", [
        ("/version", "Version & platform info"),
        ("/doctor", "Run system diagnostics"),
        ("/bug", "Debug information"),
    ])
    
    _section("Git & Version Control", "🌿", [
        ("/commit", "AI-generated git commit message"),
        ("/branch [name]", "List branches or switch to one"),
        ("/diff", "Git diff of changes"),
    ])

    _section("Skills & MCP", "🔌", [
        ("/skills", "List installed skills"),
        ("/skill install <name>", "Install a skill (web-dev, data-science, etc.)"),
        ("/skill uninstall <name>", "Remove a skill"),
        ("/mcp", "List MCP servers"),
        ("/mcp add <name> <cmd>", "Add MCP server"),
        ("/mcp remove <name>", "Remove MCP server"),
    ])

    _section("Plan Mode", "📋", [
        ("/plan", "Toggle Plan Mode — agent plans but doesn't execute"),
        ("/context", "Show context window (messages, token usage)"),
        ("/add-dir [path]", "Add a directory to agent context"),
        ("/hooks [init]", "Show or initialize configured hooks"),
    ])

    _section("Account", "🔐", [
        ("/login", "Login with email/password"),
        ("/register", "Create a new account"),
        ("/logout", "Sign out"),
        ("/account", "View profile, plan & usage"),
        ("/billing", "View/upgrade your subscription plan"),
        ("/apikey", "Manage API keys"),
    ])
    
    _section("Settings", "⚙️", [
        ("/approval <mode>", "Set approval mode (auto/default/ask)"),
        ("/permissions [mode]", "Permission mode"),
    ])
    
    _section("Control", "⌨️", [
        ("/clear", "Clear conversation"),
        ("/quit", "Exit (also /exit, /q)"),
    ])
    
    mode_note = ""
    if USE_COUNCIL and OPENROUTER_API_KEY:
        mode_note = "🏛️ Council Mode (14 models via OpenRouter + Alibaba)"
    elif DEEPSEEK_API_KEY:
        mode_note = "☁️ Cloud Mode (DeepSeek API)"
    else:
        mode_note = "💻 Local Mode (Ollama)"
    console.print(f"  [dim]Active: {mode_note}[/dim]")
    console.print()


# --- Streaming display ---





def _render_markdown_response(text: str):
    """Render accumulated LLM response text as formatted Markdown via Rich."""
    if not text or not text.strip():
        return
    try:
        md = Markdown(text.strip(), code_theme="monokai")
        console.print(md)
    except Exception:
        # Fallback: print raw text if Markdown parsing fails
        console.print(text)


def stream_response_enhanced(agent: Agent, user_input: str):
    """Claude Code-style streaming with tool call display and Markdown rendering."""
    text_buffer = []  # Accumulate text deltas for batch Markdown rendering
    active_tool = False

    console.print()

    for event in agent.stream_chat(user_input):
        if isinstance(event, TextDelta):
            if not active_tool:
                text_buffer.append(event.text)

        elif isinstance(event, ToolCallStart):
            # Flush any accumulated text as rendered Markdown before tool display
            if text_buffer:
                _render_markdown_response("".join(text_buffer))
                text_buffer.clear()

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
            # Flush remaining text as rendered Markdown
            if text_buffer:
                _render_markdown_response("".join(text_buffer))
                text_buffer.clear()
            # Show system messages (iteration limit, circuit breakers)
            if event.final_text and event.final_text.startswith("["):
                console.print(f"  [dim]{event.final_text}[/dim]")
            break

    # Safety flush: render any leftover text (e.g. if stream ended without AgentDone)
    if text_buffer:
        _render_markdown_response("".join(text_buffer))

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
        label = prefix if prefix else '?'
        console.print(f"[claw.error]No session matching '{label}'[/claw.error]")
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
    from .agent import DEEPSEEK_API_KEY, OPENROUTER_API_KEY, USE_COUNCIL
    
    console.print()
    console.print("[bold]Running diagnostics...[/bold]\n")
    checks = []

    # 1. Python
    checks.append(("Python", True, sys.version.split()[0]))

    # 2. OpenRouter Council
    if USE_COUNCIL and OPENROUTER_API_KEY:
        from .ll_council import DEFAULT_COUNCIL_MODELS
        checks.append(("OpenRouter Council", True, f"✓ {len(DEFAULT_COUNCIL_MODELS)} models configured"))
    elif DEEPSEEK_API_KEY:
        checks.append(("DeepSeek Cloud", True, "✓ API key configured"))
    else:
        checks.append(("Cloud Mode", False, "No cloud API key set"))

    # 3. Ollama connectivity (optional if cloud mode is active)
    import httpx
    try:
        r = httpx.get("http://localhost:11434/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        checks.append(("Ollama Connection", True, f"{len(models)} models available"))
    except Exception as e:
        if USE_COUNCIL or DEEPSEEK_API_KEY:
            checks.append(("Ollama (Optional)", True, "Not running — OK, using cloud mode"))
        else:
            checks.append(("Ollama Connection", False, f"{str(e)[:60]}"))
        models = []

    # 4. Default model
    if USE_COUNCIL and OPENROUTER_API_KEY:
        checks.append(("Council Models", True, "8 models via OpenRouter"))
    elif models:
        preferred = "deepseek-v3.1:671b-cloud"
        has_preferred = any(preferred in m for m in models)
        checks.append(("Default Model", has_preferred, preferred if has_preferred else f"Not found — using {models[0]}"))
    else:
        checks.append(("Default Model", False, "No models available"))

    # 5. Tools
    checks.append(("Tool Registry", len(TOOL_REGISTRY) >= 22, f"{len(TOOL_REGISTRY)} tools loaded"))

    # 6. Session directory
    from .sessions import DEFAULT_SESSION_DIR
    checks.append(("Sessions Dir", DEFAULT_SESSION_DIR.exists(), str(DEFAULT_SESSION_DIR)))

    # 7. httpx
    try:
        import httpx as _h
        checks.append(("httpx", True, _h.__version__))
    except ImportError:
        checks.append(("httpx", False, "not installed"))

    # 8. rich
    try:
        from importlib.metadata import version as _pkg_version
        _rich_ver = _pkg_version("rich")
        checks.append(("rich", True, _rich_ver))
    except Exception:
        checks.append(("rich", False, "not installed"))

    # 9. Git (optional)
    import subprocess
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            checks.append(("Git", True, result.stdout.strip()))
        else:
            checks.append(("Git (Optional)", True, "Not installed — OK"))
    except Exception:
        checks.append(("Git (Optional)", True, "Not found — OK"))

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


# --- Auth Commands ---

def cmd_login():
    """Login with email/password via Supabase."""
    from .auth import get_auth_manager
    auth = get_auth_manager()
    if not auth.configured:
        console.print("  [yellow]Supabase not configured.[/yellow]")
        console.print("  [dim]Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.[/dim]")
        return
    if auth.logged_in:
        console.print(f"  [dim]Already logged in as {auth.email}[/dim]")
        console.print(f"  [dim]Use /logout first to switch accounts[/dim]")
        return
    try:
        email = console.input("  [bold]Email:[/bold] ").strip()
        if not email:
            return
        import getpass
        password = getpass.getpass("  Password: ")
        if not password:
            return
    except (KeyboardInterrupt, EOFError):
        return
    ok, msg = auth.login(email, password)
    if ok:
        console.print(f"  [claw.success]{msg}[/claw.success]")
    else:
        console.print(f"  [claw.error]{msg}[/claw.error]")


def cmd_register():
    """Create a new Supabase account."""
    from .auth import get_auth_manager
    auth = get_auth_manager()
    if not auth.configured:
        console.print("  [yellow]Supabase not configured.[/yellow]")
        console.print("  [dim]Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.[/dim]")
        return
    try:
        email = console.input("  [bold]Email:[/bold] ").strip()
        if not email:
            return
        display_name = console.input("  [bold]Display name:[/bold] ").strip() or email.split("@")[0]
        import getpass
        password = getpass.getpass("  Password (min 8 chars): ")
        if len(password) < 8:
            console.print("  [claw.error]Password must be at least 8 characters[/claw.error]")
            return
        confirm = getpass.getpass("  Confirm password: ")
        if password != confirm:
            console.print("  [claw.error]Passwords don't match[/claw.error]")
            return
    except (KeyboardInterrupt, EOFError):
        return
    ok, msg = auth.signup(email, password, display_name)
    if ok:
        console.print(f"  [claw.success]{msg}[/claw.success]")
    else:
        console.print(f"  [claw.error]{msg}[/claw.error]")


def cmd_logout():
    """Sign out of Supabase."""
    from .auth import get_auth_manager
    auth = get_auth_manager()
    ok, msg = auth.logout()
    console.print(f"  [dim]{msg}[/dim]")


def cmd_account():
    """Show current account info, plan, and usage."""
    from .auth import get_auth_manager
    auth = get_auth_manager()
    if not auth.logged_in:
        console.print("  [dim]Not logged in. Use /login or /register[/dim]")
        return
    profile = auth.profile
    plan = auth.plan
    console.print()
    console.print(f"  [bold cyan]🔐 Account[/bold cyan]")
    console.print(f"    Email: [bold]{profile.email}[/bold]")
    console.print(f"    Name: {profile.display_name}")
    console.print(f"    Role: {profile.role}")
    console.print(f"    Plan: [bold magenta]{plan.display_name if plan else 'Free'}[/bold magenta]")
    console.print()
    if plan:
        day_used = profile.tokens_used_today
        day_max = plan.max_tokens_per_day
        month_used = profile.tokens_used_month
        month_max = plan.max_tokens_per_month
        console.print(f"  [bold]Token Usage[/bold]")
        if day_max == -1:
            console.print(f"    Today: {day_used:,} (unlimited)")
        else:
            pct = (day_used / day_max * 100) if day_max else 0
            bar_f = int(pct / 5)
            bar = "█" * bar_f + "░" * (20 - bar_f)
            console.print(f"    Today: {day_used:,} / {day_max:,} [{bar}] {pct:.0f}%")
        if month_max == -1:
            console.print(f"    Month: {month_used:,} (unlimited)")
        else:
            pct = (month_used / month_max * 100) if month_max else 0
            bar_f = int(pct / 5)
            bar = "█" * bar_f + "░" * (20 - bar_f)
            console.print(f"    Month: {month_used:,} / {month_max:,} [{bar}] {pct:.0f}%")
        console.print(f"    Total: {profile.total_tokens_used:,}")
        console.print()
        console.print(f"  [bold]Features[/bold]")
        features = []
        if plan.council_access:
            features.append("[green]✓[/green] Council")
        if plan.cloud_models:
            features.append("[green]✓[/green] Cloud Models")
        if plan.ultrathink_mode:
            features.append("[green]✓[/green] UltraThink")
        if plan.mcp_access:
            features.append("[green]✓[/green] MCP")
        if plan.api_access:
            features.append("[green]✓[/green] API Access")
        if plan.custom_skills:
            features.append("[green]✓[/green] Custom Skills")
        for f in features:
            console.print(f"    {f}")
    console.print()


def cmd_billing_plan():
    """Show available subscription plans and current plan."""
    from .auth import get_auth_manager
    auth = get_auth_manager()
    if not auth.configured:
        console.print("  [dim]Supabase not configured — running in local mode (no plan limits)[/dim]")
        return
    plans = auth.client.get_plans(auth.session.access_token if auth.logged_in else "")
    current_plan_id = auth.profile.plan_id if auth.logged_in and auth.profile else ""
    console.print()
    console.print(f"  [bold cyan]📋 Available Plans[/bold cyan]")
    console.print()
    for p in plans:
        current = " [green]◄ CURRENT[/green]" if p.get("id") == current_plan_id else ""
        price = f"${p.get('price_monthly', 0)}/mo" if p.get("price_monthly", 0) > 0 else "Free"
        console.print(f"  [bold]{p.get('display_name', p.get('name'))}{current}[/bold] — {price}")
        console.print(f"    [dim]{p.get('description', '')}[/dim]")
        tok_day = p.get("max_tokens_per_day", 0)
        tok_mo = p.get("max_tokens_per_month", 0)
        console.print(f"    Tokens: {tok_day:,}/day, {tok_mo:,}/month" if tok_day != -1 else f"    Tokens: unlimited/day, unlimited/month")
        features = []
        if p.get("council_access"):
            features.append("Council")
        if p.get("cloud_models"):
            features.append("Cloud")
        if p.get("ultrathink_mode"):
            features.append("UltraThink")
        if p.get("mcp_access"):
            features.append("MCP")
        if p.get("api_access"):
            features.append("API")
        if features:
            console.print(f"    Features: {', '.join(features)}")
        console.print()


def cmd_apikey(arg: str):
    """Manage API keys."""
    from .auth import get_auth_manager
    auth = get_auth_manager()
    if not auth.logged_in:
        console.print("  [dim]Login first with /login[/dim]")
        return
    if not auth.plan or not auth.plan.api_access:
        console.print("  [yellow]API access requires Pro plan or higher.[/yellow]")
        return
    sub = arg.strip().lower()
    if sub == "create" or sub == "new":
        try:
            name = console.input("  [bold]Key name:[/bold] ").strip() or "Default"
        except (KeyboardInterrupt, EOFError):
            return
        raw_key, result = auth.client.create_api_key(
            auth.user_id, name, auth.session.access_token
        )
        console.print()
        console.print(f"  [claw.success]API Key created![/claw.success]")
        console.print(f"  [bold yellow]Key: {raw_key}[/bold yellow]")
        console.print(f"  [claw.error]⚠ Save this key — it won't be shown again![/claw.error]")
    elif sub == "list" or not sub:
        keys = auth.client.list_api_keys(auth.user_id, auth.session.access_token)
        if not keys:
            console.print("  [dim]No API keys. Create one with /apikey create[/dim]")
            return
        console.print()
        console.print(f"  [bold]Your API Keys[/bold]")
        for k in keys:
            status = "[green]active[/green]" if k.get("is_active") else "[red]revoked[/red]"
            console.print(f"    {k.get('key_prefix', '???')}... — {k.get('name', '')} — {status}")
    else:
        console.print("  [dim]Usage: /apikey [list|create][/dim]")


# --- Skills Commands ---

def cmd_skills(arg: str):
    """List or manage skills."""
    from .skills import list_skills, install_skill, uninstall_skill, format_skills_table
    
    if not arg or arg.strip() == "list":
        # List all skills
        skills = list_skills()
        console.print()
        console.print("[bold cyan] Installed Skills[/bold cyan]")
        console.print()
        
        if not skills:
            console.print("  [dim]No skills installed.[/dim]")
            console.print("  [dim]Install with: /skill install <name>[/dim]")
        else:
            # Group by type
            builtin = [s for s in skills if s.is_builtin]
            custom = [s for s in skills if not s.is_builtin]
            
            if custom:
                console.print("  [bold]Custom Skills[/bold]")
                for s in custom:
                    console.print(f"    [green]✓[/green] [bold]{s.name}[/bold] v{s.version} - {s.description}")
                console.print()
            
            if builtin:
                console.print("  [bold]Built-in Skills[/bold]")
                for s in builtin:
                    console.print(f"    [cyan]○[/cyan] [bold]{s.name}[/bold] v{s.version} - {s.description}")
                console.print()
            
            console.print("  [dim]Install: /skill install <name>[/dim]")
            console.print("  [dim]Remove: /skill uninstall <name>[/dim]")
    else:
        console.print(f"  [dim]Unknown skill command: {arg}[/dim]")
        console.print("  [dim]Try: /skills or /skill list[/dim]")


def cmd_skill_manage(arg: str):
    """Install or uninstall a skill."""
    from .skills import install_skill, uninstall_skill, list_skills
    
    if not arg:
        console.print("  [dim]Usage: /skill <install|uninstall> <name>[/dim]")
        console.print("  [dim]Example: /skill install web-dev[/dim]")
        return
    
    parts = arg.strip().split(maxsplit=1)
    action = parts[0].lower()
    name = parts[1] if len(parts) > 1 else ""
    
    if action == "install":
        if not name:
            console.print("  [dim]Usage: /skill install <name>[/dim]")
            console.print("  [dim]Available: web-dev, data-science, devops, security, api-dev[/dim]")
            return
        result = install_skill(name)
        console.print(f"  {result}")
    
    elif action == "uninstall":
        if not name:
            console.print("  [dim]Usage: /skill uninstall <name>[/dim]")
            return
        result = uninstall_skill(name)
        console.print(f"  {result}")
    
    elif action == "list":
        cmd_skills("")
    
    else:
        console.print(f"  [dim]Unknown action: {action}[/dim]")
        console.print("  [dim]Try: install, uninstall, or list[/dim]")


# --- New Claude-parity commands ---

def cmd_commit(agent: Agent):
    """AI-generated git commit — stages changes and creates a commit with an AI message."""
    import subprocess
    # Check for changes
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, timeout=10)
    if not result.stdout.strip():
        console.print("  [dim]No changes to commit.[/dim]")
        return
    # Get diff for AI to summarize
    diff_result = subprocess.run(["git", "diff", "--cached", "--stat"], capture_output=True, text=True, timeout=10)
    if not diff_result.stdout.strip():
        # Nothing staged — stage all
        subprocess.run(["git", "add", "-A"], timeout=10)
        diff_result = subprocess.run(["git", "diff", "--cached", "--stat"], capture_output=True, text=True, timeout=10)
    diff_text = diff_result.stdout.strip() or result.stdout.strip()
    console.print("  [dim]Generating commit message...[/dim]")
    msg = agent.chat(
        f"Write a concise conventional git commit message for these changes (one line, imperative mood, <72 chars):\n\n{diff_text[:3000]}\n\nRespond with ONLY the commit message, nothing else."
    )
    msg = msg.strip().strip('"').strip("'").split("\n")[0][:72]
    console.print(f"  [bold]Message:[/bold] {msg}")
    try:
        confirm = console.input("  [bold]Commit? (y/n/e to edit):[/bold] ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        return
    if confirm == "e":
        try:
            msg = console.input("  [bold]Edit message:[/bold] ").strip() or msg
        except (KeyboardInterrupt, EOFError):
            return
        confirm = "y"
    if confirm in ("y", "yes"):
        r = subprocess.run(["git", "commit", "-m", msg], capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            console.print(f"  [claw.success]✓ Committed: {msg}[/claw.success]")
        else:
            console.print(f"  [claw.error]Commit failed: {r.stderr.strip()[:200]}[/claw.error]")
    else:
        console.print("  [dim]Cancelled.[/dim]")


def cmd_hooks(arg: str = ""):
    """Show configured hooks or set them up."""
    from .hooks import HookRunner
    runner = HookRunner.load()
    hooks_path = os.path.join(os.path.expanduser("~"), ".claw-agent", "hooks.json")

    sub = arg.strip().lower()
    if sub == "init":
        if os.path.exists(hooks_path):
            console.print(f"  [dim]hooks.json already exists at {hooks_path}[/dim]")
        else:
            example = [
                {"event": "pre_tool_use", "tools": ["run_command"], "command": "echo 'pre-hook'"},
                {"event": "post_tool_use", "tools": ["write_file"], "command": "echo 'post-hook'"},
            ]
            import json as _json
            os.makedirs(os.path.dirname(hooks_path), exist_ok=True)
            with open(hooks_path, "w") as f:
                _json.dump(example, f, indent=2)
            console.print(f"  [claw.success]Created {hooks_path}[/claw.success]")
        return

    console.print()
    console.print(f"  [bold cyan]🔗 Hooks[/bold cyan]")
    console.print(f"  [dim]Config: {hooks_path}[/dim]")
    console.print()
    if not runner.hooks:
        console.print("  [dim]No hooks configured.[/dim]")
        console.print("  [dim]Create hooks.json at ~/.claw-agent/hooks.json or run /hooks init[/dim]")
        console.print()
        console.print("  [dim]Hook format:[/dim]")
        console.print('  [dim]  {"event": "pre_tool_use", "tools": ["run_command"], "command": "your-script"}[/dim]')
        console.print('  [dim]  {"event": "post_tool_use", "tools": ["write_file"], "command": "your-script"}[/dim]')
    else:
        console.print(f"  [bold]{len(runner.hooks)} hook(s) configured:[/bold]")
        for i, h in enumerate(runner.hooks, 1):
            event = h.get("event", "?")
            tools = h.get("tools", "all")
            cmd = h.get("command", "?")
            console.print(f"  [cyan]{i}.[/cyan] [{event}] tools={tools!r}: {cmd}")
    console.print()
    console.print("  [dim]Events: pre_tool_use, post_tool_use[/dim]")
    console.print("  [dim]Run /hooks init to create an example config.[/dim]")


def cmd_plan(agent: Agent):
    """Toggle Plan Mode — agent will propose steps without executing tools."""
    agent._plan_mode = not agent._plan_mode
    if agent._plan_mode:
        # Inject plan mode system message
        agent.messages.append({
            "role": "system",
            "content": (
                "PLAN MODE ACTIVATED. You are now in plan-only mode. "
                "DO NOT call any tools (except ask_user, enter_plan_mode, exit_plan_mode). "
                "Instead, describe your plan as numbered steps and STOP. "
                "Wait for the user to approve the plan before executing. "
                "When the user approves, call exit_plan_mode to resume normal execution."
            ),
        })
        console.print("  [bold yellow]📋 Plan Mode ON[/bold yellow] — agent will plan but not execute.")
        console.print("  [dim]Ask a question to see a plan. Run /plan again to turn off.[/dim]")
    else:
        # Remove plan-mode system messages
        agent.messages = [
            m for m in agent.messages
            if not (m.get("role") == "system" and "PLAN MODE ACTIVATED" in m.get("content", ""))
        ]
        console.print("  [bold green]▶ Plan Mode OFF[/bold green] — normal execution resumed.")


def cmd_add_dir(arg: str, agent: Agent):
    """Add a directory to the agent's workspace context."""
    target = (arg or os.getcwd()).strip()
    if not os.path.isdir(target):
        console.print(f"  [claw.error]Not a directory: {target}[/claw.error]")
        return
    abs_target = os.path.abspath(target)
    # Inject as a system message into the conversation
    import glob as _glob
    files = _glob.glob(os.path.join(abs_target, "**", "*"), recursive=True)
    files = [f for f in files if os.path.isfile(f)][:200]  # cap at 200
    rel_files = [os.path.relpath(f, abs_target) for f in files]
    summary = f"ADDED DIRECTORY: {abs_target}\n{len(files)} files:\n" + "\n".join(rel_files[:50])
    if len(rel_files) > 50:
        summary += f"\n... and {len(rel_files) - 50} more"
    agent.messages.append({"role": "system", "content": summary})
    console.print(f"  [claw.success]Added {abs_target} ({len(files)} files) to context[/claw.success]")


def cmd_branch(arg: str = ""):
    """Switch git branches or list available branches."""
    import subprocess
    sub = arg.strip()
    if not sub:
        # List branches
        result = subprocess.run(["git", "branch", "--all"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            console.print("  [dim]Not a git repo or git not available.[/dim]")
            return
        console.print()
        console.print("  [bold]Git Branches:[/bold]")
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line.startswith("* "):
                console.print(f"  [green]* {line[2:]}[/green] (current)")
            elif line:
                console.print(f"  [dim]  {line}[/dim]")
        console.print()
        console.print("  [dim]Switch with: /branch <name>[/dim]")
        return

    # Switch to branch
    result = subprocess.run(["git", "checkout", sub], capture_output=True, text=True, timeout=15)
    if result.returncode == 0:
        console.print(f"  [claw.success]✓ Switched to branch: {sub}[/claw.success]")
        if result.stdout.strip():
            console.print(f"  [dim]{result.stdout.strip()}[/dim]")
    else:
        console.print(f"  [claw.error]Branch switch failed: {result.stderr.strip()[:200]}[/claw.error]")


def cmd_context(agent: Agent):
    """Show current context window — messages, sizes, types."""
    console.print()
    console.print("  [bold cyan]📐 Context Window[/bold cyan]")
    console.print()
    total_chars = 0
    for i, msg in enumerate(agent.messages):
        role = msg.get("role", "?")
        content = str(msg.get("content", ""))
        tc = msg.get("tool_calls")
        chars = len(content)
        total_chars += chars
        tokens_est = chars // 4
        role_color = {"system": "yellow", "user": "green", "assistant": "blue", "tool": "cyan"}.get(role, "white")
        tc_label = f" +{len(tc)} tool_calls" if tc else ""
        preview = content[:60].replace("\n", " ")
        if len(content) > 60:
            preview += "…"
        console.print(
            f"  [{role_color}][{i}] {role:<10}[/{role_color}] "
            f"[dim]{tokens_est:>5} tok  {preview}{tc_label}[/dim]"
        )
    total_tokens = total_chars // 4
    from .agent import MAX_CONTEXT_TOKENS
    pct = total_tokens / MAX_CONTEXT_TOKENS * 100
    bar_f = int(pct / 5)
    bar = "█" * bar_f + "░" * (20 - bar_f)
    console.print()
    console.print(f"  Total: ~{total_tokens:,} tokens ({pct:.1f}%) [{bar}]")
    console.print(f"  Max: {MAX_CONTEXT_TOKENS:,} tokens")
    console.print()


# --- MCP Commands ---

def cmd_mcp(arg: str):
    """Manage MCP servers."""
    from .mcp import load_mcp_config, add_mcp_server, remove_mcp_server, list_mcp_servers
    
    servers = load_mcp_config()
    
    if not arg or arg.strip() == "list":
        # List MCP servers
        console.print()
        console.print("[bold cyan]🔌 MCP Servers[/bold cyan]")
        console.print()
        
        if not servers:
            console.print("  [dim]No MCP servers configured.[/dim]")
            console.print("  [dim]Add with: /mcp add <name> <command>[/dim]")
        else:
            console.print(f"  {'Name':<20} {'Command':<30} {'Transport':<12} {'Status'}")
            console.print("  " + "─" * 75)
            for name, server in servers.items():
                status = "[green]enabled[/green]" if server.enabled else "[dim]disabled[/dim]"
                console.print(f"  {name:<20} {server.command:<30} {server.transport:<12} {status}")
            console.print()
            console.print("  [dim]Add: /mcp add <name> <command>[/dim]")
            console.print("  [dim]Remove: /mcp remove <name>[/dim]")
    else:
        parts = arg.strip().split(maxsplit=2)
        action = parts[0].lower()
        
        if action == "add" and len(parts) >= 3:
            name = parts[1]
            command = parts[2]
            result = add_mcp_server(name, command)
            console.print(f"  {result}")
        elif action == "remove" and len(parts) >= 2:
            name = parts[1]
            result = remove_mcp_server(name)
            console.print(f"  {result}")
        else:
            console.print("  [dim]Usage: /mcp [list|add <name> <cmd>|remove <name>][/dim]")


# --- Approval Mode (Claude-like) ---

def cmd_approval(arg: str, agent: Agent):
    """Set approval mode (like Claude Code)."""
    if not arg:
        console.print()
        console.print("[bold cyan]⚙️ Approval Mode[/bold cyan]")
        console.print()
        current = "AUTO" if agent.permissions.auto_approve else "DEFAULT"
        console.print(f"  Current: [bold]{current}[/bold]")
        console.print()
        console.print("  Available modes:")
        console.print("    [bold]auto[/bold]     - Auto-approve all tool calls (yolo mode)")
        console.print("    [bold]default[/bold]  - Ask for confirmation on dangerous tools")
        console.print("    [bold]ask[/bold]      - Always ask for confirmation")
        console.print()
        console.print("  [dim]Set with: /approval <mode>[/dim]")
        return
    
    mode = arg.strip().lower()
    
    if mode == "auto":
        agent.permissions.auto_approve = True
        console.print("  [bold yellow]⚠ Approval mode: AUTO[/bold yellow]")
        console.print("  [dim]All tool calls will be auto-approved[/dim]")
    elif mode == "default":
        agent.permissions.auto_approve = False
        console.print("  [bold green]✓ Approval mode: DEFAULT[/bold green]")
        console.print("  [dim]Dangerous tools will require confirmation[/dim]")
    elif mode == "ask":
        agent.permissions.auto_approve = False
        console.print("  [bold blue]ℹ Approval mode: ASK[/bold blue]")
        console.print("  [dim]All tool calls will require confirmation[/dim]")
    else:
        console.print(f"  [dim]Unknown mode: {mode}[/dim]")
        console.print("  [dim]Try: auto, default, or ask[/dim]")


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
        with open(config_path, "r") as f:
            content = f.read()
        console.print(Panel(content, title=".claw", border_style="cyan"))
        return
    # Auto-detect project
    config = {
        "model": "deepseek-r1:671b",
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

def oneshot(model: str, prompt: str, output_format: str = "text"):
    """Run a single prompt, print result, exit."""
    import json as _json_mod
    agent = make_agent(model)
    if output_format == "text":
        console.print(f"[dim]Model: {model}[/dim]\n")
        stream_response_enhanced(agent, prompt)
    elif output_format in ("json", "stream-json"):
        from .agent import TextDelta, ToolCallStart, AgentDone
        result_chunks: list[str] = []
        tool_calls_made: list[dict] = []
        for event in agent.stream_chat(prompt):
            if isinstance(event, TextDelta):
                result_chunks.append(event.text)
                if output_format == "stream-json":
                    sys.stdout.write(_json_mod.dumps({"type": "text", "text": event.text}) + "\n")
                    sys.stdout.flush()
            elif isinstance(event, ToolCallStart):
                tool_calls_made.append({"name": event.name, "args": event.arguments})
        if output_format == "json":
            full_text = "".join(result_chunks)
            out = {"model": model, "result": full_text, "tool_calls": tool_calls_made}
            sys.stdout.write(_json_mod.dumps(out, indent=2) + "\n")
    else:
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
    parser.add_argument(
        "-c", "--continue", dest="continue_session", action="store_true", default=False,
        help="Continue the most recent conversation session",
    )
    parser.add_argument(
        "--resume", dest="resume_session", default=None, metavar="SESSION_ID",
        help="Resume a specific session by ID",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", default=False,
        help="Verbose output — show token counts, timing, and tool details",
    )
    parser.add_argument(
        "--output-format", choices=["text", "json", "stream-json"], default="text",
        help="Output format for one-shot (non-interactive) mode",
    )
    args = parser.parse_args()

    # Auto-detect: Priority 1) OpenRouter Council 2) DeepSeek 3) Ollama
    from .agent import DEEPSEEK_API_KEY, OPENROUTER_API_KEY, USE_COUNCIL, DEFAULT_MODEL, DEFAULT_BASE_URL
    from .ll_council import DEFAULT_COUNCIL_MODELS
    
    models = []

    if USE_COUNCIL and OPENROUTER_API_KEY:
        # Council mode - use OpenRouter with multiple models
        model = args.model or "council"  # Special "council" model triggers council mode
        models = DEFAULT_COUNCIL_MODELS
        console.print(f"[bold green]✓ Council Mode[/bold green] [dim]({len(models)} models via OpenRouter)[/dim]")
        console.print(f"[dim]  Models: {', '.join(m.split('/')[-1] for m in models[:4])}...[/dim]")
    elif DEEPSEEK_API_KEY:
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
                "  Or set OPENROUTER_API_KEY or DEEPSEEK_API_KEY for cloud mode.",
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
            oneshot(model, " ".join(args.prompt), output_format=args.output_format)
        sys.exit(0)

    # Interactive REPL
    print_banner(model, models)
    agent = make_agent(model, permissions=permissions)
    # Apply --max-turns override
    if args.max_turns is not None:
        agent._max_iterations = max(1, args.max_turns)
    # Apply --verbose
    if args.verbose:
        agent._verbose = True
    # Apply --continue / --resume (load previous session)
    resumed = False
    if args.resume_session:
        try:
            from .sessions import load_session
            sess = load_session(args.resume_session)
            agent.messages = sess.messages
            console.print(f"  [dim]Resumed session {args.resume_session} ({len(agent.messages)} messages)[/dim]")
            resumed = True
        except FileNotFoundError:
            console.print(f"  [claw.error]Session not found: {args.resume_session}[/claw.error]")
        except Exception as e:
            console.print(f"  [dim]Could not resume session: {e}[/dim]")
    elif args.continue_session:
        try:
            from .sessions import list_sessions
            sessions = list_sessions()
            if sessions:
                latest = sessions[0]
                agent.messages = latest.messages
                console.print(f"  [dim]Continuing most recent session ({len(agent.messages)} messages)[/dim]")
                resumed = True
            else:
                console.print("  [dim]No previous session found, starting fresh.[/dim]")
        except Exception as e:
            console.print(f"  [dim]Could not continue session: {e}[/dim]")
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
                    # FIX: Show models with proper output
                    current_models = list_models()
                    if not current_models:
                        console.print("  [yellow]No local models available[/yellow]")
                        from .agent import DEEPSEEK_API_KEY, OPENROUTER_API_KEY, USE_COUNCIL
                        if USE_COUNCIL and OPENROUTER_API_KEY:
                            console.print("  [green]✓ Council mode active (8 OpenRouter models)[/green]")
                        elif DEEPSEEK_API_KEY:
                            console.print("  [green]✓ Cloud mode using DeepSeek[/green]")
                    else:
                        for m in current_models[:20]:
                            marker = " [green]*[/green]" if m == agent.model else ""
                            console.print(f"  [cyan]{m}[/cyan]{marker}")
                        if len(current_models) > 20:
                            console.print(f"  [dim]... and {len(current_models) - 20} more[/dim]")
            elif cmd == "/models":
                # FIX: Always show models with proper output
                current_models = list_models()
                from .agent import DEEPSEEK_API_KEY, OPENROUTER_API_KEY, USE_COUNCIL
                from .ll_council import DEFAULT_COUNCIL_MODELS
                
                if USE_COUNCIL and OPENROUTER_API_KEY:
                    console.print("  [green bold]🏛️ Council Models (8 via OpenRouter)[/green bold]")
                    console.print()
                    tier1 = ["deepseek/deepseek-v3", "qwen/qwen3-80b", "meta-llama/llama-3.3-70b-instruct"]
                    tier2 = ["qwen/qwen-2.5-coder-32b-instruct", "deepseek/deepseek-r1"]
                    tier3 = ["google/gemma-3-12b-it", "openai/gpt-4o-mini", "anthropic/claude-3-haiku-20240307"]
                    
                    console.print("  [bold]🥇 Tier 1 - Most Powerful:[/bold]")
                    for m in tier1:
                        console.print(f"    [cyan]• {m}[/cyan]")
                    console.print()
                    console.print("  [bold]⭐ Tier 2 - Specialized:[/bold]")
                    for m in tier2:
                        console.print(f"    [cyan]• {m}[/cyan]")
                    console.print()
                    console.print("  [bold]⚡ Tier 3 - Fast:[/bold]")
                    for m in tier3:
                        console.print(f"    [cyan]• {m}[/cyan]")
                elif current_models:
                    console.print(f"  [bold]Available Models ({len(current_models)}):[/bold]")
                    for m in current_models[:20]:
                        marker = " [green]* current[/green]" if m == agent.model else ""
                        console.print(f"    [cyan]• {m}[/cyan]{marker}")
                else:
                    console.print("  [yellow]No models available[/yellow]")
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
            # Skills commands
            elif cmd == "/skills":
                cmd_skills(cmd_arg)
            elif cmd == "/skill":
                cmd_skill_manage(cmd_arg)
            # New parity commands
            elif cmd == "/commit":
                cmd_commit(agent)
            elif cmd == "/hooks":
                cmd_hooks(cmd_arg)
            elif cmd == "/plan":
                cmd_plan(agent)
            elif cmd in ("/add-dir", "/adddir"):
                cmd_add_dir(cmd_arg, agent)
            elif cmd == "/branch":
                cmd_branch(cmd_arg)
            elif cmd == "/context":
                cmd_context(agent)
            # MCP commands
            elif cmd == "/mcp":
                cmd_mcp(cmd_arg)
            # Approval mode (Claude-like)
            elif cmd == "/approval":
                cmd_approval(cmd_arg, agent)
            # Auth commands
            elif cmd == "/login":
                cmd_login()
            elif cmd == "/register":
                cmd_register()
            elif cmd == "/logout":
                cmd_logout()
            elif cmd == "/account":
                cmd_account()
            elif cmd in ("/billing",):
                cmd_billing_plan()
            elif cmd == "/apikey":
                cmd_apikey(cmd_arg)
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
