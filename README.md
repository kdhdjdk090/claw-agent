# Claw AI

Claw AI is a codex-style AI assistant with four user surfaces:

- Web app
- CLI coder agent
- Chrome extension
- VS Code agent

The active cloud stack is NVIDIA NIM first, with Alibaba Cloud DashScope as a secondary provider. Local Ollama mode is also supported for CLI and editor workflows.

## Quick Links

- Web app: https://clean-claw-ai.vercel.app
- Full install guide: [INSTALL_GUIDE.md](INSTALL_GUIDE.md)
- Global CLI install: [INSTALL_GLOBAL.md](INSTALL_GLOBAL.md)
- Chrome extension files: [chrome-extension](chrome-extension)
- VS Code extension files: [vscode-extension](vscode-extension)

## Download The Repo

```bash
git clone https://github.com/kdhdjdk090/claw-agent.git
cd claw-agent
```

You can also click the green `Code` button on GitHub and use `Download ZIP`.

## 1. Use The Web App

No install required:

```text
https://clean-claw-ai.vercel.app
```

Use this if you just want Claw AI immediately in the browser.

## 2. Install The CLI Coder Agent

### Option A: Install directly from GitHub

```bash
pip install git+https://github.com/kdhdjdk090/claw-agent.git
claw
```

### Option B: Install from a local clone

```bash
git clone https://github.com/kdhdjdk090/claw-agent.git
cd claw-agent
pip install -e .
claw
```

### Requirements

- Python 3.10+
- Git

### Cloud mode

Set at least one cloud key before running the CLI:

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

Optional secondary cloud key:

```bash
export DASHSCOPE_API_KEY="your-key"
```

### Local Ollama mode

```bash
ollama serve
claw
```

### Useful CLI commands

- `claw`
- `claw "explain this repo"`
- `claw --print "summarize this file"`
- `python -m claw_agent`

## 3. Install The Chrome Extension

The Chrome extension lives in [chrome-extension](chrome-extension).

### Load unpacked in Chrome

1. Open `chrome://extensions/`
2. Enable `Developer mode`
3. Click `Load unpacked`
4. Select the `chrome-extension/` folder from this repo
5. Pin `Claw Agent` from the Chrome extensions menu

### Configure extension keys

The extension reads keys from Chrome sync storage, not directly from `.env.local`.

Recommended local setup flow:

1. Create `.env.local` in the repo root with your keys
2. Run one of the helper scripts:

Windows PowerShell:

```powershell
.\setup-chrome-extension.ps1
```

Node:

```bash
node setup-chrome-extension.js
```

3. Open the generated helper script in `chrome-extension/AUTO_LOAD_KEYS.local.js`
4. Open the Claw side panel in Chrome
5. Right-click inside the panel -> `Inspect`
6. Paste the helper script into the DevTools console
7. Reload the extension

### Chrome extension features

- Side panel chat in any tab
- Model selector
- Browser-page context
- Context menu actions
- NVIDIA NIM backed chat flow

## 4. Install The VS Code Agent

The VS Code extension lives in [vscode-extension](vscode-extension).

### Option A: Run in development mode

```bash
cd vscode-extension
code .
```

Then press `F5` to launch an Extension Development Host.

### Option B: Package as VSIX

```bash
cd vscode-extension
npm install -g @vscode/vsce
vsce package
```

Then in VS Code:

1. Open Extensions
2. Click the `...` menu
3. Choose `Install from VSIX...`
4. Select the generated `.vsix` file

### Recommended VS Code settings

```json
{
  "claw.apiMode": "cloud",
  "claw.model": "qwen3.5-397b-a17b",
  "claw.nvidiaApiKey": "",
  "claw.dashscopeApiKey": "",
  "claw.ollamaUrl": "http://localhost:11434"
}
```

### VS Code commands

- `Claw: Open Agent Chat`
- `Claw: Quick Prompt`
- `Claw: Explain Selection`
- `Claw: Fix Selection`

## Environment Variables

Primary:

- `NVIDIA_API_KEY`

Optional:

- `NIM_API_KEY`
- `DASHSCOPE_API_KEY`
- `OPENAI_API_KEY`
- `COMETAPI_KEY`
- `DEEPSEEK_API_KEY`

Behavior flags:

- `DISABLE_COUNCIL=1`
- `PREFER_NVIDIA=1`
- `NVIDIA_DIRECT=1`
- `AUTH_MODE=chatgpt`
- `COUNCIL_PROVIDER=auto|nvidia|alibaba`

## Verify Your Setup

```bash
python -m unittest discover -s tests -p "test_*.py"
node --check api/index.js
```

## Common Problems

### `claw: command not found`

Reinstall the package and ensure Python scripts are on your `PATH`:

```bash
pip install -e .
```

### Chrome extension loads but cannot answer

Usually the extension has not been configured with keys in `chrome.storage.sync`. Run the Chrome setup helper and reload the extension.

### VS Code extension opens but chat does not work

Check:

- `claw.apiMode`
- `claw.model`
- `claw.nvidiaApiKey` or local runtime settings

### Vercel deploy works but old UI still shows

Hard refresh the browser after deploy. The main UI is an inline HTML/JS bundle and can be cached aggressively.

## Repo Structure

```text
claw-agent/
├── claw_agent/           # CLI runtime
├── api/                  # Vercel/server API
├── chrome-extension/     # Chrome sidepanel extension
├── vscode-extension/     # VS Code extension
├── INSTALL_GUIDE.md      # Full install guide
├── INSTALL_GLOBAL.md     # Global CLI guide
└── setup-chrome-extension.*  # Chrome helper scripts
```

If you want, I can also add a GitHub-friendly screenshot section and a `Getting Started` block at the top of the repo homepage.
