# Claw Agent — Workflow Patterns

Step-by-step patterns for common tasks. Each workflow is battle-tested.

## 1. Bug Fix Workflow

```
1. Reproduce: Read error message / test failure
2. Locate: grep_search for the error string, function name, or variable
3. Read: read_file the relevant source (± 50 lines of context)
4. Understand: Trace the data flow — inputs → processing → output
5. Fix: replace_in_file with minimal change (not a rewrite)
6. Verify: Run the failing test → confirm it passes
7. Regression: Run full test suite → confirm nothing else broke
8. Report: Summarize root cause + fix in 2-3 sentences
```

## 2. Feature Addition Workflow

```
1. Explore: list_directory + find_files to map the codebase
2. Pattern match: Read 2-3 similar features to understand conventions
3. Plan: If complex, task_create to break into steps
4. Implement: Write code following existing patterns
5. Test: Write tests FIRST (if TDD), then implement
6. Integrate: Update imports, registrations, exports
7. Verify: Run tests + read_file to confirm
8. Document: Update relevant .md files if architecture changed
```

## 3. Code Review Workflow

```
1. git_diff to see all changes
2. For each changed file:
   a. read_file the full file (not just the diff)
   b. Check: correctness, edge cases, style, naming
   c. Check: security (input validation, SQL injection, XSS)
   d. Check: performance (N+1 queries, unnecessary allocations)
3. Run tests to verify nothing is broken
4. Summarize findings as: Critical / Warning / Suggestion
```

## 4. Refactoring Workflow

```
1. Read the code to refactor (full context, not just the function)
2. Identify all callers: grep_search for the function/class name
3. Write tests for current behavior (if none exist)
4. Make the refactoring change
5. Update all callers
6. Run tests → confirm all green
7. git_diff to review the total change
```

## 5. New Project Setup Workflow

```
1. Create directory structure
2. Initialize package manager (pip, npm, cargo, etc.)
3. Set up configuration files (.env, tsconfig, pyproject.toml)
4. Create MEMORY.md, SOUL.md with project context
5. Write first test (proves the setup works)
6. Implement minimum viable feature
7. Run test → verify green
8. Initialize git, create .gitignore, first commit
```

## 6. Debugging Workflow (when stuck)

```
1. Re-read the error carefully — the answer is usually in the message
2. grep_search for the error string across the codebase
3. Add logging/print statements to trace execution flow
4. Check: Is the input correct? Is the dependency available?
5. Check: Has this worked before? What changed? (git_log)
6. If still stuck after 3 attempts:
   - Use AI Lab arena.py for adversarial analysis
   - Or ask_user for clarification
```

## 7. Multi-File Change Workflow

```
1. Plan all files that need changing (list them explicitly)
2. For each file:
   a. read_file (full relevant section)
   b. Make the change (replace_in_file or multi_edit_file)
   c. Verify the edit (read_file back)
3. Run tests after ALL files are changed (not between)
4. git_diff to review the complete changeset
5. Summarize all changes in a single response
```

## 8. Research Workflow

```
1. web_search for the topic
2. web_fetch the top 2-3 results
3. Extract key facts and code examples
4. Synthesize into a recommendation
5. Include sources/links in the response
```

## 9. System Prompt Enhancement Workflow

```
1. Read current system prompt in agent.py
2. Identify the gap or improvement needed
3. Draft the enhancement (match existing style)
4. Add to SYSTEM_PROMPT_TEMPLATE or appropriate .md file
5. Test by running claw with a relevant prompt
6. Iterate if the output quality isn't right
```

## 10. Council Mode Workflow

When multiple models disagree:
```
1. Each model in the council responds independently
2. Responses are compared by consensus voting
3. If majority agrees → use that answer
4. If split → escalate to Tier 1 Premium models only
5. If still split → present both options to user with tradeoff analysis
```

## Task Management

For multi-step work, use the task system:
- `task_create` — Define a task with clear acceptance criteria
- `task_update` — Mark progress (not-started → in-progress → completed)
- `task_list` — Show current task board
- `task_get` — Get details of a specific task

## Error Handling Patterns

| Error Type | Action |
|---|---|
| File not found | Check path, try find_files |
| Permission denied | Report to user, suggest fix |
| Test failure | Read assertion, fix logic |
| Tool timeout | Retry once, then report |
| Parse error | Read the file, check syntax |
| Network error | Retry with backoff, then report |

## Commit Message Convention

```
feat: add new feature
fix: bug fix
refactor: code restructure (no behavior change)
docs: documentation update
test: add or fix tests
chore: tooling, config, build
perf: performance improvement
```
