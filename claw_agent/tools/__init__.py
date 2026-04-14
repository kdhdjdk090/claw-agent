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

# ---- Image edit tools (4) ---------------------------------------------------
from .image_edit_tools import resize_image, crop_image, convert_image, create_thumbnail

# ---- PDF tools (2) ----------------------------------------------------------
from .pdf_tools import read_pdf, pdf_info

# ---- Data tools (3) ---------------------------------------------------------
from .data_tools import parse_csv, csv_stats, json_query

# ---- Config tools (3) -------------------------------------------------------
from .config_tools import read_config, write_config, validate_json

# ---- Diff tools (2) ---------------------------------------------------------
from .diff_tools import file_diff, compare_dirs

# ---- Network tools (3) ------------------------------------------------------
from .network_tools import ping_host, dns_lookup, check_port

# ---- Text tools (3) ---------------------------------------------------------
from .text_tools import word_count, markdown_to_html, render_template

# ---- Database tools (2) -----------------------------------------------------
from .db_tools import sqlite_query, sqlite_schema

# ---- Regex tools (2) --------------------------------------------------------
from .regex_tools import test_regex, explain_regex

# ---- Test tools (3) ---------------------------------------------------------
from .test_tools import run_tests, parse_test_output, generate_test_stub

# ---- Lint tools (3) ---------------------------------------------------------
from .lint_tools import format_code, lint_check, auto_fix_lint

# ---- Package tools (3) ------------------------------------------------------
from .package_tools import list_dependencies, check_outdated, audit_dependencies

# ---- Docker tools (4) -------------------------------------------------------
from .docker_tools import docker_ps, docker_build, docker_compose_up, docker_compose_down

# ---- Log tools (3) ----------------------------------------------------------
from .log_tools import parse_log, tail_file, search_logs

# ---- Crypto tools (4) -------------------------------------------------------
from .crypto_tools import generate_token, hash_string, base64_codec, checksum_file

# ---- Metrics tools (3) ------------------------------------------------------
from .metrics_tools import count_lines, code_complexity, file_type_stats

# ---- Math tools (3) ---------------------------------------------------------
from .math_tools import evaluate_expr, convert_units, number_base

# ---- Datetime tools (3) -----------------------------------------------------
from .datetime_tools import now_tz, date_diff, parse_cron

# ---- Scaffold tools (3) -----------------------------------------------------
from .scaffold_tools import init_project, add_gitignore, add_license

# ---- Doc tools (3) ----------------------------------------------------------
from .doc_tools import extract_signatures, generate_docstring, generate_readme

# ---- Profile tools (3) ------------------------------------------------------
from .profile_tools import time_command, memory_usage, benchmark

# ---- Validation tools (3) ---------------------------------------------------
from .validation_tools import validate_json_schema, validate_yaml, check_url

# ---- Template tools (3) -----------------------------------------------------
from .template_tools import tpl_render, tpl_list_vars, tpl_render_file

# ---- Snippet tools (3) ------------------------------------------------------
from .snippet_tools import save_snippet, load_snippet, search_snippets

# ---- Backup tools (3) -------------------------------------------------------
from .backup_tools import backup_file, restore_backup, list_backups

# ---- SQL tools (3) ----------------------------------------------------------
from .sql_tools import sql_run, sql_tables, csv_to_sqlite

# ---- API mock tools (3) -----------------------------------------------------
from .api_mock_tools import mock_endpoint, mock_server, stop_mock

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
    # Image editing (4)
    "resize_image": resize_image,
    "crop_image": crop_image,
    "convert_image": convert_image,
    "create_thumbnail": create_thumbnail,
    # PDF (2)
    "read_pdf": read_pdf,
    "pdf_info": pdf_info,
    # Data (3)
    "parse_csv": parse_csv,
    "csv_stats": csv_stats,
    "json_query": json_query,
    # Config (3)
    "read_config": read_config,
    "write_config": write_config,
    "validate_json": validate_json,
    # Diff (2)
    "file_diff": file_diff,
    "compare_dirs": compare_dirs,
    # Network (3)
    "ping_host": ping_host,
    "dns_lookup": dns_lookup,
    "check_port": check_port,
    # Text (3)
    "word_count": word_count,
    "markdown_to_html": markdown_to_html,
    "render_template": render_template,
    # Database (2)
    "sqlite_query": sqlite_query,
    "sqlite_schema": sqlite_schema,
    # Regex (2)
    "test_regex": test_regex,
    "explain_regex": explain_regex,
    # Testing (3)
    "run_tests": run_tests,
    "parse_test_output": parse_test_output,
    "generate_test_stub": generate_test_stub,
    # Linting (3)
    "format_code": format_code,
    "lint_check": lint_check,
    "auto_fix_lint": auto_fix_lint,
    # Packages (3)
    "list_dependencies": list_dependencies,
    "check_outdated": check_outdated,
    "audit_dependencies": audit_dependencies,
    # Docker (4)
    "docker_ps": docker_ps,
    "docker_build": docker_build,
    "docker_compose_up": docker_compose_up,
    "docker_compose_down": docker_compose_down,
    # Logging (3)
    "parse_log": parse_log,
    "tail_file": tail_file,
    "search_logs": search_logs,
    # Crypto (4)
    "generate_token": generate_token,
    "hash_string": hash_string,
    "base64_codec": base64_codec,
    "checksum_file": checksum_file,
    # Metrics (3)
    "count_lines": count_lines,
    "code_complexity": code_complexity,
    "file_type_stats": file_type_stats,
    # Math (3)
    "evaluate_expr": evaluate_expr,
    "convert_units": convert_units,
    "number_base": number_base,
    # Datetime (3)
    "now_tz": now_tz,
    "date_diff": date_diff,
    "parse_cron": parse_cron,
    # Scaffold (3)
    "init_project": init_project,
    "add_gitignore": add_gitignore,
    "add_license": add_license,
    # Doc (3)
    "extract_signatures": extract_signatures,
    "generate_docstring": generate_docstring,
    "generate_readme": generate_readme,
    # Profile (3)
    "time_command": time_command,
    "memory_usage": memory_usage,
    "benchmark": benchmark,
    # Validation (3)
    "validate_json_schema": validate_json_schema,
    "validate_yaml": validate_yaml,
    "check_url": check_url,
    # Template (3)
    "tpl_render": tpl_render,
    "tpl_list_vars": tpl_list_vars,
    "tpl_render_file": tpl_render_file,
    # Snippet (3)
    "save_snippet": save_snippet,
    "load_snippet": load_snippet,
    "search_snippets": search_snippets,
    # Backup (3)
    "backup_file": backup_file,
    "restore_backup": restore_backup,
    "list_backups": list_backups,
    # SQL (3)
    "sql_run": sql_run,
    "sql_tables": sql_tables,
    "csv_to_sqlite": csv_to_sqlite,
    # API Mock (3)
    "mock_endpoint": mock_endpoint,
    "mock_server": mock_server,
    "stop_mock": stop_mock,
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
    # === IMAGE EDITING ===
    {
        "type": "function",
        "function": {
            "name": "resize_image",
            "description": "Resize an image to specified dimensions, preserving aspect ratio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the image file."},
                    "width": {"type": "integer", "description": "Target width in pixels."},
                    "height": {"type": "integer", "description": "Target height in pixels (0 = auto)."},
                    "output": {"type": "string", "description": "Output path (default: overwrite)."},
                },
                "required": ["file_path", "width"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crop_image",
            "description": "Crop an image to a bounding box (left, top, right, bottom).",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the image file."},
                    "left": {"type": "integer", "description": "Left pixel coordinate."},
                    "top": {"type": "integer", "description": "Top pixel coordinate."},
                    "right": {"type": "integer", "description": "Right pixel coordinate."},
                    "bottom": {"type": "integer", "description": "Bottom pixel coordinate."},
                    "output": {"type": "string", "description": "Output path."},
                },
                "required": ["file_path", "left", "top", "right", "bottom"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "convert_image",
            "description": "Convert image to another format (png, jpg, webp, bmp, gif, tiff).",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the image file."},
                    "format": {"type": "string", "description": "Target format: png, jpg, webp, bmp, gif, tiff."},
                    "output": {"type": "string", "description": "Output path."},
                },
                "required": ["file_path", "format"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_thumbnail",
            "description": "Create a square thumbnail of an image.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the image file."},
                    "size": {"type": "integer", "description": "Thumbnail size in pixels (default 128)."},
                    "output": {"type": "string", "description": "Output path."},
                },
                "required": ["file_path"],
            },
        },
    },
    # === PDF ===
    {
        "type": "function",
        "function": {
            "name": "read_pdf",
            "description": "Extract text from a PDF file, optionally specific pages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the PDF file."},
                    "pages": {"type": "string", "description": "Page range, e.g. '1-3' or '1,3,5' (default: all)."},
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pdf_info",
            "description": "Get PDF metadata: page count, author, title, file size.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the PDF file."},
                },
                "required": ["file_path"],
            },
        },
    },
    # === DATA ===
    {
        "type": "function",
        "function": {
            "name": "parse_csv",
            "description": "Parse and display a CSV/TSV file in a readable table format.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the CSV file."},
                    "limit": {"type": "integer", "description": "Max rows to display (default 50)."},
                    "delimiter": {"type": "string", "description": "Delimiter character (default ','). Use '\\t' for TSV."},
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "csv_stats",
            "description": "Compute statistics (count, mean, median, stdev, min, max) for a CSV column.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the CSV file."},
                    "column": {"type": "string", "description": "Column name to analyze."},
                },
                "required": ["file_path", "column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "json_query",
            "description": "Read and query JSON data using dot-notation paths (e.g. 'data.items.0.name').",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path_or_text": {"type": "string", "description": "Path to a JSON file or inline JSON text."},
                    "query": {"type": "string", "description": "Dot-notation query path (optional)."},
                },
                "required": ["file_path_or_text"],
            },
        },
    },
    # === CONFIG ===
    {
        "type": "function",
        "function": {
            "name": "read_config",
            "description": "Read a config file (JSON, YAML, TOML, INI, .env) and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the config file."},
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_config",
            "description": "Set a value in a JSON config file using dot-notation key path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the JSON config file."},
                    "key": {"type": "string", "description": "Dot-notation key path (e.g. 'server.port')."},
                    "value": {"type": "string", "description": "Value to set (auto-detects type)."},
                },
                "required": ["file_path", "key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_json",
            "description": "Validate JSON syntax, optionally against a JSON Schema.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text_or_file": {"type": "string", "description": "JSON text or path to a JSON file."},
                    "schema": {"type": "string", "description": "Optional JSON Schema to validate against."},
                },
                "required": ["text_or_file"],
            },
        },
    },
    # === DIFF ===
    {
        "type": "function",
        "function": {
            "name": "file_diff",
            "description": "Show unified diff between two files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_a": {"type": "string", "description": "Path to the first file."},
                    "file_b": {"type": "string", "description": "Path to the second file."},
                    "context_lines": {"type": "integer", "description": "Lines of context (default 3)."},
                },
                "required": ["file_a", "file_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_dirs",
            "description": "Compare two directories recursively, showing files unique to each and differing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_a": {"type": "string", "description": "Path to the first directory."},
                    "dir_b": {"type": "string", "description": "Path to the second directory."},
                    "extensions": {"type": "string", "description": "Comma-separated file extensions to filter (e.g. '.py,.js')."},
                },
                "required": ["dir_a", "dir_b"],
            },
        },
    },
    # === NETWORK ===
    {
        "type": "function",
        "function": {
            "name": "ping_host",
            "description": "Ping a host and return latency statistics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "Hostname or IP address."},
                    "count": {"type": "integer", "description": "Number of pings (default 4, max 20)."},
                },
                "required": ["host"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "dns_lookup",
            "description": "Look up DNS records for a hostname.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hostname": {"type": "string", "description": "Domain name to look up."},
                    "record_type": {"type": "string", "description": "Record type: A, AAAA, MX, TXT, NS, CNAME (default A)."},
                },
                "required": ["hostname"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_port",
            "description": "Check if a TCP port is open on a host, with optional banner grab.",
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "Hostname or IP address."},
                    "port": {"type": "integer", "description": "Port number to check."},
                    "timeout": {"type": "number", "description": "Timeout in seconds (default 5)."},
                },
                "required": ["host", "port"],
            },
        },
    },
    # === TEXT ===
    {
        "type": "function",
        "function": {
            "name": "word_count",
            "description": "Count words, lines, characters, sentences, and paragraphs in text or a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text_or_file": {"type": "string", "description": "Text content or path to a file."},
                },
                "required": ["text_or_file"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "markdown_to_html",
            "description": "Convert Markdown text to HTML.",
            "parameters": {
                "type": "object",
                "properties": {
                    "markdown_text": {"type": "string", "description": "Markdown content to convert."},
                },
                "required": ["markdown_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "render_template",
            "description": "Render a Python format-string template with variables.",
            "parameters": {
                "type": "object",
                "properties": {
                    "template": {"type": "string", "description": "Template string with {variable} placeholders."},
                    "variables": {"type": "string", "description": "JSON object of variable name→value pairs."},
                },
                "required": ["template", "variables"],
            },
        },
    },
    # === DATABASE ===
    {
        "type": "function",
        "function": {
            "name": "sqlite_query",
            "description": "Execute a SQL query on a SQLite database file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "db_path": {"type": "string", "description": "Path to the SQLite database file."},
                    "query": {"type": "string", "description": "SQL query to execute."},
                    "params": {"type": "string", "description": "JSON array of query parameters for ? placeholders."},
                },
                "required": ["db_path", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sqlite_schema",
            "description": "Show the schema of all tables in a SQLite database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "db_path": {"type": "string", "description": "Path to the SQLite database file."},
                },
                "required": ["db_path"],
            },
        },
    },
    # === REGEX ===
    {
        "type": "function",
        "function": {
            "name": "test_regex",
            "description": "Test a regex pattern against text, showing all matches with positions and groups.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Regular expression pattern."},
                    "text": {"type": "string", "description": "Text to match against."},
                    "flags": {"type": "string", "description": "Regex flags: i=ignorecase, m=multiline, s=dotall, x=verbose."},
                },
                "required": ["pattern", "text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_regex",
            "description": "Explain a regex pattern in human-readable terms.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Regular expression pattern to explain."},
                },
                "required": ["pattern"],
            },
        },
    },
    # === TESTING ===
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Auto-detect test framework and run tests in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Project root directory."},
                    "framework": {"type": "string", "description": "Force framework: pytest, jest, go, cargo, unittest, mocha."},
                    "pattern": {"type": "string", "description": "File/test name pattern filter."},
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "parse_test_output",
            "description": "Parse test output into structured results (passed, failed, skipped, errors).",
            "parameters": {
                "type": "object",
                "properties": {
                    "output": {"type": "string", "description": "Raw test output text."},
                },
                "required": ["output"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_test_stub",
            "description": "Generate a test file skeleton for a source file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_file": {"type": "string", "description": "Path to the source file to generate tests for."},
                    "framework": {"type": "string", "description": "Test framework: pytest, jest, go."},
                },
                "required": ["source_file"],
            },
        },
    },
    # === LINTING ===
    {
        "type": "function",
        "function": {
            "name": "format_code",
            "description": "Run code formatter on a file (black, prettier, gofmt, rustfmt).",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "File to format."},
                    "formatter": {"type": "string", "description": "Force formatter: black, prettier, gofmt, rustfmt."},
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lint_check",
            "description": "Run linter on a file (ruff, eslint, go vet, clippy).",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "File to lint."},
                    "linter": {"type": "string", "description": "Force linter: ruff, eslint, go, clippy."},
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "auto_fix_lint",
            "description": "Run linter with auto-fix on a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "File to auto-fix."},
                    "linter": {"type": "string", "description": "Linter to use: ruff, eslint, go, clippy."},
                },
                "required": ["file_path"],
            },
        },
    },
    # === PACKAGES ===
    {
        "type": "function",
        "function": {
            "name": "list_dependencies",
            "description": "List project dependencies (pip, npm, cargo, go).",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Project root directory."},
                    "ecosystem": {"type": "string", "description": "Force ecosystem: python, node, rust, go."},
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_outdated",
            "description": "Check for outdated dependencies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Project root directory."},
                    "ecosystem": {"type": "string", "description": "Force ecosystem: python, node, rust, go."},
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "audit_dependencies",
            "description": "Audit dependencies for known security vulnerabilities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Project root directory."},
                    "ecosystem": {"type": "string", "description": "Force ecosystem: python, node."},
                },
                "required": ["directory"],
            },
        },
    },
    # === DOCKER ===
    {
        "type": "function",
        "function": {
            "name": "docker_ps",
            "description": "List Docker containers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "all_containers": {"type": "boolean", "description": "Show all containers including stopped ones."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "docker_build",
            "description": "Build a Docker image from a Dockerfile.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Build context directory."},
                    "tag": {"type": "string", "description": "Image tag (e.g. myapp:latest)."},
                    "dockerfile": {"type": "string", "description": "Path to Dockerfile (default: Dockerfile)."},
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "docker_compose_up",
            "description": "Start Docker Compose services.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory containing docker-compose.yml."},
                    "detach": {"type": "boolean", "description": "Run in background (default true)."},
                    "services": {"type": "string", "description": "Specific services to start (space-separated)."},
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "docker_compose_down",
            "description": "Stop Docker Compose services.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory containing docker-compose.yml."},
                    "remove_volumes": {"type": "boolean", "description": "Also remove volumes (default false)."},
                },
                "required": ["directory"],
            },
        },
    },
    # === LOGGING ===
    {
        "type": "function",
        "function": {
            "name": "parse_log",
            "description": "Parse a log file with optional level and pattern filtering.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to log file."},
                    "level": {"type": "string", "description": "Filter by level: ERROR, WARN, INFO, DEBUG."},
                    "pattern": {"type": "string", "description": "Regex pattern to filter lines."},
                    "last_n": {"type": "integer", "description": "Return only the last N matching lines."},
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tail_file",
            "description": "Return the last N lines of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "File to tail."},
                    "lines": {"type": "integer", "description": "Number of lines (default 20, max 500)."},
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_logs",
            "description": "Search for a pattern across all log files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to search."},
                    "pattern": {"type": "string", "description": "Regex pattern to search."},
                    "extensions": {"type": "string", "description": "File extensions to search (comma-separated, default: .log,.txt)."},
                    "max_results": {"type": "integer", "description": "Max matching lines to return (default 50)."},
                },
                "required": ["directory", "pattern"],
            },
        },
    },
    # === CRYPTO ===
    {
        "type": "function",
        "function": {
            "name": "generate_token",
            "description": "Generate a cryptographically secure random token or password.",
            "parameters": {
                "type": "object",
                "properties": {
                    "length": {"type": "integer", "description": "Token length (default 32)."},
                    "charset": {"type": "string", "description": "Type: hex, alphanumeric, base64, urlsafe, digits, password."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hash_string",
            "description": "Hash a string with a given algorithm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to hash."},
                    "algorithm": {"type": "string", "description": "Algorithm: sha256, sha512, sha1, md5, blake2b."},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "base64_codec",
            "description": "Encode or decode base64 text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to encode or decode."},
                    "operation": {"type": "string", "description": "'encode' or 'decode' (default encode)."},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "checksum_file",
            "description": "Compute the checksum of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to file."},
                    "algorithm": {"type": "string", "description": "Algorithm: sha256, sha512, sha1, md5, blake2b."},
                },
                "required": ["file_path"],
            },
        },
    },
    # === METRICS ===
    {
        "type": "function",
        "function": {
            "name": "count_lines",
            "description": "Count lines of code by language in a directory (code, blank, comment breakdown).",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Root directory to scan."},
                    "include": {"type": "string", "description": "Comma-separated extensions to include (e.g. '.py,.js')."},
                    "exclude_dirs": {"type": "string", "description": "Comma-separated directories to skip."},
                },
                "required": ["directory"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "code_complexity",
            "description": "Calculate cyclomatic complexity for a Python file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to Python file."},
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_type_stats",
            "description": "Show file extension distribution in a directory (count and size).",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to analyze."},
                },
                "required": ["directory"],
            },
        },
    },
    # === MATH ===
    {
        "type": "function",
        "function": {
            "name": "evaluate_expr",
            "description": "Safely evaluate a math expression (supports +,-,*,/,**,sqrt,sin,cos,log,etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression to evaluate."},
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "convert_units",
            "description": "Convert between units (length, weight, data, time, volume, temperature).",
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {"type": "number", "description": "Numeric value to convert."},
                    "from_unit": {"type": "string", "description": "Source unit (e.g. 'km', 'lb', 'gb', 'C')."},
                    "to_unit": {"type": "string", "description": "Target unit (e.g. 'mi', 'kg', 'mb', 'F')."},
                },
                "required": ["value", "from_unit", "to_unit"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "number_base",
            "description": "Convert a number between bases (2-36, or aliases: bin, oct, dec, hex).",
            "parameters": {
                "type": "object",
                "properties": {
                    "number": {"type": "string", "description": "Number string (e.g. '255', '0xff', '0b1010')."},
                    "from_base": {"type": "string", "description": "Source base: 2-36 or bin/oct/dec/hex."},
                    "to_base": {"type": "string", "description": "Target base: 2-36 or bin/oct/dec/hex."},
                },
                "required": ["number", "from_base", "to_base"],
            },
        },
    },
    # === DATETIME ===
    {
        "type": "function",
        "function": {
            "name": "now_tz",
            "description": "Get current date and time in any timezone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tz": {"type": "string", "description": "Timezone: UTC, EST, PST, JST, IST, CET, or offset like '+5'."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "date_diff",
            "description": "Calculate the difference between two dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date1": {"type": "string", "description": "First date (YYYY-MM-DD or 'today')."},
                    "date2": {"type": "string", "description": "Second date (YYYY-MM-DD or 'today'). Defaults to today."},
                },
                "required": ["date1"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "parse_cron",
            "description": "Explain a cron expression in plain English.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Cron expression (e.g. '*/5 * * * *')."},
                },
                "required": ["expression"],
            },
        },
    },
    # === SCAFFOLD ===
    {
        "type": "function",
        "function": {
            "name": "init_project",
            "description": "Initialize a project directory with boilerplate files for a given language.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory to create the project in."},
                    "language": {"type": "string", "description": "Language: python, node, go, or rust."},
                    "name": {"type": "string", "description": "Project name (defaults to directory name)."},
                },
                "required": ["path", "language"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_gitignore",
            "description": "Add a language-appropriate .gitignore to a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory to add .gitignore to."},
                    "language": {"type": "string", "description": "Language: python, node, go, rust, or general."},
                },
                "required": ["path", "language"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_license",
            "description": "Create a LICENSE file in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory to add the LICENSE to."},
                    "license_type": {"type": "string", "description": "License: mit, apache2, or gpl3."},
                    "author": {"type": "string", "description": "Copyright holder name."},
                },
                "required": ["path", "license_type"],
            },
        },
    },
    # === DOC ===
    {
        "type": "function",
        "function": {
            "name": "extract_signatures",
            "description": "Extract all function and class signatures from a Python file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to a .py file."},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_docstring",
            "description": "Generate docstring templates for undocumented functions in a Python file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to a .py file."},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_readme",
            "description": "Generate a README.md skeleton from a project directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the project root directory."},
                },
                "required": ["path"],
            },
        },
    },
    # === PROFILE ===
    {
        "type": "function",
        "function": {
            "name": "time_command",
            "description": "Time a shell command over N runs, returning min/avg/max.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to time."},
                    "runs": {"type": "integer", "description": "Number of runs (default 3)."},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "memory_usage",
            "description": "Run a Python script and report peak memory usage via tracemalloc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "script_path": {"type": "string", "description": "Path to the Python script to profile."},
                },
                "required": ["script_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "benchmark",
            "description": "Compare two commands side-by-side with timing results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd_a": {"type": "string", "description": "First command."},
                    "cmd_b": {"type": "string", "description": "Second command."},
                    "runs": {"type": "integer", "description": "Number of runs each (default 3)."},
                },
                "required": ["cmd_a", "cmd_b"],
            },
        },
    },
    # === VALIDATION ===
    {
        "type": "function",
        "function": {
            "name": "validate_json_schema",
            "description": "Validate a JSON string against a JSON Schema.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "JSON string to validate."},
                    "schema": {"type": "string", "description": "JSON Schema string to validate against."},
                },
                "required": ["data", "schema"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_yaml",
            "description": "Validate YAML syntax and optionally check structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "YAML string to validate."},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_url",
            "description": "Check if a URL is reachable and return status code and headers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to check."},
                },
                "required": ["url"],
            },
        },
    },
    # === TEMPLATE ===
    {
        "type": "function",
        "function": {
            "name": "tpl_render",
            "description": "Render a string template by substituting {{ var }} placeholders.",
            "parameters": {
                "type": "object",
                "properties": {
                    "template": {"type": "string", "description": "Template string with {{ varname }} placeholders."},
                    "variables": {"type": "string", "description": "JSON dict of variable→value mappings."},
                },
                "required": ["template", "variables"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tpl_list_vars",
            "description": "Extract all {{ var }} placeholder names from a template string.",
            "parameters": {
                "type": "object",
                "properties": {
                    "template": {"type": "string", "description": "Template string to scan."},
                },
                "required": ["template"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "tpl_render_file",
            "description": "Read a template file, substitute variables, and optionally write result.",
            "parameters": {
                "type": "object",
                "properties": {
                    "template_path": {"type": "string", "description": "Path to the template file."},
                    "variables": {"type": "string", "description": "JSON dict of variable→value mappings."},
                    "output_path": {"type": "string", "description": "Optional output path to write rendered result."},
                },
                "required": ["template_path", "variables"],
            },
        },
    },
    # === SNIPPET ===
    {
        "type": "function",
        "function": {
            "name": "save_snippet",
            "description": "Save a named code snippet for later reuse.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Unique name for the snippet."},
                    "code": {"type": "string", "description": "The code/text content to save."},
                    "language": {"type": "string", "description": "Language hint (e.g. python, js)."},
                    "tags": {"type": "string", "description": "Comma-separated tags."},
                },
                "required": ["name", "code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "load_snippet",
            "description": "Load a previously saved code snippet by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the snippet to load."},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_snippets",
            "description": "Search saved snippets by name, tags, or content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term to match against names, tags, and content."},
                },
                "required": ["query"],
            },
        },
    },
    # === BACKUP ===
    {
        "type": "function",
        "function": {
            "name": "backup_file",
            "description": "Create a timestamped backup of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to back up."},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "restore_backup",
            "description": "Restore a file from a named backup.",
            "parameters": {
                "type": "object",
                "properties": {
                    "backup_name": {"type": "string", "description": "Name of the backup file (from list_backups)."},
                    "dest": {"type": "string", "description": "Destination path to restore to. Defaults to original location."},
                },
                "required": ["backup_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_backups",
            "description": "List available backups, optionally filtered by filename.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filter_name": {"type": "string", "description": "Optional substring to filter backup names."},
                },
                "required": [],
            },
        },
    },
    # === SQL ===
    {
        "type": "function",
        "function": {
            "name": "sql_run",
            "description": "Execute a SQL query on a SQLite database, returning formatted results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "db_path": {"type": "string", "description": "Path to the SQLite database file."},
                    "sql": {"type": "string", "description": "SQL query to execute."},
                },
                "required": ["db_path", "sql"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sql_tables",
            "description": "Show tables, columns, types, and row counts for a SQLite database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "db_path": {"type": "string", "description": "Path to the SQLite database file."},
                },
                "required": ["db_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "csv_to_sqlite",
            "description": "Import a CSV file into a SQLite table.",
            "parameters": {
                "type": "object",
                "properties": {
                    "csv_path": {"type": "string", "description": "Path to the CSV file."},
                    "db_path": {"type": "string", "description": "Path to the SQLite database (created if needed)."},
                    "table": {"type": "string", "description": "Table name (defaults to CSV filename)."},
                },
                "required": ["csv_path", "db_path"],
            },
        },
    },
    # === API MOCK ===
    {
        "type": "function",
        "function": {
            "name": "mock_endpoint",
            "description": "Register a mock HTTP endpoint with a canned response.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "URL path to mock (e.g. /api/users)."},
                    "method": {"type": "string", "description": "HTTP method: GET, POST, PUT, DELETE (default GET)."},
                    "status": {"type": "integer", "description": "HTTP status code (default 200)."},
                    "body": {"type": "string", "description": "Response body string."},
                    "content_type": {"type": "string", "description": "Content-Type header (default application/json)."},
                },
                "required": ["path", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mock_server",
            "description": "Start a mock HTTP server with all registered endpoints.",
            "parameters": {
                "type": "object",
                "properties": {
                    "port": {"type": "integer", "description": "Port to listen on (default 8089)."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stop_mock",
            "description": "Stop a running mock HTTP server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "port": {"type": "integer", "description": "Port of the server to stop (default 8089)."},
                },
                "required": [],
            },
        },
    },
]
