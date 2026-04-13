# 🦞 Claw AI - Complete Installation Guide

## 🌐 Web Chat (No Install Required)

**Instant Access:** https://clean-claw-ai.vercel.app

No installation needed! Just open the URL and start chatting with 14 AI models.

---

## 💻 CLI Installation (Local Terminal)

### Prerequisites
- Python 3.10+ installed
- Git installed

### Install Steps

```bash
# 1. Clone or navigate to the project
cd c:\Users\Sinwa\Pictures\ClaudeAI\claw-agent

# 2. Install dependencies
pip install -e .

# 3. Set environment variables (already configured in .env.local)
# OPENROUTER_API_KEY and DASHSCOPE_API_KEY are already set

# 4. Start Claw AI
claw
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `claw` | Start interactive mode |
| `claw "Write a Python function"` | One-shot prompt |
| `claw --model openai/gpt-4o-mini` | Use specific model |
| `claw --print "Explain recursion"` | Print-only mode (no tools) |

---

## 🔌 Chrome Extension Installation

### Method 1: Load Unpacked (Developer Mode)

1. **Open Chrome Extensions:**
   - Go to `chrome://extensions/`
   - Enable **Developer mode** (toggle in top-right)

2. **Load the Extension:**
   - Click **"Load unpacked"**
   - Navigate to: `c:\Users\Sinwa\Pictures\ClaudeAI\claw-agent\chrome-extension`
   - Click **Select Folder**

3. **Pin to Toolbar:**
   - Click the puzzle icon (🧩) in Chrome toolbar
   - Pin **Claw Agent** to keep it visible

4. **Start Using:**
   - Click the Claw Agent icon
   - The extension uses **OpenRouter Cloud API** by default (no Ollama needed!)
   - Select model from dropdown: GPT-4o-mini, Claude 3 Haiku, etc.

### Method 2: Install from Chrome Web Store (Coming Soon)

*Will be available once published*

### Chrome Extension Features

- ✅ **40 browser control tools** - click, fill, navigate, extract
- ✅ **Cloud API mode** - Works without Ollama
- ✅ **Streaming responses** - Real-time output
- ✅ **Session persistence** - Chats saved between sessions
- ✅ **Model selection** - Choose from 6+ cloud models

---

## 💙 VS Code Extension Installation

### Method 1: Install from VSIX (Recommended)

1. **Package the Extension:**
   ```bash
   cd c:\Users\Sinwa\Pictures\ClaudeAI\claw-agent\vscode-extension
   npm install -g @vscode/vsce
   vsce package
   ```
   This creates `claw-agent-2.0.0.vsix`

2. **Install in VS Code:**
   - Open VS Code
   - Go to **Extensions** (Ctrl+Shift+X)
   - Click **"..."** → **Install from VSIX...**
   - Select `claw-agent-2.0.0.vsix`

3. **Configure:**
   - Open VS Code Settings (Ctrl+,)
   - Search for **"Claw"**
   - Set:
     - `claw.apiMode`: **cloud** (for OpenRouter)
     - `claw.model`: `openai/gpt-4o-mini` (or any OpenRouter model)
     - `claw.openrouterApiKey`: Leave empty (built-in key)

4. **Start Using:**
   - Press **Ctrl+Shift+A** to open Claw Agent
   - Or click the Claw icon in the activity bar

### Method 2: Development Mode

1. **Open in VS Code:**
   ```bash
   cd c:\Users\Sinwa\Pictures\ClaudeAI\claw-agent\vscode-extension
   code .
   ```

2. **Run Extension:**
   - Press **F5** to launch Extension Development Host
   - A new VS Code window opens with Claw Agent

### VS Code Features

- ✅ **Cloud API mode** - No Ollama required
- ✅ **Explain Selection** - Right-click → Claw: Explain
- ✅ **Fix Selection** - Right-click → Claw: Fix
- ✅ **Agent Chat** - Full chat interface in sidebar
- ✅ **Model selection** - Choose from OpenRouter models

---

## ️ API Configuration

### OpenRouter API Key (Pre-configured)
```
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
```

### Alibaba Cloud API Key (Pre-configured)
```
sk-dd77222941994dd2b7d76d728f211047
```

Both keys are already configured in all platforms. No additional setup needed!

---

## 🤖 Available Models

### OpenRouter Models (8)
| Model | Use Case |
|-------|----------|
| `deepseek/deepseek-v3` | Most powerful (600B MoE) |
| `qwen/qwen3-80b` | Best balance |
| `meta-llama/llama-3.3-70b-instruct` | Most stable |
| `qwen/qwen-2.5-coder-32b-instruct` | Coding specialist |
| `deepseek/deepseek-r1` | Reasoning/math |
| `google/gemma-3-12b-it` | Fastest |
| `openai/gpt-4o-mini` | Reliable general |
| `anthropic/claude-3-haiku-20240307` | Natural chat |

### Alibaba Cloud Models (6)
| Model | Use Case |
|-------|----------|
| `qwen3-coder-480b-a35b-instruct` | Best coder (480B) |
| `qwen3.5-397b-a17b` | Most powerful (397B) |
| `qwen3-max` | Flagship |
| `qwen3-235b-a22b` | Reasoning (235B) |
| `qwen3-coder-plus` | Coding expert |
| `qwen-plus` | Fast balanced |

---

## 🛠️ Skills (14 Available)

| Skill | Description |
|-------|-------------|
| `web-dev` | React, Vue, Next.js, JavaScript |
| `data-science` | pandas, numpy, matplotlib, ML |
| `devops` | Docker, Kubernetes, CI/CD, cloud |
| `security` | Vulnerability scanning, code audit |
| `api-dev` | REST, GraphQL, OpenAPI |
| `mobile-dev` | React Native, Flutter |
| `ml-ops` | ML training, deployment, monitoring |
| `database` | SQL, NoSQL, migrations |
| `code-review` | Best practices, refactoring |
| `testing` | Unit, integration, e2e, TDD |
| `documentation` | README, API docs, diagrams |
| `git-workflow` | Branching, merging, CI |
| `blockchain` | Solidity, smart contracts, Web3 |
| `game-dev` | Unity, Godot, web games |

---

## 📱 Mobile Access

The web interface is **fully mobile responsive**:
- Open https://clean-claw-ai.vercel.app on any device
- Works on iOS Safari, Android Chrome
- Touch-optimized interface
- File upload supported

---

## ❓ Troubleshooting

### Web Chat Issues

**Problem:** Network error
- **Solution:** Check internet connection, try refreshing the page

**Problem:** Blank responses
- **Solution:** Clear browser cache, try incognito mode

**Problem:** Lost chats on reload
- **Solution:** Chats are saved to browser storage. Check if localStorage is enabled.

### Chrome Extension Issues

**Problem:** "Cannot connect to Ollama"
- **Solution:** Extension now uses Cloud API by default. Set `USE_CLOUD_API = true` in `sidepanel.js`

**Problem:** Extension not loading
- **Solution:** Enable Developer mode, reload the extension

### VS Code Extension Issues

**Problem:** Extension not appearing
- **Solution:** Restart VS Code, check if installed in correct VS Code instance

**Problem:** API errors
- **Solution:** Check `claw.apiMode` is set to `cloud` in settings

### CLI Issues

**Problem:** `claw: command not found`
- **Solution:** Run `pip install -e .` in the claw-agent directory

**Problem:** Import errors
- **Solution:** Ensure you're in the correct directory: `cd c:\Users\Sinwa\Pictures\ClaudeAI\claw-agent`

---

## 🚀 Quick Start Summary

### Fastest Way to Start
1. Open https://clean-claw-ai.vercel.app
2. Start chatting immediately!

### For Developers
1. **CLI:** `cd claw-agent && claw`
2. **Chrome:** Load unpacked extension from `chrome-extension/` folder
3. **VS Code:** Install from VSIX file

### All Platforms Share
- ✅ Same 14 AI models
- ✅ Same 14 skills
- ✅ Same OpenRouter + Alibaba Cloud APIs
- ✅ Session persistence
- ✅ File upload support
- ✅ Mobile responsive

---

## 📞 Support

For issues or questions:
- Check the troubleshooting section above
- Review the configuration in `.env.local`
- Verify API keys are valid
- Check internet connectivity

---

**Built with ❤️ — 14 AI models, 2 providers, 0 cost** 🦞✨
