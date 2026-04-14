# Claw Agent — Tool Reference

Complete guide to all 34 tools. Tools are the agent's hands — every action happens through a tool call.

## File Tools (4)

### read_file
Read contents of a file with optional line range.
```
read_file(path, start_line=None, end_line=None)
```
- **Always** read before editing
- Use line ranges for large files (read relevant section, not entire file)
- Returns content with line numbers

### write_file
Create or completely overwrite a file.
```
write_file(path, content)
```
- Use for NEW files or complete rewrites
- For small changes, prefer `replace_in_file` instead
- Creates parent directories automatically

### list_directory
List contents of a directory.
```
list_directory(path)
```
- Returns files and subdirectories
- Use to explore unfamiliar codebases
- Start at root, then drill into interesting directories

### find_files
Search for files by name pattern.
```
find_files(pattern, path=".")
```
- Glob-style patterns: `*.py`, `**/test_*.js`, `src/**/*.ts`
- Use to locate files before reading them

## Shell Tool (1)

### run_command
Execute a shell command.
```
run_command(command, timeout=30)
```
- Shell is **cmd.exe** on Windows — use `dir`, `type`, `findstr`
- Use for: running tests, installing packages, git operations, builds
- Never run commands that spawn this agent (no `claw` commands)
- Timeout default: 30 seconds

## Search Tool (1)

### grep_search
Search file contents with regex.
```
grep_search(pattern, path=".", include="")
```
- Fast regex search across files
- Use `include` to filter: `include="*.py"` or `include="*.ts"`
- Returns matching lines with file paths and line numbers
- Best for: finding function definitions, error strings, imports

## Edit Tools (4)

### replace_in_file
Replace exact text in a file.
```
replace_in_file(path, old_text, new_text)
```
- `old_text` must match EXACTLY (including whitespace and indentation)
- Include 3+ lines of context before and after the target
- For multiple replacements in one file, use `multi_edit_file`

### multi_edit_file
Multiple replacements in a single file.
```
multi_edit_file(path, edits=[{old_text, new_text}, ...])
```
- Edits applied sequentially — each edit sees the result of previous ones
- More efficient than multiple `replace_in_file` calls

### insert_at_line
Insert text at a specific line number.
```
insert_at_line(path, line_number, text)
```
- Line numbers are 1-based
- Inserts BEFORE the specified line

### diff_files
Compare two files or two versions.
```
diff_files(path1, path2)
```
- Returns unified diff format
- Use to verify changes or compare implementations

## Web Tools (2)

### web_search
Search the internet.
```
web_search(query)
```
- Returns search results with titles, URLs, and snippets
- Use for: documentation lookup, error messages, library research

### web_fetch
Fetch content from a URL.
```
web_fetch(url)
```
- Returns page content as text
- Use after `web_search` to read full articles/docs
- Respects robots.txt

## Agent Tools (4)

### run_subagent
Spawn a sub-agent for a specific task.
```
run_subagent(prompt, model=None)
```
- Sub-agent has its own context and tool access
- Use for: parallel tasks, isolated research, specialized analysis
- Results returned to parent agent

### plan_and_execute
Create and execute a multi-step plan.
```
plan_and_execute(goal, steps=[])
```
- Breaks complex goals into ordered steps
- Executes each step sequentially
- Tracks progress and handles failures

### plan_mode_start / plan_mode_response
Interactive planning mode.
- Start a plan, get user feedback, refine, then execute
- Use for large features or architectural changes

## Task Tools (4)

### task_create
Create a trackable task.
```
task_create(title, description="", priority="medium")
```

### task_update
Update task status or details.
```
task_update(task_id, status=None, notes=None)
```
- Statuses: not-started → in-progress → completed

### task_list
Show all current tasks.
```
task_list(status=None)
```

### task_get
Get details of a specific task.
```
task_get(task_id)
```

## Notebook Tool (1)

### notebook_run
Execute a Jupyter notebook cell or script.
```
notebook_run(code, language="python")
```
- Runs in isolated environment
- Returns output and any errors

## Context Tools (3)

### get_workspace_context
Get high-level overview of the workspace.
```
get_workspace_context()
```
- Returns: directory tree, git info, language detection, project type
- Use as FIRST step when exploring a new codebase

### git_diff
Show uncommitted changes.
```
git_diff(staged=False)
```
- Use to review what you've changed before committing

### git_log
Show recent commit history.
```
git_log(count=10)
```
- Use to understand recent changes and context

## Utility Tools (6)

### sleep
Pause execution.
```
sleep(seconds)
```

### config_get / config_set
Read/write agent configuration.
```
config_get(key)
config_set(key, value)
```

### powershell
Execute PowerShell command (Windows).
```
powershell(command)
```

### ask_user
Prompt the user for input.
```
ask_user(question)
```
- Use SPARINGLY — only when you genuinely need clarification
- Prefer using tools to find answers yourself

### tool_search
Search available tools by name or description.
```
tool_search(query)
```

## MCP Tools (2)

### mcp_list_tools / mcp_call_tool
Interact with external MCP servers.
- MCP extends Claw's capabilities with third-party tool servers
- List available tools from connected servers, then call them

## Tool Selection Guide

| Task | Best Tool |
|---|---|
| Find a file | `find_files` |
| Find text in files | `grep_search` |
| Read a file | `read_file` |
| Create new file | `write_file` |
| Edit existing file | `replace_in_file` or `multi_edit_file` |
| Run tests | `run_command` |
| Explore codebase | `get_workspace_context` + `list_directory` |
| Check git changes | `git_diff` |
| Research a topic | `web_search` + `web_fetch` |
| Complex multi-step | `plan_and_execute` or `task_create` |
