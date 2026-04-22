# Complete Guide

## Overview

Claw AI now runs as one visible assistant with hidden specialist passes.

Internal pass order:
1. Planner
2. Coder
3. Reviewer
4. Critic
5. Synthesizer

The user receives one final response.

## Providers

Primary:
- NVIDIA NIM

Secondary:
- Alibaba DashScope
- OpenAI/CometAPI (if configured)

Fallback:
- DeepSeek direct
- Local Ollama

## Install

```bash
pip install -e .
```

## Run

```bash
claw
```

## Core commands

```text
/help
/model
/models
/tools
/doctor
/status
/config
```

## Skills

Skills are loaded from claw_agent/skills.py and custom skill folders.
Use:
```text
/skills
```

## Plugins/tools wiring checks

Run:
```bash
python -m unittest discover -s tests -p "test_*.py"
node --check api/index.js
```

Check runtime:
```text
/doctor
/tools
```

## Security

- Keep API keys in environment or extension settings.
- Do not hardcode secrets in scripts.
- Use repository redaction for any leaked keys.