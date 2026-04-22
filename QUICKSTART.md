# Quick Start

## 1) Set API key (recommended)

PowerShell:
```powershell
$env:NVIDIA_API_KEY="your-key"
```

cmd:
```cmd
set NVIDIA_API_KEY=your-key
```

Linux/macOS:
```bash
export NVIDIA_API_KEY="your-key"
```

## 2) Run

```bash
claw
```

or

```bash
python -m claw_agent
```

## 3) Check mode

In CLI:
```text
/status
/model
/doctor
```

Expected cloud mode details show NVIDIA NIM (or Alibaba if selected).

## Common commands

```text
/help
/tools
/cost
/save
/sessions
/resume <id>
/diff
/config
/quit
```

## Troubleshooting

- If cloud key is missing, runtime can fall back to local/deepseek mode.
- If council is too heavy for a task, set DISABLE_COUNCIL=1.
- Run diagnostics with /doctor.