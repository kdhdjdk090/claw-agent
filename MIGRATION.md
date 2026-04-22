# Migration Guide

## Goal

Migrate from OpenRouter-first behavior to NVIDIA NIM-first behavior with one-assistant output.

## Completed migration

- Runtime provider default switched to NVIDIA NIM.
- API server moved to NVIDIA endpoint.
- Chrome extension switched to nvidia_api_key + NVIDIA endpoint.
- Provider labels in CLI/status updated to NVIDIA NIM.
- Compatibility aliases preserved where required for older env naming.

## Required env update

Old:
- OPENROUTER_API_KEY

New:
- NVIDIA_API_KEY
- or NIM_API_KEY

## Post-migration validation

```bash
python -m unittest discover -s tests -p "test_*.py"
node --check api/index.js
```

## Operational notes

- Some legacy docs/changelogs may still mention old provider names.
- Active runtime and user-facing controls are NVIDIA-first.