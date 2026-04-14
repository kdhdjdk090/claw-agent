# Claw Agent — Project Memory

This file is automatically loaded into the agent's context at startup.
It is the agent's persistent memory about the project, architecture, and conventions.

## Project: Claw Agent
- **Language**: Python 3.10+ (strict type hints, asyncio throughout)
- **Package**: `claw_agent` — installed as `claw` CLI command
- **LLM Backends** (auto-detected, priority order):
  1. Council mode: 14 models via OpenRouter (8) + Alibaba Cloud (6)
  2. DeepSeek Cloud: deepseek-reasoner via API
  3. Ollama local: deepseek-v3.1:671b-cloud (default)
- **Surfaces**: CLI (`claw` command), VS Code extension, Chrome extension, Web UI (`public/index.html`)
- **Tools**: 34 tools across 11 categories (File, Shell, Search, Edit, AdvancedEdit, Web, Agent, Task, Notebook, Context, Utility, MCP)
- **Skills**: 18+ built-in skills — code, analyze, write, summarize, translate, math, reason (v2.0.0 w/ 8-patch engine), brainstorm, explain, extract, vision, debug, refactor, review, test, docs, design, search
- **AI Lab**: arena.py (Solver+Judge adversarial), reasoning_engine.py (8-patch), seaks.py (Self-Evolving Kernel)
- **Council**: ll_council.py — 14 models in 3 tiers (Premium/Specialized/Fast) with consensus voting

## Architecture
- System prompt assembled from 6 layers in `agent.py`:
  1. SYSTEM_PROMPT_TEMPLATE (identity, tools, rules, formatting)
  2. _load_project_context() → MEMORY.md, SOUL.md, .claw (4K cap each)
  3. get_all_skills_context() → custom skill definitions from skills.py
  4. REASONING_WISDOM → arena.py adversarial testing insights
  5. SEAKS kernel → self-evolving rules from seaks.py
  6. MCP context → external tool server descriptions
- Constants: MAX_ITERATIONS=200, MAX_CONTEXT_TOKENS=200K, AUTO_COMPACT_THRESHOLD=100K
- CLI rendering: Rich Markdown with `monokai` code theme
- Web UI rendering: formatMarkdown() regex parser

## Conventions
- **HTTP**: httpx (never `requests`)
- **CLI formatting**: Rich library (Markdown, Panel, Table)
- **Testing**: test_full.py (92 tests), test_slash_and_ext.py (102 tests), pytest
- **Tool result limits**: 8K in CLI, 4K in Chrome extension
- **Tool registry**: `claw_agent/tools/__init__.py` — TOOL_REGISTRY dict
- **Skill registry**: `claw_agent/skills.py` — BUILTIN_SKILLS dict
- **Config files**: Searched in cwd + 3 parent directories
- **Shell**: cmd.exe on Windows — use `dir`, `type`, `findstr` (not Unix commands)

## Key Files
- `agent.py` — Core loop, streaming, 6-layer system prompt assembly
- `cli.py` — Interactive CLI with Rich markdown rendering
- `skills.py` — Skill definitions (SkillInfo dataclass) + install/uninstall
- `ll_council.py` — 14-model council with tier-based routing
- `tools/__init__.py` — All 34 tool registrations
- `ai_lab/` — Arena, reasoning engine, SEAKS
- `sessions.py` — Conversation persistence & auto-compaction
- `hooks.py` — Pre/post tool execution pipeline
- `mcp.py` — Model Context Protocol server integration

## Known Issues
- Bridge cost event test is flaky (timing issue, not a real bug)
- Chrome extension: javascript_eval removed (CSP blocks it on most sites)
- SEAKS kernel evolution rate needs tuning for edge-case prompts
- Council mode requires OPENROUTER_API_KEY in env; falls back to DeepSeek if unset

## Recent Changes
- PATCH 8 added to reasoning_engine.py — constraint feasibility checker (ELITE verdict)
- CLI response rendering upgraded from raw stdout to Rich Markdown buffering
- Web UI `addMessage()` now uses `formatMarkdown()` for assistant messages
- System prompt enhanced with 10 RESPONSE FORMATTING rules
- CLAW.md rewritten as master configuration (was incorrectly Rust-focused)

## Notes
- Add your own project notes below this line
