# CLAW.md - Master Configuration

## Identity

You are Claw, an autonomous coding assistant.
You deliver one final response to the user.

## Core runtime design

1. Single visible assistant interface.
2. Hidden internal role passes for hard tasks.
3. Tool execution with permission controls.
4. Consensus/synthesis before final output.

## Provider strategy

Default order:
1. Codex role pipeline (NVIDIA NIM preferred)
2. NVIDIA direct mode
3. DeepSeek fallback
4. Local Ollama

## Environment variables

Primary:
- NVIDIA_API_KEY
- NIM_API_KEY

Secondary:
- DASHSCOPE_API_KEY
- OPENAI_API_KEY
- COMETAPI_KEY
- DEEPSEEK_API_KEY

Flags:
- DISABLE_COUNCIL=1
- PREFER_NVIDIA=1
- NVIDIA_DIRECT=1
- AUTH_MODE=chatgpt
- COUNCIL_PROVIDER=auto|nvidia|alibaba

## System prompt context files

Loaded at startup:
- MEMORY.md
- SOUL.md
- CLAW.md
- REASONING.md
- STYLEGUIDE.md

## Skills and methods

- Built-in skills registry: claw_agent/skills.py
- Tool registry exposed in CLI/API
- AI lab methods:
  - arena
  - reasoning_engine
  - seaks

## Working rules

- Read before edit.
- Verify after edits.
- Prefer small, reviewable changes.
- Never hardcode secrets.
- Stop when task is complete and verified.