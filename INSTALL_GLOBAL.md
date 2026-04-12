# 🦅 Claw AI - Global Installation Guide

Install and use Claw AI CLI from **any computer** in under 2 minutes!

---

## 🚀 Quick Install (Any PC)

### Option 1: One-Line Install (Recommended)

Open a terminal and run:

```bash
pip install git+https://github.com/kdhdjdk090/claw-agent.git
```

Then just type:
```bash
claw
```

### Option 2: Manual Install

```bash
# 1. Clone the repository
git clone https://github.com/kdhdjdk090/claw-agent.git
cd claw-agent

# 2. Install
pip install -e .

# 3. Run
claw
```

---

## 📋 Prerequisites

### Windows
- **Python 3.10+**: Download from https://python.org
- **Git**: Download from https://git-scm.com

### macOS/Linux
- Python is usually pre-installed
- Install Git: `sudo apt install git` (Linux) or `brew install git` (macOS)

---

## 🔧 After Installation

### 1. Start Ollama (for local mode)

```bash
# Windows
ollama serve

# macOS/Linux
ollama serve
```

### 2. Pull a Model (if you don't have one)

```bash
# Best model (cloud proxy)
ollama pull deepseek-v3.1:671b-cloud

# Or local model
ollama pull gemma4:latest
```

### 3. Run Claw AI

```bash
claw
```

---

## 🌐 Using Without Ollama (Cloud Mode)

If you want to use the **DeepSeek Cloud API** instead of local Ollama:

### Windows (PowerShell)
```powershell
$env:DEEPSEEK_API_KEY="your-api-key-here"
claw
```

### Windows (cmd)
```cmd
set DEEPSEEK_API_KEY=your-api-key-here
claw
```

### Linux/macOS
```bash
export DEEPSEEK_API_KEY="your-api-key-here"
claw
```

---

## 💻 Usage Examples

### Interactive Mode (Full REPL)
```bash
claw
```

### One-Shot Mode
```bash
claw prompt "Write a Python function to sort a list"
```

### Auto-Approve Mode (No permission prompts)
```bash
claw --yolo prompt "Create a new Python project"
```

### Use Specific Model
```bash
claw -m deepseek-v3.1:671b-cloud
claw -m gemma4:latest
claw -m qwen2.5:7b
```

---

## 🎯 Available Slash Commands

Once inside the CLI, type:

```
/help              Show all commands
/tools             List all 26 tools
/cost              Token usage stats
/status            Workspace status
/model             Show current model
/models            List available models
/clear             Clear conversation
/save              Save session
/sessions          List sessions
/resume <id>       Resume session
/diff              Git diff
/config            Agent config
/permissions       Permission mode
/memory            Context usage
/doctor            Diagnostics
/version           Version info
/quit              Exit
```

---

## 🔧 Troubleshooting

### "claw: command not found"
**Fix:** Add Python Scripts to PATH
```bash
# Windows
set PATH=%PATH%;%APPDATA%\Python\Python313\Scripts

# Linux/macOS
export PATH="$HOME/.local/bin:$PATH"
```

### "Ollama is not running"
**Fix:** Start Ollama
```bash
ollama serve
```

### "Model not found"
**Fix:** Pull the model
```bash
ollama pull deepseek-v3.1:671b-cloud
```

### "Module not found" errors
**Fix:** Reinstall
```bash
pip install --upgrade git+https://github.com/kdhdjdk090/claw-agent.git
```

---

## 🌍 Use from Multiple PCs

The CLI is now available on any machine where you run the install command.

### Sync Sessions Across PCs

Your sessions are saved in:
- **Windows:** `%USERPROFILE%\.claw-agent\sessions\`
- **Linux/macOS:** `~/.claw-agent/sessions/`

To sync sessions, copy this folder between machines or use a cloud sync tool.

---

## 📊 Quick Reference Card

```
┌─────────────────────────────────────────┐
│  🦅 Claw AI - Quick Commands            │
├─────────────────────────────────────────┤
│  Install:  pip install git+URL          │
│  Start:    claw                         │
│  Help:     /help                        │
│  One-shot: claw prompt "question"       │
│  Yolo:     claw --yolo prompt "task"    │
│  Model:    claw -m gemma4:latest        │
│  Quit:     /quit                        │
└─────────────────────────────────────────┘
```

---

**Status: Ready for global use! 🌍**
