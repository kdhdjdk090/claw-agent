"""Core agent loop with streaming - orchestrates Ollama + tool execution.

Supports both blocking chat() and streaming stream_chat() for CLI/UI use.
"""

from __future__ import annotations

import json
import inspect
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Generator

import httpx

from .tools import TOOL_REGISTRY, OLLAMA_TOOL_DEFINITIONS
from .permissions import PermissionContext, GATED_TOOLS
from .sessions import Session
from .cost_tracker import CostTracker
from .hooks import HookRunner
from .mcp import MCPManager
from .codex_runtime import CodexRuntime, CodexTaskResult

# Configure logging for claw_agent module
logger = logging.getLogger("claw_agent")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

try:
    import tiktoken
    _enc = tiktoken.encoding_for_model("gpt-4")
except Exception:
    _enc = None


def _load_project_env() -> None:
    """Load workspace .env.local / .env files for local CLI runs.

    Searches upward from *both* the current working directory and the
    package install directory so `claw` works regardless of where the
    user invokes it from.
    """
    # Collect unique starting directories: package dir first (most reliable),
    # then its parent, then cwd.  Package dir takes priority so an unrelated
    # .env.local in the users cwd (e.g. Vercel CLI token) cannot shadow the
    # real API keys stored next to the package.
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    start_dirs: list[str] = []
    for d in (pkg_dir, os.path.dirname(pkg_dir), os.getcwd()):
        d = os.path.normpath(d)
        if d not in start_dirs:
            start_dirs.append(d)

    for filename in (".env.local", ".env"):
        for start in start_dirs:
            search = start
            for _ in range(4):
                path = os.path.join(search, filename)
                if os.path.isfile(path):
                    try:
                        with open(path, "r", encoding="utf-8", errors="replace") as f:
                            for raw_line in f:
                                line = raw_line.strip()
                                if not line or line.startswith("#") or "=" not in line:
                                    continue
                                key, value = line.split("=", 1)
                                key = key.strip()
                                value = value.strip()
                                if value and len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                                    value = value[1:-1]
                                if key:
                                    os.environ[key] = value
                    except OSError:
                        pass
                    return  # found and loaded — stop searching
                parent = os.path.dirname(search)
                if parent == search:
                    break
                search = parent


_load_project_env()

# Populate DEFAULT_COUNCIL_MODELS now that env vars are loaded.
from .ll_council import OPENROUTER_MODELS, _get_default_council as _init_council  # noqa: E402
_init_council()


def _get_live_datetime() -> str:
    """Return the real current date/time from the host system clock."""
    now = datetime.now(timezone.utc)
    local = datetime.now()
    return (
        f"{local.strftime('%A, %d %B %Y  %H:%M:%S')} (local)  |  "
        f"{now.strftime('%Y-%m-%dT%H:%M:%SZ')} (UTC)"
    )


def _build_tools_section() -> str:
    """Dynamically build the TOOLS section from the live TOOL_REGISTRY."""
    # Group tools by their source module (e.g. file_tools → File)
    groups: dict[str, list[str]] = {}
    for name, fn in TOOL_REGISTRY.items():
        mod = getattr(fn, "__module__", "") or ""
        # Extract category from module name: claw_agent.tools.git_tools → Git
        if "." in mod:
            mod_short = mod.rsplit(".", 1)[-1]  # "git_tools"
        else:
            mod_short = mod
        label = mod_short.replace("_tools", "").replace("_", " ").title()
        if not label or label == "Mcp":
            label = "MCP"
        groups.setdefault(label, []).append(name)
    lines = [f"TOOLS ({len(TOOL_REGISTRY)}):"]
    for label in sorted(groups):
        tools_str = ", ".join(sorted(groups[label]))
        lines.append(f"  {label}: {tools_str}")
    return "\n".join(lines)


SYSTEM_PROMPT_TEMPLATE = """\
You are Claw, an expert autonomous AI coding agent running on model "{model}".
You have deep expertise in all programming languages, frameworks, databases, DevOps, cloud, \
system administration, and software engineering. You act decisively.
When asked what model you are, say you are Claw running on "{model}" {mode_label}.

CURRENT DATE & TIME (LIVE — from host system clock):
{current_datetime}
IMPORTANT: This is the REAL current date/time. NEVER guess, fabricate, or hallucinate dates.
If asked for the current date/time, use the value above or call the `now_tz` tool for other timezones.
NEVER cite external time services (NIST, time.gov, GPS) — you cannot access them. Use your tools.

WORKSPACE: {cwd}
PLATFORM: {platform}

{tools_section}

SUPERPOWERS — your approach to any task:
1. EXPLORE first: list_directory, find_files, grep_search, get_workspace_context to map the codebase.
2. UNDERSTAND: read_file relevant files. Read imports, types, tests. Understand before editing.
3. PLAN: For complex tasks, use task_create to track steps. For massive tasks, use plan_and_execute.
4. ACT: write_file, replace_in_file, multi_edit_file, run_command. Make changes precisely.
5. VERIFY: read_file the result. Run tests with run_command. Check git_diff. Confirm correctness.

EPISTEMIC REASONING — how you handle knowledge, truth, and uncertainty:
This is your logic method. Follow it for EVERY response, not just code tasks.

1. THINK BEFORE YOU SPEAK: For non-trivial questions, reason through the problem step-by-step
   internally before committing to an answer. Never jump to conclusions.
2. KNOW YOUR LIMITS: Your training data has a cutoff date. For ANY claim about current events,
   recent news, live prices, real-time data, or time-sensitive facts → you MUST call `web_search`
   FIRST. NEVER generate current events, news, or geopolitical information from memory alone.
   You DO have live web access via `web_search` and `web_fetch` when network access is available.
   If asked whether you can browse/search the live web, answer yes and explain that you verify
   current facts through tools rather than passive memory.
3. LABEL YOUR CONFIDENCE on factual claims:
   - VERIFIED: Confirmed by tool output (file read, web search result, command output)
   - INFERRED: Logical deduction from verified facts (label as "Based on X, I conclude Y")
   - UNCERTAIN: Your best guess — explicitly say "I'm not certain, but..."
   - UNKNOWN: You don't know. Say "I don't know" honestly. This is ALWAYS better than fabricating.
4. NEVER FABRICATE: No fake URLs. No fake quotes. No fake statistics. No fake dates. No fake
   citations. No fake government/military sources. No fake news reports. If you cannot verify
   a claim with your tools, say "I don't have verified information on this" and offer to search.
5. CONSIDER ALTERNATIVES: Before concluding, ask yourself "Is there another explanation?"
   Don't anchor on the first plausible answer. Consider at least 2 interpretations for ambiguous questions.
6. SELF-CORRECT: If you notice an error in your own reasoning, STOP, acknowledge it, and fix it
   immediately. Never defend a wrong answer to save face. Changing your mind with evidence is strength.
7. SEPARATE EVIDENCE FROM INTERPRETATION: When presenting findings, clearly distinguish between
   what the data/tools say (evidence) vs. what you conclude from it (interpretation).
8. FEASIBILITY CHECK: Before proposing any solution, verify the constraints can actually be satisfied.
   Reject impossible premises explicitly instead of fabricating a construction that looks plausible.
9. INTELLECTUAL HONESTY: Treat every factual claim as something that needs backing. If asked about
   a topic you're uncertain about, lead with your uncertainty. "I believe X, but I should verify"
   is better than confidently stating X and being wrong.
10. USE YOUR TOOLS FOR FACTS: You have web_search, web_fetch, and 100+ other tools. When making
    factual claims about the real world, USE THEM. Tool-verified answers > training-data guesses.

CRITICAL RULES:
1. Only use ask_user when you genuinely cannot proceed — prefer reading files, code, and context to infer answers.
2. Use "." or "{cwd}" for the current directory. Use relative paths.
3. Read files before editing. Verify changes after making them.
4. Be concise in final responses. Summarize what you did and what changed.
5. STOP when you have answered the question or completed the task. Do NOT keep calling tools.
6. If a tool returns an error, empty, "(no output)", or "[exit code: N]" with N≠0, DO NOT call it again. Move on or STOP.
7. If run_command returns "(no output)", it succeeded silently. Do NOT re-run it.
8. NEVER run the same tool more than twice in a row. If it didn't work twice, STOP and explain.
9. NEVER run "claw" or any command that spawns this agent recursively.
10. Complete the task thoroughly. Use as many tool calls as needed — you have a generous budget.
11. NEVER fabricate URLs, file paths, or content. Only use real data from tool results.
12. NEVER re-explore something you already explored. If you listed a directory, don't list it again.
13. When asked "is everything working" or "check all features", run tests ONCE, report results, STOP.
14. On Windows: the shell is cmd.exe. Use cmd commands: `dir`, `type`, `findstr`, `for`. NEVER use `wc`, `head`, `tail`, `cat`, `grep`, `awk`, `sed` (Unix-only). NEVER use PowerShell cmdlets like `Get-ChildItem`, `Select-String`, `Measure-Object` — they will fail. To count files use `dir /s /b *.py | find /c /v ""`. To search text use `findstr /s /i "pattern" *.py`.
15. For multi-file changes, edit each file in sequence. Verify the final state.
16. When debugging: read error messages carefully, grep for the error, find the root cause.
17. When refactoring: understand all callers before changing a function signature.
18. If you see 'SYSTEM: STOP' in a tool result, respond with text only — no more tools.

RESPONSE FORMATTING — always structure your output clearly:
- Use **markdown** for all responses: headers (## / ###), bold (**key terms**), code blocks (```lang), lists.
- Use fenced code blocks with language tags for ALL code: ```python, ```javascript, ```bash, etc.
- Use bullet lists (-) for multiple items. Use numbered lists (1. 2. 3.) for ordered steps.
- Use ### headers to separate major sections in long answers.
- Use inline `code` for file names, function names, variable names, commands.
- Use > blockquotes for important warnings or notes.
- Keep paragraphs short (2-4 sentences max). Use blank lines between sections.
- For explanations: lead with the answer, then explain why. Never bury the answer.
- NEVER output raw unformatted text walls. NEVER mix broken markdown fragments.
- When showing file changes: show the relevant diff or code block, not a verbal description.
"""

MAX_ITERATIONS = 200
# Support local Ollama, DeepSeek Cloud API, NVIDIA NIM (direct + Council), and Codex mode
AUTH_MODE = os.environ.get("AUTH_MODE", "free").strip().lower()  # free | chatgpt
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
NVIDIA_API_KEY = (
    os.environ.get("NVIDIA_API_KEY", "")
    or os.environ.get("NIM_API_KEY", "")
    or os.environ.get("OPENROUTER_API_KEY", "")
)
NVIDIA_API_BASE = "https://integrate.api.nvidia.com"
OPENROUTER_API_KEY = NVIDIA_API_KEY
OPENROUTER_API_BASE = NVIDIA_API_BASE
OLLAMA_BASE = "http://localhost:11434"

_NVIDIA_MODEL_ERROR_HINTS = (
    "no endpoints found",
    "model not found",
    "unknown model",
    "provider returned error",
    "route not found",
)


def _get_nvidia_direct_models() -> list[str]:
    """Return preferred direct-mode NVIDIA NIM models, newest first."""
    env_default = (
        os.environ.get("NVIDIA_DEFAULT_MODEL", "").strip()
        or os.environ.get("NIM_DEFAULT_MODEL", "").strip()
        or os.environ.get("OPENROUTER_DEFAULT_MODEL", "").strip()
    )
    models = []
    if env_default:
        models.append(env_default)
    models.extend(OPENROUTER_MODELS)
    return list(dict.fromkeys(model for model in models if model))


_get_openrouter_direct_models = _get_nvidia_direct_models


def _format_http_error(response: httpx.Response) -> str:
    """Return a concise API error string with provider details when available."""
    detail = ""
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            data = response.json()
            if isinstance(data, dict):
                error = data.get("error")
                if isinstance(error, dict):
                    detail = str(error.get("message") or error.get("code") or "")
                elif error:
                    detail = str(error)
                if not detail and data.get("message"):
                    detail = str(data.get("message"))
        except Exception:
            # JSON parsing failed - will fall back to text extraction
            detail = ""
    if not detail:
        try:
            detail = response.text.strip()
        except Exception:
            # Text extraction failed
            detail = ""
    detail = detail[:200]
    if detail:
        return f"HTTP {response.status_code}: {detail}"
    return f"HTTP {response.status_code}: {response.reason_phrase}"


def _should_retry_nvidia_model_error(response: httpx.Response) -> bool:
    """Return True when an NVIDIA request should try the next model."""
    if response.status_code in {429, 402}:
        return True
    if response.status_code not in {400, 404}:
        return False
    details = _format_http_error(response).lower()
    return response.status_code == 404 or any(hint in details for hint in _NVIDIA_MODEL_ERROR_HINTS)


_should_retry_openrouter_model_error = _should_retry_nvidia_model_error


def get_runtime_provider_mode() -> str:
    """Return the active runtime provider mode.

    Priority:
    0. Codex (role-based deliberation) when AUTH_MODE=chatgpt or NVIDIA council enabled
    1. NVIDIA council when available and not disabled
    2. NVIDIA direct when explicitly preferred or council is disabled
    3. DeepSeek direct
    4. NVIDIA direct fallback
    5. Local Ollama
    """
    # Codex mode: role-based deliberation pipeline
    if AUTH_MODE == "chatgpt":
        return "codex"

    council_disabled = bool(os.environ.get("DISABLE_COUNCIL", ""))
    prefer_nvidia = bool(
        os.environ.get("PREFER_NVIDIA", "")
        or os.environ.get("NVIDIA_DIRECT", "")
        or os.environ.get("PREFER_OPENROUTER", "")
        or os.environ.get("OPENROUTER_DIRECT", "")
    )

    # Use codex mode as the new default for council
    if NVIDIA_API_KEY and not council_disabled:
        return "codex"
    if NVIDIA_API_KEY and (prefer_nvidia or council_disabled):
        return "nvidia"
    if DEEPSEEK_API_KEY:
        return "deepseek"
    if NVIDIA_API_KEY:
        return "nvidia"
    return "ollama"


RUNTIME_PROVIDER_MODE = get_runtime_provider_mode()
USE_COUNCIL = RUNTIME_PROVIDER_MODE in ("council", "codex")
USE_CODEX = RUNTIME_PROVIDER_MODE == "codex"

if RUNTIME_PROVIDER_MODE == "codex":
    # Codex mode uses role-based models; pick synthesizer model as default label
    from .codex_runtime import FREE_ROLE_MODELS, _detect_provider
    _codex_provider = _detect_provider()
    DEFAULT_BASE_URL = NVIDIA_API_BASE if _codex_provider == "nvidia" else "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    DEFAULT_MODEL = FREE_ROLE_MODELS.get(_codex_provider, {}).get("synthesizer", ["codex-council"])[0]
    _CLOUD_API_KEY = NVIDIA_API_KEY or os.environ.get("DASHSCOPE_API_KEY", "")
elif RUNTIME_PROVIDER_MODE == "deepseek":
    DEFAULT_BASE_URL = DEEPSEEK_API_BASE
    DEFAULT_MODEL = "deepseek-reasoner"
    _CLOUD_API_KEY = DEEPSEEK_API_KEY
elif RUNTIME_PROVIDER_MODE in {"nvidia", "council"}:
    DEFAULT_BASE_URL = NVIDIA_API_BASE
    DEFAULT_MODEL = _get_nvidia_direct_models()[0]
    _CLOUD_API_KEY = NVIDIA_API_KEY
else:
    DEFAULT_BASE_URL = OLLAMA_BASE
    DEFAULT_MODEL = "deepseek-v3.1:671b-cloud"
    _CLOUD_API_KEY = ""

# When total token count exceeds this, auto-compact the conversation
MAX_CONTEXT_TOKENS = 200_000
# Start compacting at 50% of the hard context ceiling to avoid overflow.
AUTO_COMPACT_THRESHOLD = MAX_CONTEXT_TOKENS // 2
# Keep the system message + last N messages after compaction
COMPACT_KEEP_RECENT = 8

# Project config files loaded into system prompt (searched in cwd, then parents)
# Core identity + reasoning + style are loaded every time
# Reference docs (TOOLS.md, WORKFLOW.md, PROMPTS.md, SKILLS.md) are kept as
# files the agent can read on demand — loading them all would bloat the prompt.
CONFIG_FILES = (
    "MEMORY.md",       # project memory & conventions
    "SOUL.md",         # personality & response principles
    "CLAW.md",         # master config: architecture, rules, decision framework
    "REASONING.md",    # thinking framework & reasoning patches
    "STYLEGUIDE.md",   # response quality & formatting standards
    ".claw",           # JSON runtime settings (parsed separately by _load_claw_config)
)


def _load_project_context() -> str:
    """Load MEMORY.md, SOUL.md, and .claw from the workspace into the system prompt."""
    parts = []
    cwd = os.getcwd()
    for filename in CONFIG_FILES:
        # Search cwd, then up to 3 parent dirs
        search = cwd
        for _ in range(4):
            path = os.path.join(search, filename)
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read(4000)  # cap at 4K per file
                    parts.append(f"\n--- {filename} ---\n{content.strip()}")
                except OSError:
                    pass
                break
            parent = os.path.dirname(search)
            if parent == search:
                break
            search = parent
    return "\n".join(parts)


def _load_claw_config() -> dict:
    """Load and parse .claw JSON config. Returns settings dict (empty if no config)."""
    cwd = os.getcwd()
    search = cwd
    for _ in range(4):
        path = os.path.join(search, ".claw")
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.loads(f.read())
                if isinstance(data, dict):
                    return data
            except (json.JSONDecodeError, OSError):
                pass
            break
        parent = os.path.dirname(search)
        if parent == search:
            break
        search = parent
    return {}

# Commands that must never be executed (anti-recursion + safety)
BLOCKED_COMMANDS = (
    "claw",
    "claw ",
    "python -m claw_agent",
    "python claw_agent",
    "python bridge.py",
    "python src/bridge.py",
)

_COUNCIL_BYPASS_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bwhat(?:'s| is)?\s+(?:the\s+)?(?:date|time|day)\b",
        r"\bcurrent\b",
        r"\btoday'?s?\b",
        r"\blatest\b",
        r"\brecent\b",
        r"\b(news|headline|market|stock|price|weather|score)\b",
        r"\b(search\s+web|web\s+search|look\s+up|lookup|find\s+online|get\s+info\s+about)\b",
    )
]

_GROUNDED_WEB_RESEARCH_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\ball\s+info\s+about\b",
        r"\b(find|search|research|summari[sz]e|explain|tell\s+me\s+about|what(?:'s| is)\s+happening)\b.*\b(news|war|conflict|attack|sanction|election|strike|missile|ceasefire|president|prime\s+minister|ceo|market|price|stock|economy|shipping|oil|weather)\b",
        r"\b(us|u\.s\.|america|iran|israel|russia|ukraine|china|taiwan|gaza|hamas|hezbollah|trump|biden)\b.*\b(war|conflict|attack|strike|sanction|talks|ceasefire|missile|drone|blockade)\b",
        r"\b(latest|breaking|recent|today'?s?)\b.*\b(news|war|conflict|events?|developments?)\b",
        r"(?=.*\b(real[\s-]?time|right now|as of|current|latest|today'?s?)\b)(?=.*\b(news|events?|developments?|price|prices|stock|weather|score|release|launch|announcement|ceo|president|prime\s+minister)\b)",
    )
]

_WEB_CAPABILITY_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(can|do)\s+you\s+(browse|search|access|use)\b.*\b(web|internet|online)\b",
        r"\b(do\s+you\s+have|have\s+you\s+got)\b.*\b(web|internet|online|live|real[\s-]?time)\b.*\b(access|search|browsing)\b",
        r"\b(can|do)\s+you\s+answer\b.*\b(real[\s-]?time|current|latest|live)\b.*\b(question|questions|info(?:rmation)?)\b",
        r"\b(can|do)\s+you\s+get\b.*\b(latest|current|real[\s-]?time|live)\b.*\b(info(?:rmation)?|answers?|data)\b",
    )
]

_CODE_QUERY_HINTS = (
    "repo",
    "repository",
    "code",
    "function",
    "class",
    "method",
    "module",
    "file",
    "folder",
    "stack trace",
    "traceback",
    "bug",
    "test",
    "pytest",
    "compile",
    "build",
    "python",
    "javascript",
    "typescript",
    "react",
    "api",
    "endpoint",
    "sql",
    "json",
)

_SIMPLE_DATETIME_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"^\s*what(?:'s| is)?\s+(?:the\s+)?time(?:\s+now)?\s*\??\s*$",
        r"^\s*what\s+time\s+is\s+it(?:\s+now)?\s*\??\s*$",
        r"^\s*what(?:'s| is)?\s+it(?:\s+right)?\s+now\s*\??\s*$",
        r"^\s*what(?:'s| is)?\s+(?:the\s+)?date(?:\s+today|\s+now)?\s*\??\s*$",
        r"^\s*what(?:'s| is)?\s+(?:the\s+)?date\s+and\s+time(?:\s+now)?\s*\??\s*$",
        r"^\s*what(?:'s| is)?\s+(?:the\s+)?day(?:\s+today|\s+of\s+the\s+week)?\s*\??\s*$",
        r"^\s*what\s+day\s+is\s+it(?:\s+today)?\s*\??\s*$",
    )
]


def _normalize_user_message(user_message: str) -> str:
    stripped = user_message.strip()
    if stripped.lower().startswith("/nocouncil"):
        return stripped[len("/nocouncil"):].strip()
    return user_message


def _looks_like_code_query(user_message: str) -> bool:
    lowered = user_message.lower()
    return any(re.search(rf"\b{re.escape(hint)}\b", lowered) for hint in _CODE_QUERY_HINTS)


def _needs_grounded_web_research(user_message: str) -> bool:
    cleaned = _normalize_user_message(user_message).strip()
    if not cleaned or _looks_like_code_query(cleaned):
        return False
    return any(pattern.search(cleaned) for pattern in _GROUNDED_WEB_RESEARCH_PATTERNS)


def _build_grounding_system_message(user_message: str) -> str | None:
    cleaned = _normalize_user_message(user_message).strip()
    if not _needs_grounded_web_research(cleaned):
        return None

    return (
        "GROUNDING REQUIRED FOR THIS REQUEST.\n"
        "Treat this as a real-world, time-sensitive research task.\n"
        "You MUST follow this workflow before answering:\n"
        "1. Call web_search first to find recent sources.\n"
        "2. Call web_fetch on the most relevant 2 to 5 sources before making factual claims.\n"
        "3. Prefer official sources and major wire services or reputable outlets.\n"
        "4. Do not present search-result snippets as verified facts.\n"
        "5. If sources disagree or remain unclear, say so explicitly.\n"
        "6. Write the final answer in this structure: Summary, What is verified, What is uncertain, Sources.\n"
        "7. In Sources, use bullet points with source name and URL.\n\n"
        f"USER REQUEST:\n{cleaned}"
    )


def _prepare_user_message(user_message: str) -> str:
    cleaned = _normalize_user_message(user_message).strip()
    return cleaned or user_message


def _get_builtin_datetime_reply(user_message: str) -> str | None:
    """Answer simple local clock/date questions without hitting any provider."""
    cleaned = _normalize_user_message(user_message).strip()
    if not cleaned or not any(pattern.match(cleaned) for pattern in _SIMPLE_DATETIME_PATTERNS):
        return None

    local_now = datetime.now()
    utc_now = datetime.now(timezone.utc)
    lowered = cleaned.lower()

    if "date and time" in lowered:
        return (
            f"Local date and time: {local_now.strftime('%A, %d %B %Y %H:%M:%S')}\n"
            f"UTC: {utc_now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
    if "time" in lowered:
        return (
            f"Local time: {local_now.strftime('%H:%M:%S')}\n"
            f"Local date: {local_now.strftime('%A, %d %B %Y')}\n"
            f"UTC: {utc_now.strftime('%H:%M:%S')} UTC"
        )
    if "day" in lowered:
        return (
            f"Today is {local_now.strftime('%A')}.\n"
            f"Local date: {local_now.strftime('%d %B %Y')}"
        )
    return (
        f"Today's date: {local_now.strftime('%A, %d %B %Y')}\n"
        f"Local time: {local_now.strftime('%H:%M:%S')}\n"
        f"UTC: {utc_now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )


def _get_builtin_web_capability_reply(user_message: str) -> str | None:
    """Answer direct questions about whether Claw can browse/search the live web."""
    cleaned = _normalize_user_message(user_message).strip()
    if not cleaned or not any(pattern.search(cleaned) for pattern in _WEB_CAPABILITY_PATTERNS):
        return None

    return (
        "Yes — in this Claw runtime I can use live web tools.\n\n"
        "- `web_search` can search the live web.\n"
        "- `web_fetch` can open specific pages so I can verify details.\n"
        "- For current or time-sensitive questions, I should search first and answer from those sources.\n"
        "- If a live lookup fails because of a network issue, I should say the lookup failed rather than claim I am permanently offline.\n\n"
        "I do not passively know real-time facts from memory alone; I answer current questions by using those tools."
    )


def _get_builtin_reply(user_message: str) -> str | None:
    """Handle deterministic local replies without calling any provider."""
    return _get_builtin_datetime_reply(user_message) or _get_builtin_web_capability_reply(user_message)


def _should_bypass_council(user_message: str) -> bool:
    """Return True when the prompt needs live tools instead of raw council voting."""
    cleaned = _normalize_user_message(user_message)
    lowered = cleaned.strip().lower()
    if not lowered:
        return False
    if user_message.strip().lower().startswith("/nocouncil"):
        return True
    if _needs_grounded_web_research(cleaned):
        return True
    if _looks_like_code_query(cleaned):
        return False
    return any(pattern.search(cleaned) for pattern in _COUNCIL_BYPASS_PATTERNS)

def _is_repetitive(text: str, min_chunk: int = 40, min_repeats: int = 3) -> bool:
    """Detect if streamed text ends with a repeating pattern (model stuck in loop)."""
    if len(text) < min_chunk * min_repeats:
        return False
    # Check if the last min_chunk chars appear min_repeats+ times in the tail
    tail = text[-(min_chunk * (min_repeats + 1)):]
    pattern = text[-min_chunk:]
    return tail.count(pattern) >= min_repeats


_TOOL_CALL_RE = re.compile(
    r'(?:```(?:json)?\s*)?'
    r'\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"arguments"\s*:\s*(\{[^}]*\})\s*\}'
    r'(?:\s*```)?',
    re.DOTALL,
)

# --- Event types for streaming ---
class StreamEvent:
    """Base event emitted during streaming."""
    pass

class TextDelta(StreamEvent):
    def __init__(self, text: str):
        self.text = text

class ToolCallStart(StreamEvent):
    def __init__(self, name: str, arguments: dict):
        self.name = name
        self.arguments = arguments

class ToolCallEnd(StreamEvent):
    def __init__(self, name: str, result: str, duration_ms: float):
        self.name = name
        self.result = result
        self.duration_ms = duration_ms

class TurnComplete(StreamEvent):
    def __init__(self, content: str, prompt_tokens: int, completion_tokens: int):
        self.content = content
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens

class AgentDone(StreamEvent):
    def __init__(self, final_text: str):
        self.final_text = final_text


class Agent:
    """Autonomous agent with streaming support."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        permissions: PermissionContext | None = None,
        session: Session | None = None,
        on_tool_call: Callable[[str, dict], None] | None = None,
        on_tool_result: Callable[[str, str], None] | None = None,
        confirm_fn: Callable[[], bool] | None = None,
        ask_fn: Callable[[str, list], str] | None = None,
    ):
        # Auto-detect: Use DeepSeek API if key is set, otherwise Ollama
        self.model = model or DEFAULT_MODEL
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        # Cloud mode if any API key is set AND we're not explicitly pointed at Ollama,
        # OR if the base_url is a known cloud endpoint
        _is_ollama_url = self.base_url.startswith("http://localhost") or self.base_url.startswith("http://127.0.0.1")
        self.is_cloud = bool(_CLOUD_API_KEY) and not _is_ollama_url
        self.client = httpx.Client(timeout=300)
        self.permissions = permissions or PermissionContext.default()
        self.session = session or Session(model=self.model)
        self.cost = CostTracker()
        self._confirm_fn = confirm_fn
        self._ask_fn = ask_fn
        self._plan_mode: bool = False
        self._hooks = HookRunner.load()  # Cache hooks once at init (M1)

        # Register ask_fn so the ask_user tool can call back into the CLI
        if ask_fn is not None:
            from .tools.utility_tools import register_ask_user_fn
            register_ask_user_fn(ask_fn)

        # Register self with agent_tools so enter/exit_plan_mode can toggle flag
        import claw_agent.tools.agent_tools as _at
        _at._PLAN_MODE_CALLBACK = self

        # Determine mode label for system prompt
        if self.is_cloud:
            _provider = "OpenRouter" if "openrouter" in self.base_url else "DeepSeek"
            self._mode_label = f"via {_provider} Cloud API"
        else:
            self._mode_label = "via local Ollama"

        # H4: Load and apply .claw project config
        claw_config = _load_claw_config()
        if claw_config:
            if "model" in claw_config and model == "deepseek-v3.1:671b-cloud":
                # Only override if user didn't explicitly pick a model
                self.model = claw_config["model"]
            if "auto_approve" in claw_config:
                self.permissions.auto_approve = bool(claw_config["auto_approve"])
            if "max_iterations" in claw_config:
                # Store per-instance override
                self._max_iterations = min(int(claw_config["max_iterations"]), 200)
            else:
                self._max_iterations = MAX_ITERATIONS
            if "blocked_commands" in claw_config:
                # Extend blocked tools from config
                extra_denies = frozenset(
                    t.strip() for t in claw_config.get("blocked_tools", [])
                )
                if extra_denies:
                    self.permissions.deny_names = self.permissions.deny_names | extra_denies
        else:
            self._max_iterations = MAX_ITERATIONS

        self._compacted = False
        # Build system prompt from template + project files (MEMORY.md, SOUL.md, .claw)
        project_ctx = _load_project_context()
        system_content = SYSTEM_PROMPT_TEMPLATE.format(
            cwd=os.getcwd(),
            model=self.model,
            platform=sys.platform,
            mode_label=self._mode_label,
            tools_section=_build_tools_section(),
            current_datetime=_get_live_datetime(),
        )
        if project_ctx:
            system_content += "\n\nPROJECT CONTEXT (loaded from workspace files):" + project_ctx
        
        # Add skills context (built-in + custom installed)
        from .skills import get_all_skills_context
        skills_ctx = get_all_skills_context()
        if skills_ctx:
            system_content += "\n\nSKILLS & CAPABILITIES:" + skills_ctx

        # Add skill library awareness (315+ skills, dynamically detected per-turn)
        try:
            from .skill_library import get_skill_count, get_category_counts, ALL_CATEGORIES
            count = get_skill_count()
            cats = get_category_counts()
            system_content += f"\n\nSKILL LIBRARY ({count} skills across {len(cats)} categories):"
            system_content += "\nYou have deep expertise loaded on-demand via keyword detection."
            system_content += "\nCategories: " + ", ".join(
                f"{c} ({cats.get(c, 0)})" for c in ALL_CATEGORIES if cats.get(c, 0) > 0
            )
            system_content += "\nRelevant skills are automatically injected when the user's message matches skill triggers."
        except Exception:
            pass
        
        # Add reasoning wisdom patches (deep logic, anti-hallucination, self-audit)
        from .ai_lab.arena import get_enhanced_system_prompt_addition
        system_content += get_enhanced_system_prompt_addition()
        
        # SEAKS: Load self-evolving kernel and inject live rules into system prompt
        try:
            from .ai_lab.seaks import SEAKS
            self._seaks = SEAKS()
            seaks_patch = self._seaks.get_system_prompt_patch()
            if seaks_patch:
                system_content += "\n" + seaks_patch
        except Exception:
            self._seaks = None
        
        # Initialize MCP tool manager — discover tools from configured servers
        self._mcp = MCPManager()
        try:
            self._mcp.discover()
        except Exception:
            self._mcp.load_from_cache()

        # Build combined tool definitions (built-in + MCP)
        mcp_defs = self._mcp.get_tool_definitions()
        self._all_tool_definitions = OLLAMA_TOOL_DEFINITIONS + mcp_defs

        # Add MCP context (with actual tool names if discovered)
        mcp_ctx = self._mcp.get_context() if self._mcp.get_tool_names() else ""
        if not mcp_ctx:
            from .mcp import get_mcp_context
            mcp_ctx = get_mcp_context()
        if mcp_ctx:
            system_content += "\n\nMCP SERVERS:" + mcp_ctx
        
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_content},
        ]
        self._on_tool_call = on_tool_call
        self._on_tool_result = on_tool_result

        # Initialize council if enabled
        self.council = None
        self._codex_runtime: CodexRuntime | None = None
        if USE_CODEX:
            self._codex_runtime = CodexRuntime(workspace_root=os.getcwd())
        elif USE_COUNCIL:
            from .ll_council import LLCouncil
            self.council = LLCouncil(
                system_prompt=system_content,
            )

    # ---- public: blocking --------------------------------------------------

    def chat(self, user_message: str) -> str:
        """Blocking chat - collects all streaming events, returns final text."""
        builtin_reply = _get_builtin_reply(user_message)
        if builtin_reply is not None:
            prepared_user_message = _prepare_user_message(user_message)
            self.messages.append({"role": "user", "content": prepared_user_message})
            self.session.total_turns += 1
            self.messages.append({"role": "assistant", "content": builtin_reply})
            self._sync_session_state()
            return builtin_reply

        # Use codex runtime for role-based deliberation
        if self._codex_runtime and self._codex_runtime.should_use_council(user_message):
            result = self._codex_runtime.run_task(user_message)
            return result.final_answer

        # Use council if enabled
        if self.council and not _should_bypass_council(user_message):
            result = self.council.query_council(_normalize_user_message(user_message))
            return result.consensus_answer
        
        # Fallback to single model
        final = ""
        for event in self.stream_chat(user_message):
            if isinstance(event, AgentDone):
                final = event.final_text
        return final

    def council_chat(self, user_message: str) -> str:
        """Explicit council chat - always uses council even if disabled."""
        if not self.council:
            from .ll_council import LLCouncil, DEFAULT_COUNCIL_MODELS
            self.council = LLCouncil(
                system_prompt=self.messages[0]["content"],
            )
        
        result = self.council.query_council(_normalize_user_message(user_message))
        return result.consensus_answer

    # ---- public: streaming -------------------------------------------------

    def stream_chat(self, user_message: str) -> Generator[StreamEvent, None, None]:
        """Stream events as the agent thinks, calls tools, and responds."""
        prepared_user_message = _prepare_user_message(user_message)
        grounding_message = _build_grounding_system_message(user_message)
        self.messages.append({"role": "user", "content": prepared_user_message})
        self.session.total_turns += 1

        try:
            builtin_reply = _get_builtin_reply(user_message)
            if builtin_reply is not None:
                self.messages.append({"role": "assistant", "content": builtin_reply})
                yield TextDelta(builtin_reply)
                yield TurnComplete(builtin_reply, 0, 0)
                yield AgentDone(builtin_reply)
                return

            # Codex runtime path: role-based deliberation pipeline
            if self._codex_runtime and self._codex_runtime.should_use_council(user_message):
                try:
                    codex_result = self._codex_runtime.run_task(prepared_user_message)
                    final_text = codex_result.final_answer
                    self.messages.append({"role": "assistant", "content": final_text})
                    yield TextDelta(final_text)
                    yield TurnComplete(final_text, 0, 0)
                    yield AgentDone(final_text)
                except Exception as e:
                    self.messages.append({
                        "role": "system",
                        "content": f"Codex runtime unavailable ({e}). Falling back to single-model execution.",
                    })
                    yield TextDelta(f"\n[Codex fallback: {e}]\n")
                else:
                    return

            # Interactive council path: the REPL uses stream_chat(), so council mode
            # must be handled here as well, not only in blocking chat().
            if self.council and not _should_bypass_council(user_message):
                try:
                    result = self.council.query_council(prepared_user_message)
                    final_text = result.consensus_answer
                    self.messages.append({"role": "assistant", "content": final_text})
                    yield TextDelta(final_text)
                    yield TurnComplete(final_text, 0, 0)
                    yield AgentDone(final_text)
                except Exception as e:
                    self.messages.append({
                        "role": "system",
                        "content": f"Council unavailable ({e}). Falling back to single-model execution.",
                    })
                    yield TextDelta(f"\n[Council fallback: {e}]\n")
                else:
                    return

            if grounding_message:
                self.messages.append({"role": "system", "content": grounding_message})

            # Dynamic skill detection: inject relevant skill context per-turn
            try:
                from .skill_detector import get_detected_skills_context
                skill_ctx = get_detected_skills_context(prepared_user_message)
                if skill_ctx:
                    self.messages.append({"role": "system", "content": skill_ctx})
            except Exception:
                pass  # Graceful degradation if detector fails
            yield from self._stream_loop()
        finally:
            self._sync_session_state()

    # ---- internal ----------------------------------------------------------

    def _sync_session_state(self) -> None:
        """Persist the resumable conversation snapshot into the active session."""
        self.session.model = self.model
        self.session.messages = [
            m for m in self.messages[1:]
            if not (
                m.get("role") == "system"
                and "CONVERSATION COMPACTED" not in m.get("content", "")
            )
        ]
        self.session.input_tokens = self.cost.total_prompt_tokens
        self.session.output_tokens = self.cost.total_completion_tokens

    def _request_model_candidates(self) -> list[str]:
        """Return model candidates for the current request, including retries."""
        candidates = [self.model]
        if self.is_cloud and "openrouter" in self.base_url:
            candidates.extend(
                model for model in _get_openrouter_direct_models()
                if model != self.model
            )
        return list(dict.fromkeys(candidate for candidate in candidates if candidate))

    def _set_active_model(self, model: str) -> None:
        """Persist a provider-selected model switch into the live session."""
        if not model or model == self.model:
            return
        self.model = model
        self.session.model = model

    def _compact_if_needed(self):
        """Auto-compact when the live session is approaching the context ceiling."""
        total_chars = sum(len(str(m.get("content", ""))) for m in self.messages)
        if _enc:
            est_tokens = sum(len(_enc.encode(str(m.get("content", "")))) for m in self.messages)
        else:
            est_tokens = total_chars // 4
        recorded_tokens = self.cost.turns[-1].total_tokens if self.cost.turns else 0
        compact_pressure = max(est_tokens, recorded_tokens)
        if compact_pressure < AUTO_COMPACT_THRESHOLD:
            return
        if len(self.messages) <= COMPACT_KEEP_RECENT + 1:
            return
        system = self.messages[0]
        old = self.messages[1:-COMPACT_KEEP_RECENT]
        recent = self.messages[-COMPACT_KEEP_RECENT:]

        # Try LLM-based summarization first, fall back to naive truncation
        summary = self._llm_summarize(old)
        if not summary:
            summary = self._truncation_summary(old)

        self.messages = [system, {"role": "system", "content": summary}] + recent
        self.cost.turns.clear()
        self._compacted = True

    def _llm_summarize(self, old_messages: list[dict]) -> str | None:
        """Ask the LLM to produce a concise summary of discarded messages."""
        # Build a digest of old messages (capped to avoid huge payloads)
        digest_parts = []
        char_budget = 12000
        used = 0
        for m in old_messages:
            role = m.get("role", "?")
            content = str(m.get("content", ""))[:600]
            tc = m.get("tool_calls")
            if tc:
                names = [t.get("function", {}).get("name", "?") for t in tc]
                line = f"{role}: [called {', '.join(names)}]"
            elif content:
                line = f"{role}: {content}"
            else:
                continue
            if used + len(line) > char_budget:
                break
            digest_parts.append(line)
            used += len(line)

        if not digest_parts:
            return None

        digest = "\n".join(digest_parts)
        prompt = (
            "Summarize this conversation history concisely. "
            "Preserve: key decisions, file paths modified, tool results, "
            "user requirements, and any unfinished tasks. "
            "Use bullet points. Be factual and brief.\n\n"
            f"{digest}"
        )
        try:
            headers = {"Content-Type": "application/json"}
            if self.is_cloud:
                headers["Authorization"] = f"Bearer {os.environ.get('OPENROUTER_API_KEY') or os.environ.get('DEEPSEEK_API_KEY', '')}"
            resp = self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1024,
                    "temperature": 0.2,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if text and len(text) > 20:
                return f"CONVERSATION COMPACTED - LLM summary of earlier context:\n{text.strip()}"
        except Exception:
            pass
        return None

    @staticmethod
    def _truncation_summary(old_messages: list[dict]) -> str:
        """Fallback: build a summary by truncating old messages."""
        summary_parts = []
        for m in old_messages:
            role = m.get("role", "?")
            content = m.get("content", "")
            if role == "tool":
                summary_parts.append(f"[tool result: {content[:100]}]")
            elif role == "assistant":
                tc = m.get("tool_calls")
                if tc:
                    names = [t.get("function", {}).get("name", "?") for t in tc]
                    summary_parts.append(f"[called tools: {', '.join(names)}]")
                if content:
                    summary_parts.append(f"[assistant: {content[:150]}]")
            elif role == "user":
                summary_parts.append(f"[user: {content[:150]}]")
        return "CONVERSATION COMPACTED - earlier context summary:\n" + "\n".join(summary_parts)

    def _stream_loop(self) -> Generator[StreamEvent, None, None]:
        # ---- Loop protection (fresh per user message) ----
        total_errors = 0
        empty_results = 0  # tools returning no output / "(no output)"
        tool_call_counts: dict[str, int] = {}  # per-tool call counter
        total_tool_calls = 0  # absolute cap across entire turn
        consecutive_same_tool = 0
        last_tool_name = ""
        MAX_TOOLS_PER_ITERATION = 15  # cap tool calls per single LLM response
        MAX_TOTAL_TOOL_CALLS = 200    # absolute cap across all iterations

        for iteration in range(self._max_iterations):
            # Auto-compact to avoid context overflow
            self._compact_if_needed()

            start = time.time()

            # --- Streaming request to API ---
            request_models = self._request_model_candidates()
            selected_model = self.model
            if self.is_cloud:
                # Cloud API (DeepSeek or OpenRouter — both OpenAI-compatible)
                payload = {
                    "model": selected_model,
                    "messages": self.messages,
                    "tools": self._all_tool_definitions,
                    "stream": True,
                }
                api_url = f"{self.base_url}/chat/completions"
                extra_headers = {
                    "Authorization": f"Bearer {_CLOUD_API_KEY}",
                    "Content-Type": "application/json",
                }
            else:
                # Local Ollama
                payload = {
                    "model": selected_model,
                    "messages": self.messages,
                    "tools": self._all_tool_definitions,
                    "stream": True,
                }
                api_url = f"{self.base_url}/api/chat"
                extra_headers = None

            collected_content = ""
            tool_calls: list[dict] = []
            prompt_tokens = 0
            completion_tokens = 0
            last_api_error: httpx.HTTPStatusError | None = None

            for selected_model in request_models:
                payload["model"] = selected_model
                collected_content = ""
                tool_calls = []
                prompt_tokens = 0
                completion_tokens = 0
                try:
                    with self.client.stream(
                        "POST", api_url, json=payload, headers=extra_headers, timeout=300
                    ) as response:
                        response.raise_for_status()
                        for line in response.iter_lines():
                            if not line:
                                continue

                            # Handle SSE format (DeepSeek/OpenAI use "data: " prefix)
                            if self.is_cloud and line.startswith("data: "):
                                line = line[6:]  # Strip "data: " prefix

                            if line.strip() == "[DONE]":
                                break

                            try:
                                chunk = json.loads(line)
                            except json.JSONDecodeError:
                                continue

                            if self.is_cloud:
                                # OpenAI/DeepSeek streaming format
                                choices = chunk.get("choices", [])
                                if not choices:
                                    continue
                                choice = choices[0]
                                delta = choice.get("delta", {})
                                content = delta.get("content", "")
                                tool_calls_delta = delta.get("tool_calls", [])
                                finish_reason = choice.get("finish_reason", "")

                                if content:
                                    collected_content += content
                                    yield TextDelta(content)

                                if tool_calls_delta:
                                    for tc in tool_calls_delta:
                                        # Merge tool call chunks
                                        if tool_calls and tool_calls[-1].get("id") == tc.get("id"):
                                            # Append to existing tool call
                                            prev_fn = tool_calls[-1].get("function", {})
                                            curr_fn = tc.get("function", {})
                                            if curr_fn.get("arguments"):
                                                prev_fn["arguments"] = prev_fn.get("arguments", "") + curr_fn["arguments"]
                                            if curr_fn.get("name"):
                                                prev_fn["name"] = curr_fn["name"]
                                        else:
                                            tool_calls.append(tc)

                                # Final chunk has usage or finish_reason
                                if chunk.get("usage"):
                                    prompt_tokens = chunk["usage"].get("prompt_tokens", 0)
                                    completion_tokens = chunk["usage"].get("completion_tokens", 0)

                                if finish_reason == "stop":
                                    break
                            else:
                                # Ollama format
                                msg = chunk.get("message", {})

                                delta = msg.get("content", "")
                                if delta:
                                    collected_content += delta
                                    yield TextDelta(delta)

                                # Detect repetitive text (model stuck in generation loop)
                                if _is_repetitive(collected_content):
                                    collected_content = collected_content[:-(40 * 2)]
                                    break

                                if msg.get("tool_calls"):
                                    tool_calls.extend(msg["tool_calls"])

                                if chunk.get("done"):
                                    prompt_tokens = chunk.get("prompt_eval_count", 0)
                                    completion_tokens = chunk.get("eval_count", 0)
                    self._set_active_model(selected_model)
                    break
                except httpx.HTTPStatusError as e:
                    last_api_error = e
                    retryable = (
                        self.is_cloud
                        and "openrouter" in self.base_url
                        and not collected_content
                        and not tool_calls
                        and _should_retry_openrouter_model_error(e.response)
                    )
                    if retryable:
                        if e.response.status_code == 429:
                            time.sleep(3)
                        continue  # next model, or else-clause when last
                    error_text = f"[API Error: {_format_http_error(e.response)}]"
                    self.messages.append({"role": "assistant", "content": error_text})
                    yield TextDelta(f"\n\n{error_text}")
                    yield AgentDone(error_text)
                    return
                except (httpx.ConnectError, httpx.TimeoutException, httpx.ReadError) as e:
                    error_text = f"[Connection error: {e}]"
                    self.messages.append({"role": "assistant", "content": error_text})
                    yield TextDelta(f"\n\n{error_text}")
                    yield AgentDone(error_text)
                    return
            else:
                if last_api_error is not None:
                    # --- Alibaba DashScope fallback for rate-limited OpenRouter ---
                    _ds_key = os.environ.get("DASHSCOPE_API_KEY", "")
                    _is_rl = (
                        self.is_cloud
                        and "openrouter" in self.base_url
                        and last_api_error.response.status_code in (429, 402)
                    )
                    if _is_rl and _ds_key:
                        from .alibaba_cloud import DASHSCOPE_API_BASE
                        _ali_models = ["qwen-plus", "qwen3.5-397b-a17b"]
                        # Build lightweight messages: strip tool schemas
                        # from system prompt so model answers directly
                        _fb_msgs = []
                        for _m in self.messages:
                            if _m.get("role") == "system":
                                _fb_msgs.append({
                                    "role": "system",
                                    "content": (
                                        "You are a helpful assistant. "
                                        "IMPORTANT: You MUST respond "
                                        "entirely in English regardless "
                                        "of the language of any search "
                                        "results or source material. "
                                        "Never respond in Chinese or "
                                        "any other non-English language. "
                                        "Give short, direct answers. "
                                        "Never mention tools, functions, "
                                        "web_search, or training cutoffs. "
                                        "Never output code blocks unless "
                                        "the user asks for code."
                                    ),
                                })
                            elif _m.get("role") in ("user", "assistant"):
                                _fb_msgs.append(_m)
                            # skip tool / function roles entirely
                        # Reinforce English at end so model sees it last
                        if _fb_msgs and _fb_msgs[-1].get("role") == "user":
                            _orig = _fb_msgs[-1].get("content", "")
                            _fb_msgs[-1] = {
                                "role": "user",
                                "content": (
                                    f"{_orig}\n\n"
                                    "(Reply in English only.)"
                                ),
                            }
                        for _ali_m in _ali_models:
                            try:
                                _ali_resp = self.client.post(
                                    f"{DASHSCOPE_API_BASE}/chat/completions",
                                    headers={
                                        "Authorization": f"Bearer {_ds_key}",
                                        "Content-Type": "application/json",
                                    },
                                    json={
                                        "model": _ali_m,
                                        "messages": _fb_msgs,
                                        "stream": False,
                                        "max_tokens": 4096,
                                    },
                                    timeout=120,
                                )
                                if _ali_resp.status_code == 200:
                                    _ali_data = _ali_resp.json()
                                    _ali_content = (
                                        _ali_data.get("choices", [{}])[0]
                                        .get("message", {}).get("content", "")
                                    )
                                    if _ali_content:
                                        collected_content = _ali_content
                                        yield TextDelta(_ali_content)
                                        break
                            except Exception:
                                continue
                        else:
                            error_text = (
                                "[All models rate-limited. "
                                "Wait ~30s and retry, or set "
                                "COUNCIL_PROVIDER=alibaba.]"
                            )
                            self.messages.append(
                                {"role": "assistant", "content": error_text}
                            )
                            yield TextDelta(f"\n\n{error_text}")
                            yield AgentDone(error_text)
                            return
                    else:
                        error_text = f"[API Error: {_format_http_error(last_api_error.response)}]"
                        self.messages.append({"role": "assistant", "content": error_text})
                        yield TextDelta(f"\n\n{error_text}")
                        yield AgentDone(error_text)
                        return

            duration_ms = (time.time() - start) * 1000

            # Convert OpenAI-format tool calls to internal format for cloud mode
            if self.is_cloud and tool_calls:
                converted_calls = []
                for index, tc in enumerate(tool_calls, start=1):
                    fn = tc.get("function", {})
                    name = fn.get("name", "")
                    # FIX: Skip tool calls with empty/invalid names (prevents 400 errors)
                    if not name or not name.strip():
                        continue
                    if not name.replace("_", "").isalnum():
                        continue
                    args_str = fn.get("arguments", "{}")
                    if args_str is None:
                        args_str = "{}"
                    elif not isinstance(args_str, str):
                        try:
                            args_str = json.dumps(args_str)
                        except TypeError:
                            args_str = "{}"
                    converted_calls.append({
                        "id": tc.get("id") or f"call_{index}",
                        "type": tc.get("type") or "function",
                        "function": {
                            "name": name,
                            "arguments": args_str,
                        }
                    })
                tool_calls = converted_calls

            # --- Cap tool calls BEFORE building history ---
            if tool_calls:
                # Cap per-iteration (Ollama can batch 15+ in one response)
                if len(tool_calls) > MAX_TOOLS_PER_ITERATION:
                    tool_calls = tool_calls[:MAX_TOOLS_PER_ITERATION]
                # Absolute total cap across all iterations
                remaining = MAX_TOTAL_TOOL_CALLS - total_tool_calls
                if remaining <= 0:
                    # Build assistant msg without tool_calls so model knows to stop
                    self.messages.append({"role": "assistant", "content": collected_content or "(tool budget exhausted)"})
                    self.messages.append({"role": "system", "content": "SYSTEM: STOP — tool call budget exhausted. Summarize and respond now."})
                    yield TurnComplete(collected_content, prompt_tokens, completion_tokens)
                    yield AgentDone("[Stopped: tool call budget exhausted]")
                    return
                if len(tool_calls) > remaining:
                    tool_calls = tool_calls[:remaining]
                total_tool_calls += len(tool_calls)

            # Build the assistant message for history (with CAPPED tool_calls only)
            assistant_msg: dict[str, Any] = {"role": "assistant", "content": collected_content}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            self.messages.append(assistant_msg)

            yield TurnComplete(collected_content, prompt_tokens, completion_tokens)

            # --- Execute tool calls if any ---
            if tool_calls:

                # Plan mode: skip execution of all tools EXCEPT plan-mode controls and ask_user
                _PLAN_PASSTHROUGH = {"enter_plan_mode", "exit_plan_mode", "ask_user"}
                if self._plan_mode:
                    exec_calls = [tc for tc in tool_calls if tc.get("function", {}).get("name", "") in _PLAN_PASSTHROUGH]
                    skipped = [tc.get("function", {}).get("name", "") for tc in tool_calls if tc.get("function", {}).get("name", "") not in _PLAN_PASSTHROUGH]
                    if skipped:
                        skip_note = f"PLAN MODE: skipped execution of [{', '.join(skipped)}] — list your plan steps as text, then call exit_plan_mode when the user approves."
                        self.messages.append({"role": "system", "content": skip_note})
                    tool_calls = exec_calls
                    if not tool_calls:
                        yield AgentDone(collected_content or "[Plan mode — describe your plan as numbered steps]")
                        return

                # Track tool results for circuit breakers
                msgs_before = len(self.messages)
                yield from self._execute_tool_calls(tool_calls)
                self.cost.record_turn(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    tool_calls=len(tool_calls),
                    duration_ms=duration_ms,
                    model=self.model,
                )

                # --- Circuit breaker checks on tool results ---
                _EMPTY_PATTERNS = {'', 'None', 'null', '(no output)', 'no output'}
                new_msgs = self.messages[msgs_before:]
                for tm in new_msgs:
                    if tm.get("role") != "tool":
                        continue
                    content = tm.get("content", "")
                    stripped = content.strip()
                    # Only match ACTUAL tool failures, not content that happens to contain "error"
                    is_err = bool(
                        re.search(r'^(?:Error:|Permission denied:|Blocked:)', stripped, re.I | re.M)
                        or re.search(r'not recognized as an internal or external command', content, re.I)
                        or re.search(r'\[exit code:\s*(?:[2-9]|\d{2,})\]', content)
                        or re.search(r'^Traceback \(most recent call last\):', stripped, re.M)
                    )
                    is_empty = len(stripped) == 0 or stripped in _EMPTY_PATTERNS
                    if is_err:
                        total_errors += 1
                    if is_empty:
                        empty_results += 1

                # Track per-tool call counts + consecutive repetition
                tc_names = [tc.get("function", {}).get("name", "") for tc in tool_calls]
                for tn in tc_names:
                    tool_call_counts[tn] = tool_call_counts.get(tn, 0) + 1
                # Consecutive = same DOMINANT tool across iterations (not within batch)
                dominant = max(set(tc_names), key=tc_names.count) if tc_names else ""
                if dominant == last_tool_name:
                    consecutive_same_tool += 1
                else:
                    consecutive_same_tool = 0
                last_tool_name = dominant

                # --- Hard stops ---
                if total_errors >= 8:
                    self.messages.append({"role": "system", "content": "SYSTEM: STOP — too many tool errors. Respond with what you know."})
                    yield AgentDone("[Stopped: too many tool errors]")
                    return
                if empty_results >= 5:
                    self.messages.append({"role": "system", "content": "SYSTEM: STOP — tools returning empty/no output. Respond with what you know."})
                    yield AgentDone("[Stopped: repeated empty tool results]")
                    return
                if consecutive_same_tool >= 8:
                    self.messages.append({"role": "system", "content": f"SYSTEM: STOP — you called '{last_tool_name}' 9+ iterations in a row. Respond to the user now."})
                    yield AgentDone(f"[Stopped: '{last_tool_name}' called repeatedly]")
                    return
                # Per-tool budget: run_command max 30, others max 50
                for tn, count in tool_call_counts.items():
                    limit = 30 if tn == "run_command" else 50
                    if count >= limit:
                        self.messages.append({"role": "system", "content": f"SYSTEM: STOP — '{tn}' called {count} times this turn. Summarize and respond now."})
                        yield AgentDone(f"[Stopped: '{tn}' used {count} times]")
                        return

                continue

            # Fallback: parse tool calls from text
            parsed = self._parse_tool_calls_from_text(collected_content)
            if parsed:
                for name, args in parsed:
                    yield from self._run_single_tool(name, args)
                self.cost.record_turn(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    tool_calls=len(parsed),
                    duration_ms=duration_ms,
                    model=self.model,
                )
                continue

            # No tool calls — agent is done
            self.cost.record_turn(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                tool_calls=0,
                duration_ms=duration_ms,
                model=self.model,
            )
            yield AgentDone(collected_content or "[No response]")
            return

        # Iteration limit reached — give model one last chance to summarize WITHOUT tools
        self.messages.append({"role": "system", "content": "SYSTEM: Tool call limit reached. Summarize your findings and respond to the user now. Do NOT call any more tools."})
        try:
            start = time.time()
            payload = {
                "model": self.model,
                "messages": self.messages,
                "stream": True,
                # NO tools — force text-only response
            }
            collected_summary = ""
            prompt_tokens = completion_tokens = 0
            last_api_error: httpx.HTTPStatusError | None = None
            summary_models = self._request_model_candidates()
            api_url = f"{self.base_url}/api/chat"
            extra_headers = None
            if self.is_cloud:
                api_url = f"{self.base_url}/chat/completions"
                extra_headers = {
                    "Authorization": f"Bearer {_CLOUD_API_KEY}",
                    "Content-Type": "application/json",
                }
            for index, selected_model in enumerate(summary_models):
                payload["model"] = selected_model
                collected_summary = ""
                prompt_tokens = completion_tokens = 0
                try:
                    with self.client.stream(
                        "POST", api_url, json=payload, headers=extra_headers, timeout=120
                    ) as response:
                        response.raise_for_status()
                        for line in response.iter_lines():
                            if not line:
                                continue
                            if self.is_cloud:
                                if line.startswith("data: "):
                                    line = line[6:]
                                if line.strip() == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(line)
                                except json.JSONDecodeError:
                                    continue
                                choices = chunk.get("choices", [])
                                if not choices:
                                    continue
                                choice = choices[0]
                                delta = choice.get("delta", {}).get("content", "")
                                if delta:
                                    collected_summary += delta
                                    yield TextDelta(delta)
                                if _is_repetitive(collected_summary):
                                    break
                                if chunk.get("usage"):
                                    prompt_tokens = chunk["usage"].get("prompt_tokens", 0)
                                    completion_tokens = chunk["usage"].get("completion_tokens", 0)
                                if choice.get("finish_reason") == "stop":
                                    break
                            else:
                                try:
                                    chunk = json.loads(line)
                                except json.JSONDecodeError:
                                    continue
                                msg = chunk.get("message", {})
                                delta = msg.get("content", "")
                                if delta:
                                    collected_summary += delta
                                    yield TextDelta(delta)
                                if _is_repetitive(collected_summary):
                                    break
                                if chunk.get("done"):
                                    prompt_tokens = chunk.get("prompt_eval_count", 0)
                                    completion_tokens = chunk.get("eval_count", 0)
                    self._set_active_model(selected_model)
                    break
                except httpx.HTTPStatusError as e:
                    last_api_error = e
                    retryable = (
                        self.is_cloud
                        and "openrouter" in self.base_url
                        and not collected_summary
                        and _should_retry_openrouter_model_error(e.response)
                    )
                    if retryable:
                        if e.response.status_code == 429:
                            time.sleep(3)
                        continue
                    raise
            if last_api_error and not collected_summary:
                # --- Alibaba DashScope fallback for summary ---
                _ds_key = os.environ.get("DASHSCOPE_API_KEY", "")
                _is_rl = (
                    self.is_cloud
                    and "openrouter" in self.base_url
                    and last_api_error.response.status_code in (429, 402)
                    and _ds_key
                )
                if _is_rl:
                    from .alibaba_cloud import DASHSCOPE_API_BASE
                    for _ali_m in ["qwen-plus", "qwen3.5-397b-a17b"]:
                        try:
                            _ali_resp = self.client.post(
                                f"{DASHSCOPE_API_BASE}/chat/completions",
                                headers={
                                    "Authorization": f"Bearer {_ds_key}",
                                    "Content-Type": "application/json",
                                },
                                json={
                                    "model": _ali_m,
                                    "messages": payload["messages"],
                                    "stream": False,
                                    "max_tokens": 2048,
                                },
                                timeout=120,
                            )
                            if _ali_resp.status_code == 200:
                                _ali_data = _ali_resp.json()
                                _ali_content = (
                                    _ali_data.get("choices", [{}])[0]
                                    .get("message", {}).get("content", "")
                                )
                                if _ali_content:
                                    collected_summary = _ali_content
                                    yield TextDelta(_ali_content)
                                    break
                        except Exception:
                            continue
                if not collected_summary:
                    raise last_api_error
            duration_ms = (time.time() - start) * 1000
            self.messages.append({"role": "assistant", "content": collected_summary})
            self.cost.record_turn(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                tool_calls=0,
                duration_ms=duration_ms,
                model=self.model,
            )
            yield AgentDone(collected_summary or "[Agent hit iteration limit]")
        except httpx.HTTPStatusError as e:
            error_text = f"[API Error: {_format_http_error(e.response)}]"
            self.messages.append({"role": "assistant", "content": error_text})
            yield TextDelta(error_text)
            yield AgentDone(error_text)
        except Exception:
            yield AgentDone("[Agent hit iteration limit - task may be incomplete.]")

    def _execute_tool_calls(self, tool_calls: list[dict]) -> Generator[StreamEvent, None, None]:
        # Parse all tool call arguments upfront
        parsed: list[tuple[str, dict, str | None]] = []
        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name", "")
            tool_call_id = tc.get("id")
            arguments = fn.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            if not isinstance(arguments, dict):
                arguments = {}
            parsed.append((name, arguments, tool_call_id))

        # Sequential fallback: single tool, or any tool needs interactive permission / shell
        if len(parsed) <= 1 or any(
            n in GATED_TOOLS or n == "run_command" for n, _, _ in parsed
        ):
            for name, args, tool_call_id in parsed:
                yield from self._run_single_tool(name, args, tool_call_id=tool_call_id)
            return

        # --- Parallel execution path for multiple non-interactive tools ---
        # Phase 1: Validate all tools sequentially (fast)
        ready: list[tuple[int, str, dict, str | None]] = []
        for i, (name, args, tool_call_id) in enumerate(parsed):
            if not name or not name.strip():
                yield ToolCallStart(name or "(empty)", args)
                yield ToolCallEnd(name or "(empty)", "Error: empty tool name rejected", 0)
                self._store_tool_result(name or "(empty)", "Error: empty tool name", tool_call_id=tool_call_id)
                continue
            if not name.replace("_", "").replace("-", "").isalnum():
                yield ToolCallStart(name, args)
                yield ToolCallEnd(name, f"Error: invalid tool name '{name}'", 0)
                self._store_tool_result(name, "Error: invalid tool name", tool_call_id=tool_call_id)
                continue
            arg_error = self._validate_tool_arguments(name, args)
            if arg_error:
                yield ToolCallStart(name, args)
                yield ToolCallEnd(name, arg_error, 0)
                self._store_tool_result(name, arg_error, tool_call_id=tool_call_id)
                continue
            spam_found = False
            for v in args.values():
                if any(s in str(v).lower() for s in (".com\u590d\u5236", "\u5f00\u5956", "\u8d5b\u8f66", "\u5f69\u7968")):
                    yield ToolCallStart(name, args)
                    yield ToolCallEnd(name, "Rejected: hallucinated spam in arguments", 0)
                    self._store_tool_result(name, "Error: invalid arguments rejected", tool_call_id=tool_call_id)
                    spam_found = True
                    break
            if spam_found:
                continue
            hook_result = self._hooks.run_pre_hooks(name, args)
            if not hook_result.allow:
                yield ToolCallStart(name, args)
                yield ToolCallEnd(name, f"Blocked by hook: {hook_result.message}", 0)
                self._store_tool_result(name, f"Blocked by hook: {hook_result.message}", tool_call_id=tool_call_id)
                continue
            if self.permissions.blocks(name):
                yield ToolCallStart(name, args)
                yield ToolCallEnd(name, f"Permission denied: tool '{name}' is blocked.", 0)
                self._store_tool_result(name, f"Permission denied: tool '{name}' is blocked.", tool_call_id=tool_call_id)
                self.permissions.denials.append({"tool": name, "reason": "blocked"})
                continue
            ready.append((i, name, args, tool_call_id))

        if not ready:
            return

        # Phase 2: Execute valid tools in parallel
        results: dict[int, str] = {}
        timings: dict[int, float] = {}
        with ThreadPoolExecutor(max_workers=min(len(ready), 8)) as pool:
            futures = {}
            for idx, name, args, _tool_call_id in ready:
                timings[idx] = time.time()
                futures[pool.submit(self._execute_tool, name, args)] = idx
            for fut in as_completed(futures):
                idx = futures[fut]
                timings[idx] = (time.time() - timings[idx]) * 1000
                try:
                    results[idx] = fut.result()
                except Exception as e:
                    results[idx] = f"Error: {e}"

        # Phase 3: Yield events in original order + post-processing
        for idx, name, args, tool_call_id in ready:
            result = results.get(idx, "Error: no result")
            dur = timings.get(idx, 0)
            self._hooks.run_post_hooks(name, args, result)
            self._store_tool_result(name, result, tool_call_id=tool_call_id)
            if self._on_tool_call:
                self._on_tool_call(name, args)
            if self._on_tool_result:
                self._on_tool_result(name, result[:500])
            yield ToolCallStart(name, args)
            yield ToolCallEnd(name, result, dur)

    # ── image-aware tool result storage ──────────────────────────
    _IMAGE_MARKER = "__IMAGE_DATA__:"

    def _store_tool_result(self, name: str, result: str, tool_call_id: str | None = None) -> None:
        """Store a tool result in self.messages, promoting images to
        multimodal content blocks so vision-capable models can see them."""
        if self._IMAGE_MARKER in result:
            # Split into text metadata and image data URI
            parts = result.split(self._IMAGE_MARKER, 1)
            metadata = parts[0].strip()
            data_uri = parts[1].strip()
            # Store compact metadata as the tool message
            tool_metadata = metadata or f"Tool '{name}' returned image data."
            tool_message: dict[str, Any] = {"role": "tool", "content": tool_metadata}
            if tool_call_id:
                tool_message["tool_call_id"] = tool_call_id
            self.messages.append(tool_message)
            # Send image as a multimodal user message (OpenAI-compatible)
            self.messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": f"[Image from tool '{name}']"},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            })
        else:
            # Normal text truncation for non-image results
            hist = (
                result if len(result) <= 8000
                else result[:8000] + "\n... [truncated for context]"
            )
            tool_message: dict[str, Any] = {"role": "tool", "content": hist}
            if tool_call_id:
                tool_message["tool_call_id"] = tool_call_id
            self.messages.append(tool_message)

    def _run_single_tool(self, name: str, arguments: dict, tool_call_id: str | None = None) -> Generator[StreamEvent, None, None]:
        # FIX: Reject empty or invalid tool names immediately (prevents crashes)
        if not name or not name.strip():
            yield ToolCallStart(name or "(empty)", arguments)
            yield ToolCallEnd(name or "(empty)", "Error: empty tool name rejected", 0)
            self._store_tool_result(name or "(empty)", "Error: empty tool name", tool_call_id=tool_call_id)
            return
        if not name.replace("_", "").replace("-", "").isalnum():
            yield ToolCallStart(name, arguments)
            yield ToolCallEnd(name, f"Error: invalid tool name '{name}'", 0)
            self._store_tool_result(name, "Error: invalid tool name", tool_call_id=tool_call_id)
            return

        arg_error = self._validate_tool_arguments(name, arguments)
        if arg_error:
            yield ToolCallStart(name, arguments)
            yield ToolCallEnd(name, arg_error, 0)
            self._store_tool_result(name, arg_error, tool_call_id=tool_call_id)
            return

        # Guard: reject tool calls with hallucinated/spam arguments
        for v in arguments.values():
            sv = str(v)
            if any(spam in sv.lower() for spam in (".com复制", "开奖", "赛车", "彩票")):
                yield ToolCallStart(name, arguments)
                yield ToolCallEnd(name, "Rejected: hallucinated spam in arguments", 0)
                self._store_tool_result(name, "Error: invalid arguments rejected", tool_call_id=tool_call_id)
                return

        # C1: Enforce permission gating for GATED_TOOLS
        if name in GATED_TOOLS:
            desc = f"{name}({', '.join(f'{k}={str(v)[:60]}' for k, v in arguments.items())})"
            if not self.permissions.request_permission(name, desc, self._confirm_fn):
                yield ToolCallStart(name, arguments)
                yield ToolCallEnd(name, f"Permission denied: user declined '{name}'", 0)
                self._store_tool_result(name, f"Permission denied: user declined '{name}'", tool_call_id=tool_call_id)
                return

        # Run pre-hooks (may deny the tool call) — use cached hooks (M1)
        hook_result = self._hooks.run_pre_hooks(name, arguments)
        if not hook_result.allow:
            yield ToolCallStart(name, arguments)
            yield ToolCallEnd(name, f"Blocked by hook: {hook_result.message}", 0)
            self._store_tool_result(name, f"Blocked by hook: {hook_result.message}", tool_call_id=tool_call_id)
            return

        yield ToolCallStart(name, arguments)
        start = time.time()

        if self.permissions.blocks(name):
            result = f"Permission denied: tool '{name}' is blocked."
            self.permissions.denials.append({"tool": name, "reason": "blocked"})
        elif name == "run_command":
            cmd = arguments.get("command", "")
            # Block recursive self-execution
            cmd_stripped = cmd.strip().lower()
            if any(cmd_stripped.startswith(bc) or cmd_stripped == bc.strip() for bc in BLOCKED_COMMANDS):
                result = f"Blocked: cannot run '{cmd}' (recursive self-execution)"
            else:
                # C2: Actually enforce dangerous command blocking
                warning = self.permissions.check_command_safety(cmd)
                if warning and not self.permissions.auto_approve:
                    if self._confirm_fn:
                        sys.stderr.write(f"\n⚠ {warning}\n")
                        if not self._confirm_fn():
                            result = f"Blocked: user declined dangerous command — {warning}"
                            self.permissions.denials.append({"tool": name, "reason": warning})
                            dur = (time.time() - start) * 1000
                            self._store_tool_result(name, result, tool_call_id=tool_call_id)
                            yield ToolCallEnd(name, result, dur)
                            return
                    else:
                        # No confirm_fn — block by default for safety
                        result = f"Blocked: {warning} (no confirmation handler)"
                        self.permissions.denials.append({"tool": name, "reason": warning})
                        dur = (time.time() - start) * 1000
                        self._store_tool_result(name, result, tool_call_id=tool_call_id)
                        yield ToolCallEnd(name, result, dur)
                        return
                result = self._execute_tool(name, arguments)
        else:
            result = self._execute_tool(name, arguments)

        # Run post-hooks (notification only) — use cached hooks (M1)
        self._hooks.run_post_hooks(name, arguments, result)

        dur = (time.time() - start) * 1000
        self._store_tool_result(name, result)

        if self._on_tool_call:
            self._on_tool_call(name, arguments)
        if self._on_tool_result:
            self._on_tool_result(name, result[:500])

        yield ToolCallEnd(name, result, dur)

    def _validate_tool_arguments(self, name: str, arguments: dict) -> str | None:
        if not isinstance(arguments, dict):
            return f"Error: invalid arguments for tool '{name}'"
        handler = TOOL_REGISTRY.get(name)
        if handler is None:
            return None
        try:
            signature = inspect.signature(handler)
        except (TypeError, ValueError):
            return None
        missing: list[str] = []
        for param in signature.parameters.values():
            if param.kind not in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            ):
                continue
            if param.default is not inspect.Parameter.empty:
                continue
            if param.name not in arguments:
                missing.append(param.name)
        if missing:
            return f"Error: missing required argument(s) for tool '{name}': {', '.join(missing)}"
        return None

    def _parse_tool_calls_from_text(self, text: str) -> list[tuple[str, dict]]:
        results = []
        for match in _TOOL_CALL_RE.finditer(text):
            name = match.group(1)
            if name in TOOL_REGISTRY or self._mcp.has_tool(name):
                try:
                    args = json.loads(match.group(2))
                    results.append((name, args))
                except json.JSONDecodeError:
                    pass
        return results

    def _execute_tool(self, name: str, arguments: dict) -> str:
        handler = TOOL_REGISTRY.get(name)
        if handler is not None:
            try:
                result = handler(**arguments)
                text = str(result)
                if len(text) > 30_000:
                    text = text[:30_000] + "\n... [truncated]"
                return text
            except Exception as exc:
                return f"Error running {name}: {exc}"
        # Fall back to MCP tool routing
        if self._mcp.has_tool(name):
            try:
                result = self._mcp.call_tool(name, arguments)
                if len(result) > 30_000:
                    result = result[:30_000] + "\n... [truncated]"
                return result
            except Exception as exc:
                return f"Error running MCP tool {name}: {exc}"
        return f"Error: unknown tool '{name}'"

    def close(self):
        """Clean up resources (HTTP client, MCP server connections)."""
        self.client.close()
        self._mcp.shutdown()
