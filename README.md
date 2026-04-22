# Claw AI

Claw AI is an AI coding assistant with one visible assistant interface and an internal multi-role reasoning pipeline.

## What changed

- OpenRouter was replaced as the active provider.
- NVIDIA NIM is now the primary cloud backend.
- Alibaba DashScope remains available as a secondary backend.
- The runtime defaults to a codex-style role pipeline when cloud keys are present.
- The user sees one final answer; planner, coder, reviewer, critic, and synthesizer passes run internally.

## Architecture

User surfaces:
- CLI
- Web UI
- VS Code extension
- Chrome extension

Runtime flow:
1. Input arrives to one assistant.
2. Provider/mode is selected (codex role pipeline, direct cloud, or local fallback).
3. Tools are executed with permission checks.
4. Internal role deliberation runs when enabled.
5. One final answer is returned.

## Provider priority

1. Codex role pipeline (NVIDIA NIM or Alibaba)
2. NVIDIA direct
3. DeepSeek direct (compatibility fallback)
4. Local Ollama

## Vercel environment setup

If this repo is deployed on Vercel, add the NVIDIA key in Project Settings -> Environment Variables.

Recommended variables:
- `NVIDIA_API_KEY`: primary secret used by the NVIDIA NIM runtime
- `NIM_API_KEY`: optional compatibility alias if older code paths still read it
- `DASHSCOPE_API_KEY`: optional secondary provider

Apply `NVIDIA_API_KEY` to:
- `Production`
- `Preview`
- `Development` if you use `vercel dev`

After saving the variable, create a new deployment. Vercel environment changes do not affect older deployments retroactively.

CLI alternative:

```bash
vercel env add NVIDIA_API_KEY production
vercel env add NVIDIA_API_KEY preview
vercel env add NVIDIA_API_KEY development
```

To sync local development from Vercel:

```bash
vercel env pull .env.local
```

## Environment variables

Required for cloud:
- NVIDIA_API_KEY

Optional:
- NIM_API_KEY
- DASHSCOPE_API_KEY
- OPENAI_API_KEY
- COMETAPI_KEY
- DEEPSEEK_API_KEY

Behavior flags:
- DISABLE_COUNCIL=1
- PREFER_NVIDIA=1
- NVIDIA_DIRECT=1
- AUTH_MODE=chatgpt
- COUNCIL_PROVIDER=auto|nvidia|alibaba

## Quick start

```bash
python -m claw_agent
```

Windows wrapper:
```bash
claw
```

## Verify

```bash
python -m unittest discover -s tests -p "test_*.py"
node --check api/index.js
```

## Extensions

### Chrome extension
- Uses NVIDIA NIM endpoint: https://integrate.api.nvidia.com
- Reads key from chrome.storage.sync field: nvidia_api_key
- Optional secondary key: dashscope_api_key

### VS Code extension
- Uses the project API mode and model configuration.
- Should be configured with NVIDIA-first defaults.

## Skills and plugins

- Built-in skills are loaded from claw_agent/skills.py.
- Project context loads from MEMORY.md, SOUL.md, CLAW.md, REASONING.md, STYLEGUIDE.md.
- Plugin/tool wiring is validated through tests and runtime diagnostics.

## Notes

- Historical OpenRouter references may still exist in archival changelog notes.
- Active runtime paths are NVIDIA-first.
