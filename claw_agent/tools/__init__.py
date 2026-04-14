"""Tool registry — all tools for Ollama tool-calling."""

from __future__ import annotations

from typing import Any, Callable

# ---- File tools (4) ---------------------------------------------------------
from .file_tools import read_file, write_file, list_directory, find_files

# ---- Shell tools (1) --------------------------------------------------------
from .shell_tools import run_command

# ---- Search tools (1) -------------------------------------------------------
from .search_tools import grep_search

# ---- Edit tools (1) ---------------------------------------------------------
from .edit_tools import replace_in_file

# ---- Advanced edit tools (3) -------------------------------------------------
from .advanced_edit_tools import multi_edit_file, insert_at_line, diff_files

# ---- Web tools (2) ----------------------------------------------------------
from .web_tools import web_fetch, web_search

# ---- Agent tools (4) --------------------------------------------------------
from .agent_tools import run_subagent, plan_and_execute, enter_plan_mode, exit_plan_mode

# ---- Task tools (4) ---------------------------------------------------------
from .task_tools import task_create, task_update, task_list, task_get

# ---- Notebook tools (1) -----------------------------------------------------
from .notebook_tools import notebook_run

# ---- Context tools (3) ------------------------------------------------------
from .context_tools import get_workspace_context, git_diff, git_log

# ---- Utility tools (5 — ported from Rust + new) ----------------------------
from .utility_tools import sleep_tool, config_get, config_set, powershell, ask_user, tool_search

# ---- Memory tools (1 unified) ------------------------------------------------
from .memory_tools import memory

# ---- Image tools (2) --------------------------------------------------------
from .image_tools import view_image, list_images

# ---- Semantic search tools (1) -----------------------------------------------
from .semantic_search_tools import semantic_search

# ---- Diagnostic tools (2) ----------------------------------------------------
from .diagnostic_tools import get_errors, check_syntax

# ---- Terminal tools (5) ------------------------------------------------------
from .terminal_tools import (
    terminal_run_async, terminal_get_output, terminal_send,
    terminal_kill, terminal_list,
)

# ---- Git tools (5) -----------------------------------------------------------
from .git_tools import (
    get_changed_files, git_stash, git_branch, git_blame, git_show_commit,
)

# ---- Browser tools (2) ------------------------------------------------------
from .browser_tools import open_browser, open_file_in_browser

# ---- Diagram tools (2) ------------------------------------------------------
from .diagram_tools import render_mermaid, mermaid_template

# ---- MCP resource tools (2) -------------------------------------------------
from ..mcp import read_mcp_resource, list_mcp_resources

# ---- Code intelligence tools (2) --------------------------------------------
from .code_intel_tools import find_references, rename_symbol

# ---- Todo tools (1) ---------------------------------------------------------
from .todo_tools import manage_todos

# ---- HTTP tools (1) ---------------------------------------------------------
from .http_tools import http_request

# ---- Project tools (2) ------------------------------------------------------
from .project_tools import get_project_info, install_packages

# ---- Archive tools (2) ------------------------------------------------------
from .archive_tools import create_archive, extract_archive

# ---- Environment tools (3) --------------------------------------------------
from .env_tools import read_env, write_env, set_env_var

# ---- Process tools (2) ------------------------------------------------------
from .process_tools import list_processes, kill_process

# ---- Hash / encoding tools (2) ----------------------------------------------
from .hash_tools import compute_hash, encode_decode

# ---- Clipboard tools (2) ----------------------------------------------------
from .clipboard_tools import clipboard_copy, clipboard_read

# ---- Registry ----------------------------------------------------------------

TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    # File system (4)
    "read_file": read_file,
    "write_file": write_file,
    "list_directory": list_directory,
    "find_files": find_files,
    # Shell (1)
    "run_command": run_command,
    # Search (1)
    "grep_search": grep_search,
    # Editing (4)
    "replace_in_file": replace_in_file,
    "multi_edit_file": multi_edit_file,
    "insert_at_line": insert_at_line,
    "diff_files": diff_files,
    # Web (2)
    "web_fetch": web_fetch,
    "web_search": web_search,
    # Agents (4)
    "run_subagent": run_subagent,
    "plan_and_execute": plan_and_execute,
    "enter_plan_mode": enter_plan_mode,
    "exit_plan_mode": exit_plan_mode,
    # Tasks (4)
    "task_create": task_create,
    "task_update": task_update,
    "task_list": task_list,
    "task_get": task_get,
    # Notebook (1)
    "notebook_run": notebook_run,
    # Context (3)
    "get_workspace_context": get_workspace_context,
    "git_diff": git_diff,
    "git_log": git_log,
    # Utility (4 — ported from Rust)
    "sleep": sleep_tool,
    "config_get": config_get,
    "config_set": config_set,
    "powershell": powershell,
    # Interaction (2)
    "ask_user": ask_user,
    "tool_search": tool_search,
    # MCP resources (2)
    "read_mcp_resource": read_mcp_resource,
    "list_mcp_resources": list_mcp_resources,
    # Memory (1)
    "memory": memory,
    # Image (2)
    "view_image": view_image,
    "list_images": list_images,
    # Semantic search (1)
    "semantic_search": semantic_search,
    # Diagnostics (2)
    "get_errors": get_errors,
    "check_syntax": check_syntax,
    # Terminal (5)
    "terminal_run_async": terminal_run_async,
    "terminal_get_output": terminal_get_output,
    "terminal_send": terminal_send,
    "terminal_kill": terminal_kill,
    "terminal_list": terminal_list,
    # Git (5)
    "get_changed_files": get_changed_files,
    "git_stash": git_stash,
    "git_branch": git_branch,
    "git_blame": git_blame,
    "git_show_commit": git_show_commit,
    # Browser (2)
    "open_browser": open_browser,
    "open_file_in_browser": open_file_in_browser,
    # Diagrams (2)
    "render_mermaid": render_mermaid,
    "mermaid_template": mermaid_template,
    # Code intelligence (2)
    "find_references": find_references,
    "rename_symbol": rename_symbol,
    # Todo (1)
    "manage_todos": manage_todos,
    # HTTP (1)
    "http_request": http_request,
    # Project (2)
    "get_project_info": get_project_info,
    "install_packages": install_packages,
    # Archive (2)
    "create_archive": create_archive,
    "extract_archive": extract_archive,
    # Environment (3)
    "read_env": read_env,
    "write_env": write_env,
    "set_env_var": set_env_var,
    # Process (2)
    "list_processes": list_processes,
    "kill_process": kill_process,
    # Hash / encoding (2)
    "compute_hash": compute_hash,
    "encode_decode": encode_decode,
    # Clipboard (2)
    "clipboard_copy": clipboard_copy,
    "clipboard_read": clipboard_read,
}

# ---- Ollama tool definitions (OpenAI-compatible) ----------------------------

OLLAMA_TOOL_DEFINITIONS: list[dict[str, Any]] = [
    # === FILE SYSTEM ===
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file. Returns the file text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read."},
                    "start_line": {"type": "integer", "description": "Optional 1-based start line."},
                    "end_line": {"type": "integer", "description": "Optional 1-based end line."},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file with content. Creates parent dirs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path."},
                    "content": {"type": "string", "description": "Full file content."},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and folders in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_files",
            "description": "Find files matching a glob pattern recursively.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern e.g. '**/*.py'."},
                    "directory": {"type": "string", "description": "Root directory."},
                },
                "required": ["pattern"],
            },
        },
    },
    # === SHELL ===
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command. Returns stdout+stderr. 120s timeout.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run."},
                    "cwd": {"type": "string", "description": "Working directory."},
                },
                "required": ["command"],
            },
        },
    },
    # === SEARCH ===
    {
        "type": "function",
        "function": {
            "name": "grep_search",
            "description": "Search for a regex pattern in files. Returns matching lines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Regex pattern."},
                    "directory": {"type": "string", "description": "Directory to search."},
                    "include": {"type": "string", "description": "File glob filter."},
                },
                "required": ["pattern"],
            },
        },
    },
    # === EDITING ===
    {
        "type": "function",
        "function": {
            "name": "replace_in_file",
            "description": "Replace an exact unique string in a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path."},
                    "old_string": {"type": "string", "description": "Exact text to find (unique)."},
                    "new_string": {"type": "string", "description": "Replacement text."},
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "multi_edit_file",
            "description": "Apply multiple edits to a file atomically. Edits is JSON: [{\"old\":\"...\",\"new\":\"...\"}]",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path."},
                    "edits": {"type": "string", "description": "JSON array of {old, new} objects."},
                },
                "required": ["path", "edits"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "insert_at_line",
            "description": "Insert text at a specific line number in a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path."},
                    "line_number": {"type": "integer", "description": "1-based line number."},
                    "text": {"type": "string", "description": "Text to insert."},
                },
                "required": ["path", "line_number", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "diff_files",
            "description": "Show unified diff between two files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path_a": {"type": "string", "description": "First file."},
                    "path_b": {"type": "string", "description": "Second file."},
                },
                "required": ["path_a", "path_b"],
            },
        },
    },
    # === WEB ===
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch a web page and extract its text content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch (http/https)."},
                    "max_chars": {"type": "integer", "description": "Max chars to return."},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web using DuckDuckGo. No API key needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query."},
                    "num_results": {"type": "integer", "description": "Number of results."},
                },
                "required": ["query"],
            },
        },
    },
    # === SUB-AGENTS ===
    {
        "type": "function",
        "function": {
            "name": "run_subagent",
            "description": "Spawn a focused sub-agent for a specific task. It runs independently and returns results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Task description for the sub-agent."},
                    "model": {"type": "string", "description": "Ollama model to use (optional)."},
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plan_and_execute",
            "description": "Break a complex goal into steps, then execute each with a sub-agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "description": "The complex goal to accomplish."},
                },
                "required": ["goal"],
            },
        },
    },
    # === TASKS ===
    {
        "type": "function",
        "function": {
            "name": "task_create",
            "description": "Create a new persistent task with optional steps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title."},
                    "steps": {"type": "string", "description": "Newline-separated steps."},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task_update",
            "description": "Update a task's status (pending/in_progress/completed/failed).",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID."},
                    "status": {"type": "string", "description": "New status."},
                    "result": {"type": "string", "description": "Result/output text."},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task_list",
            "description": "List all tracked tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status_filter": {"type": "string", "description": "Filter by status."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task_get",
            "description": "Get detailed info about a specific task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID."},
                },
                "required": ["task_id"],
            },
        },
    },
    # === NOTEBOOK ===
    {
        "type": "function",
        "function": {
            "name": "notebook_run",
            "description": "Execute a Python code snippet and return output. Like a Jupyter cell.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute."},
                    "timeout": {"type": "integer", "description": "Timeout in seconds."},
                },
                "required": ["code"],
            },
        },
    },
    # === CONTEXT ===
    {
        "type": "function",
        "function": {
            "name": "get_workspace_context",
            "description": "Detect project type, file counts, git status for a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to analyze."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": "Show git diff of current changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Repo directory."},
                    "staged": {"type": "boolean", "description": "Show staged changes only."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_log",
            "description": "Show recent git commits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Repo directory."},
                    "count": {"type": "integer", "description": "Number of commits."},
                },
                "required": [],
            },
        },
    },
    # === UTILITY (ported from Rust) ===
    {
        "type": "function",
        "function": {
            "name": "sleep",
            "description": "Pause execution for a number of seconds (1-60). Useful for waiting or polling.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {"type": "integer", "description": "Seconds to sleep (1-60)."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "config_get",
            "description": "Read agent configuration. Returns all config or a specific key.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Config key to read (optional, omit for all)."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "config_set",
            "description": "Set an agent configuration value. Persisted to ~/.claw-agent/config.json.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Config key."},
                    "value": {"type": "string", "description": "Config value."},
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "powershell",
            "description": "Execute a PowerShell command directly. Use for Windows commands like Get-ChildItem, Measure-Object, Select-Object.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "PowerShell command to execute."},
                    "cwd": {"type": "string", "description": "Working directory."},
                },
                "required": ["command"],
            },
        },
    },
    # === INTERACTION ===
    {
        "type": "function",
        "function": {
            "name": "ask_user",
            "description": (
                "Ask the user a clarifying question and get their answer. "
                "Use ONLY when you genuinely cannot proceed without human input — "
                "e.g. choosing between approaches, confirming a destructive action, "
                "or getting a value you cannot infer from the codebase. "
                "Do NOT use to ask what files contain — read them yourself."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The question to ask the user."},
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of suggested answer choices shown to the user.",
                    },
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tool_search",
            "description": "Search available tools by name or description. Use to discover which tools exist before deciding which to call.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term (tool name fragment or keyword)."},
                },
                "required": ["query"],
            },
        },
    },
    # === PLAN MODE ===
    {
        "type": "function",
        "function": {
            "name": "enter_plan_mode",
            "description": (
                "Switch to Plan Mode — propose your action plan as numbered steps "
                "WITHOUT executing any tools, then wait for user approval. "
                "Use for complex multi-step tasks where you want human confirmation before acting."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "exit_plan_mode",
            "description": "Exit Plan Mode and return to normal execution (tools allowed again).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    # === MCP RESOURCES ===
    {
        "type": "function",
        "function": {
            "name": "list_mcp_resources",
            "description": "List resources exposed by an MCP server (files, DB records, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_name": {"type": "string", "description": "Name of the configured MCP server."},
                },
                "required": ["server_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_mcp_resource",
            "description": "Read a specific resource from an MCP server by URI. Use list_mcp_resources first to find URIs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_name": {"type": "string", "description": "Name of the configured MCP server."},
                    "resource_uri": {"type": "string", "description": "URI of the resource (e.g. 'file:///path/to/doc')."},
                },
                "required": ["server_name", "resource_uri"],
            },
        },
    },
    # === MEMORY ===
    {
        "type": "function",
        "function": {
            "name": "memory",
            "description": "Persistent memory system. Commands: view, create, str_replace, insert, delete, rename. Scopes: /memories/ (user), /memories/session/ (conversation), /memories/repo/ (project).",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Operation: view|create|str_replace|insert|delete|rename."},
                    "path": {"type": "string", "description": "Path under /memories/ e.g. '/memories/notes.md'."},
                    "content": {"type": "string", "description": "For create: file content. For str_replace: (use old_str/new_str)."},
                    "old_str": {"type": "string", "description": "For str_replace: exact string to replace."},
                    "new_str": {"type": "string", "description": "For str_replace: replacement string."},
                    "line": {"type": "integer", "description": "For insert: 0-based line number."},
                    "text": {"type": "string", "description": "For insert: text to insert."},
                    "new_path": {"type": "string", "description": "For rename: new path."},
                },
                "required": ["command"],
            },
        },
    },
    # === IMAGE ===
    {
        "type": "function",
        "function": {
            "name": "view_image",
            "description": "View image file metadata and content (PNG, JPG, GIF, WebP, SVG). Returns dimensions, size, format, and base64 data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the image file."},
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_images",
            "description": "List all image files in a directory recursively.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to scan."},
                },
                "required": [],
            },
        },
    },
    # === SEMANTIC SEARCH ===
    {
        "type": "function",
        "function": {
            "name": "semantic_search",
            "description": "Natural language search across codebase using TF-IDF. Finds relevant code by keyword similarity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query."},
                    "directory": {"type": "string", "description": "Root directory to search."},
                    "max_results": {"type": "integer", "description": "Max results to return (default 10)."},
                },
                "required": ["query"],
            },
        },
    },
    # === DIAGNOSTICS ===
    {
        "type": "function",
        "function": {
            "name": "get_errors",
            "description": "Get compile/lint errors for files. Supports Python (py_compile+flake8), JS/TS (node --check), JSON.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths to check.",
                    },
                    "workspace": {"type": "string", "description": "Workspace root directory."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_syntax",
            "description": "Check syntax of a single file (Python, JSON, JS/TS).",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file to check."},
                },
                "required": ["file_path"],
            },
        },
    },
    # === TERMINAL (async persistent sessions) ===
    {
        "type": "function",
        "function": {
            "name": "terminal_run_async",
            "description": "Start a long-running command in a persistent background terminal session. Returns a session ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to run."},
                    "cwd": {"type": "string", "description": "Working directory."},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "terminal_get_output",
            "description": "Get collected output from a persistent terminal session.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID returned by terminal_run_async."},
                },
                "required": ["session_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "terminal_send",
            "description": "Send input text to a running terminal session's stdin.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID."},
                    "text": {"type": "string", "description": "Text to send (newline appended automatically)."},
                },
                "required": ["session_id", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "terminal_kill",
            "description": "Kill a persistent terminal session.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "Session ID."},
                },
                "required": ["session_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "terminal_list",
            "description": "List all active persistent terminal sessions.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    # === GIT (enhanced) ===
    {
        "type": "function",
        "function": {
            "name": "get_changed_files",
            "description": "Get all changed files in a git repo: staged, unstaged, untracked, and merge conflicts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cwd": {"type": "string", "description": "Repository directory."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_stash",
            "description": "Git stash operations: list, push, pop, apply, drop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Action: list|push|pop|apply|drop."},
                    "message": {"type": "string", "description": "Stash message (for push)."},
                    "cwd": {"type": "string", "description": "Repository directory."},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_branch",
            "description": "Git branch operations: list, create, switch, delete, current.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Action: list|create|switch|delete|current."},
                    "name": {"type": "string", "description": "Branch name (for create/switch/delete)."},
                    "cwd": {"type": "string", "description": "Repository directory."},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_blame",
            "description": "Show git blame for a file or line range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "File to blame."},
                    "start_line": {"type": "integer", "description": "Start line (optional)."},
                    "end_line": {"type": "integer", "description": "End line (optional)."},
                    "cwd": {"type": "string", "description": "Repository directory."},
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_show_commit",
            "description": "Show details of a specific commit (message, diff, author, date).",
            "parameters": {
                "type": "object",
                "properties": {
                    "ref": {"type": "string", "description": "Commit hash or ref (HEAD, branch name)."},
                    "cwd": {"type": "string", "description": "Repository directory."},
                },
                "required": [],
            },
        },
    },
    # === BROWSER ===
    {
        "type": "function",
        "function": {
            "name": "open_browser",
            "description": "Open a URL in the default web browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to open (auto-prepends https:// if no scheme)."},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_file_in_browser",
            "description": "Open a local file (HTML, SVG, PDF) in the default browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to local file."},
                },
                "required": ["file_path"],
            },
        },
    },
    # === DIAGRAMS ===
    {
        "type": "function",
        "function": {
            "name": "render_mermaid",
            "description": "Render a Mermaid diagram to an image file (SVG/PNG/PDF). Falls back to raw code if mmdc not installed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Mermaid diagram code."},
                    "output_path": {"type": "string", "description": "Output file path."},
                    "format": {"type": "string", "description": "Output format: svg|png|pdf (default svg)."},
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mermaid_template",
            "description": "Get a Mermaid diagram template. Types: flowchart, sequence, class, state, er, gantt.",
            "parameters": {
                "type": "object",
                "properties": {
                    "diagram_type": {"type": "string", "description": "Template type: flowchart|sequence|class|state|er|gantt."},
                },
                "required": ["diagram_type"],
            },
        },
    },
    # === CODE INTELLIGENCE ===
    {
        "type": "function",
        "function": {
            "name": "find_references",
            "description": "Find all usages (references) of a code symbol across the workspace. Uses word-boundary grep.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Exact symbol name (function, class, variable)."},
                    "directory": {"type": "string", "description": "Root directory to search."},
                    "include_pattern": {"type": "string", "description": "Glob pattern to filter files (e.g. '*.py')."},
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rename_symbol",
            "description": "Rename a code symbol across all files in the workspace. Supports dry_run preview.",
            "parameters": {
                "type": "object",
                "properties": {
                    "old_name": {"type": "string", "description": "Current symbol name."},
                    "new_name": {"type": "string", "description": "New symbol name."},
                    "directory": {"type": "string", "description": "Root directory to search."},
                    "include_pattern": {"type": "string", "description": "Glob pattern to filter files (e.g. '*.py')."},
                    "dry_run": {"type": "boolean", "description": "Preview changes without applying (default true)."},
                },
                "required": ["old_name", "new_name"],
            },
        },
    },
    # === TODO / TASK TRACKING ===
    {
        "type": "function",
        "function": {
            "name": "manage_todos",
            "description": "In-session todo list. Actions: list, add, update, remove, clear. Track tasks during conversation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Action: list|add|update|remove|clear."},
                    "todo_id": {"type": "integer", "description": "Todo ID (for update/remove)."},
                    "title": {"type": "string", "description": "Todo title (for add/update)."},
                    "status": {"type": "string", "description": "Status: not-started|in-progress|completed (for update)."},
                },
                "required": ["action"],
            },
        },
    },
    # === HTTP CLIENT ===
    {
        "type": "function",
        "function": {
            "name": "http_request",
            "description": "Make HTTP requests (GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS). Full REST client.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Request URL."},
                    "method": {"type": "string", "description": "HTTP method (default GET)."},
                    "headers": {"type": "object", "description": "Request headers dict."},
                    "body": {"type": "string", "description": "Request body (for POST/PUT/PATCH)."},
                    "content_type": {"type": "string", "description": "Content-Type header shortcut."},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)."},
                },
                "required": ["url"],
            },
        },
    },
    # === PROJECT INFO ===
    {
        "type": "function",
        "function": {
            "name": "get_project_info",
            "description": "Detect project type, language, frameworks, dependencies, and scripts in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Project root directory."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "install_packages",
            "description": "Install packages using pip, npm, or cargo. Auto-detects package manager if not specified.",
            "parameters": {
                "type": "object",
                "properties": {
                    "packages": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of package names to install.",
                    },
                    "manager": {"type": "string", "description": "Package manager: pip|npm|yarn|cargo (auto-detect if omitted)."},
                    "directory": {"type": "string", "description": "Working directory."},
                },
                "required": ["packages"],
            },
        },
    },
    # === ARCHIVE ===
    {
        "type": "function",
        "function": {
            "name": "create_archive",
            "description": "Create a zip/tar/tar.gz/tar.bz2 archive from a file or directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "File or directory to archive."},
                    "output": {"type": "string", "description": "Output archive path."},
                    "format": {"type": "string", "description": "Format: zip|tar|tar.gz|tar.bz2 (default zip)."},
                },
                "required": ["source", "output"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "extract_archive",
            "description": "Extract a zip/tar/tar.gz/tar.bz2 archive to a destination directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "archive": {"type": "string", "description": "Path to archive file."},
                    "destination": {"type": "string", "description": "Extraction directory (default: archive location)."},
                },
                "required": ["archive"],
            },
        },
    },
    # === ENVIRONMENT ===
    {
        "type": "function",
        "function": {
            "name": "read_env",
            "description": "Read a .env file. Sensitive values (SECRET, KEY, TOKEN, PASSWORD) are masked.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to .env file (default .env)."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_env",
            "description": "Set or update a key=value in a .env file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Environment variable name."},
                    "value": {"type": "string", "description": "Value to set."},
                    "filepath": {"type": "string", "description": "Path to .env file (default .env)."},
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_env_var",
            "description": "Set an environment variable in the current process.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Variable name."},
                    "value": {"type": "string", "description": "Variable value."},
                },
                "required": ["key", "value"],
            },
        },
    },
    # === PROCESS MANAGEMENT ===
    {
        "type": "function",
        "function": {
            "name": "list_processes",
            "description": "List running system processes. Optionally filter by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filter_name": {"type": "string", "description": "Filter processes by name substring."},
                    "limit": {"type": "integer", "description": "Max results (default 50)."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "kill_process",
            "description": "Kill a process by PID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pid": {"type": "integer", "description": "Process ID to kill."},
                    "force": {"type": "boolean", "description": "Force kill (SIGKILL/taskkill /F). Default false."},
                },
                "required": ["pid"],
            },
        },
    },
    # === HASH / ENCODING ===
    {
        "type": "function",
        "function": {
            "name": "compute_hash",
            "description": "Compute hash of a file or string (sha256, sha1, md5, sha512, sha384).",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "File path or string to hash."},
                    "algorithm": {"type": "string", "description": "Hash algorithm: sha256|sha1|md5|sha512|sha384 (default sha256)."},
                    "is_file": {"type": "boolean", "description": "Treat target as file path (default: auto-detect)."},
                },
                "required": ["target"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "encode_decode",
            "description": "Encode/decode text. Supports base64, url, hex.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to encode or decode."},
                    "encoding": {"type": "string", "description": "Encoding type: base64|url|hex (default base64)."},
                    "decode": {"type": "boolean", "description": "Decode instead of encode (default false)."},
                },
                "required": ["text"],
            },
        },
    },
    # === CLIPBOARD ===
    {
        "type": "function",
        "function": {
            "name": "clipboard_copy",
            "description": "Copy text to system clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to copy to clipboard."},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clipboard_read",
            "description": "Read current contents of system clipboard.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]
