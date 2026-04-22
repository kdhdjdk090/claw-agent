# CLI Cloud Setup

## Recommended cloud backend

Use NVIDIA NIM as the primary cloud provider.

## Setup

PowerShell:
```powershell
$env:NVIDIA_API_KEY="your-key"
```

Linux/macOS:
```bash
export NVIDIA_API_KEY="your-key"
```

Run:
```bash
claw
```

## Optional secondary backend

Alibaba DashScope:
```powershell
$env:DASHSCOPE_API_KEY="your-key"
```

## Mode behavior

- Default with NVIDIA key: codex role pipeline
- DISABLE_COUNCIL=1: direct NVIDIA mode
- No cloud keys: local/deepseek fallback

## Validate

```bash
python -m unittest discover -s tests -p "test_*.py"
```