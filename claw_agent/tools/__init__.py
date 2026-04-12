"""Tool registry — all 25 tools for Ollama tool-calling."""

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

# ---- Agent tools (2) --------------------------------------------------------
from .agent_tools import run_subagent, plan_and_execute

# ---- Task tools (4) ---------------------------------------------------------
from .task_tools import task_create, task_update, task_list, task_get

# ---- Notebook tools (1) -----------------------------------------------------
from .notebook_tools import notebook_run

# ---- Context tools (3) ------------------------------------------------------
from .context_tools import get_workspace_context, git_diff, git_log

# ---- Utility tools (3 — ported from Rust) ------------------------------------
from .utility_tools import sleep_tool, config_get, config_set, powershell

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
    # Agents (2)
    "run_subagent": run_subagent,
    "plan_and_execute": plan_and_execute,
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
    # Utility (3 — ported from Rust)
    "sleep": sleep_tool,
    "config_get": config_get,
    "config_set": config_set,
    "powershell": powershell,
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
]
