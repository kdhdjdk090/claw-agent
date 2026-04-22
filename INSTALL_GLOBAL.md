# Global CLI Installation

Use this guide if you only want the Claw AI CLI on a machine.

## Fast Install

```bash
pip install git+https://github.com/kdhdjdk090/claw-agent.git
claw
```

## Manual Install

```bash
git clone https://github.com/kdhdjdk090/claw-agent.git
cd claw-agent
pip install -e .
claw
```

## Requirements

- Python 3.10+
- Git

## Cloud Mode

Windows PowerShell:

```powershell
$env:NVIDIA_API_KEY="your-key"
claw
```

Linux/macOS:

```bash
export NVIDIA_API_KEY="your-key"
claw
```

Optional secondary provider:

```bash
export DASHSCOPE_API_KEY="your-key"
```

## Local Ollama Mode

```bash
ollama serve
claw
```

## Common Commands

```bash
claw
claw "explain this codebase"
claw --print "summarize this file"
python -m claw_agent
```

## Troubleshooting

### `claw: command not found`

Reinstall:

```bash
pip install -e .
```

### Import errors

Make sure you are in the cloned repo when using editable install:

```bash
cd claw-agent
```

### No cloud response

Check that `NVIDIA_API_KEY` is actually set in your shell before launching `claw`.
