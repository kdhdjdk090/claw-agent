# Claw AI Installation Guide

This guide covers all supported Claw AI surfaces from the GitHub repo:

- Web app
- CLI coder agent
- Chrome extension
- VS Code agent

For the shortest overview, start with [README.md](README.md).

## Web App

Open:

```text
https://clean-claw-ai.vercel.app
```

No install required.

## CLI Coder Agent

### Install from GitHub

```bash
pip install git+https://github.com/kdhdjdk090/claw-agent.git
claw
```

### Install from local clone

```bash
git clone https://github.com/kdhdjdk090/claw-agent.git
cd claw-agent
pip install -e .
claw
```

### Cloud setup

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

Optional:

```bash
export DASHSCOPE_API_KEY="your-key"
```

### Local Ollama setup

```bash
ollama serve
claw
```

## Chrome Extension

### Install

1. Open `chrome://extensions/`
2. Enable `Developer mode`
3. Click `Load unpacked`
4. Select the `chrome-extension/` folder from this repo

### Configure

The extension needs keys copied into `chrome.storage.sync`.

Recommended flow:

```powershell
.\setup-chrome-extension.ps1
```

or

```bash
node setup-chrome-extension.js
```

Then:

1. Open the generated helper file in `chrome-extension/AUTO_LOAD_KEYS.local.js`
2. Open the Claw side panel
3. Right-click -> `Inspect`
4. Paste the helper script into the console
5. Reload the extension

## VS Code Agent

### Development mode

```bash
cd vscode-extension
code .
```

Press `F5` to launch the extension host.

### VSIX package

```bash
cd vscode-extension
npm install -g @vscode/vsce
vsce package
```

Install the generated `.vsix` using `Install from VSIX...` in VS Code.

### Suggested settings

```json
{
  "claw.apiMode": "cloud",
  "claw.model": "qwen3.5-397b-a17b",
  "claw.nvidiaApiKey": "",
  "claw.dashscopeApiKey": "",
  "claw.ollamaUrl": "http://localhost:11434"
}
```

## Environment Variables

Primary:

- `NVIDIA_API_KEY`

Optional:

- `NIM_API_KEY`
- `DASHSCOPE_API_KEY`
- `OPENAI_API_KEY`
- `COMETAPI_KEY`

## Verification

```bash
python -m unittest discover -s tests -p "test_*.py"
node --check api/index.js
node --check chrome-extension/sidepanel.js
```
