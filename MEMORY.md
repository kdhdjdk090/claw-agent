# Claw Agent — Project Memory

This file is automatically loaded into the agent's context at startup.
Add project-specific notes, conventions, and context here.
The agent will read this before every conversation.

## Project: Claw Agent
- Python 3.10+ project using Ollama for local LLM inference
- 22 tools for file ops, shell, search, editing, web, tasks, code
- 3 surfaces: CLI (claw command), VS Code extension, Chrome extension
- Default model: deepseek-v3.1:671b-cloud

## Conventions
- Use Rich for CLI formatting
- Use httpx for HTTP (not requests)
- Tests: test_full.py (92 tests), test_slash_and_ext.py (102 tests)
- Tool results truncated to 8K in CLI, 4K in Chrome extension
- All tools registered in claw_agent/tools/__init__.py

## Known Issues
- Bridge cost event test is flaky (timing issue, not a real bug)
- Chrome extension: javascript_eval removed (CSP blocks it on most sites)

## Notes
- Add your own project notes below this line
