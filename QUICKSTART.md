# 🦅 Claw AI - Quick Start Guide

## ✅ Setup Complete!

The `claw` command now opens the **Python CLI** with all slash commands and DeepSeek-R1 support.

---

## 🚀 How to Start Claw AI

### Option 1: From Anywhere (Recommended)
```bash
claw
```

### Option 2: From Project Directory
```bash
cd c:\Users\Sinwa\Pictures\ClaudeAI\claw-agent
claw
```

### Option 3: Double-click Shortcut
Double-click `start-claw.cmd` in the project folder.

---

## 💬 Using Slash Commands

Once Claw AI starts, you'll see the REPL prompt. Type these commands:

### Basic Commands
```
/help              Show all available commands
/tools             List all 26 available tools
/cost              Show token usage and timing stats
/status            Show workspace status
/config            Show current agent configuration
```

### Model Commands
```
/model             Show current model
/model deepseek-r1:671b   Switch to highest model
/models            List all available models
/doctor            Run diagnostics
```

### Session Commands
```
/save              Save current session
/sessions          List saved sessions
/resume <id>       Resume a saved session
/continue          Quick-resume most recent session
/export            Export conversation to markdown
```

### Workspace Commands
```
/diff              Show git diff of changes
/permissions       Show or switch permissions mode
/memory            Show context window usage
/undo              Undo last file write
```

### Control
```
/clear             Clear conversation
/quit or /exit     Exit Claw AI
```

---

## 🎯 Example Session

```
C:\Users\Sinwa>claw

╭────────────────────────────────────────────────────────────╮
│ ✨ Claw Agent v0.1.0                                       │
│                                                            │
│ C:\Users\Sinwa\Projects                                    │
│ Model: deepseek-r1:671b                                    │
│ 26 tools available                                         │
│                                                            │
│ Type /help for commands                                    │
╰────────────────────────────────────────────────────────────╯

myproject ❯ /help

  Slash Commands

  Core
    /help                     Show this help
    /model <name>             Switch model
    /models                   List available models
    /tools                    List all 26 tools
    /cost                     Token usage & timing stats
    /compact                  Compress conversation history

  ... (more commands)

myproject ❯ Write a Python function to calculate fibonacci

🔍 Read(memory.md)
  ✓ read_file 245ms

🔧 Write(solution.py)
  ✓ write_file 189ms

✅ Done! I've created solution.py with the fibonacci function.

myproject ❯ /cost

  Tokens: 1,234 prompt, 567 completion
  Cost: FREE (local Ollama)

myproject ❯ /quit
 ─ Goodbye!
```

---

## 🔧 Troubleshooting

### "Ollama is not running"
```bash
ollama serve
```

### "Model not found"
```bash
ollama pull deepseek-r1:671b
```

### "Command not found: claw"
Make sure `C:\nvm4w\nodejs` is in your PATH (it should be by default).

### Want to use a different model?
```bash
claw -m deepseek-r1:32b    # Medium quality
claw -m deepseek-r1:14b    # Fast
claw -m deepseek-r1:8b     # Very fast
```

---

## 🌐 Web UI Alternative

You can also use the web interface:
```bash
cd c:\Users\Sinwa\Pictures\ClaudeAI\claw-agent
# Open index.html in your browser
```

**Web UI Commands:**
- `/help` - Show help modal
- `/clear` - Clear conversation
- `/model <name>` - Switch model
- `/status` - Show status

**Note:** Web UI has limited commands. Use CLI for full features.

---

## 📊 Model Comparison

| Model | Quality | RAM/VRAM | Speed |
|-------|---------|----------|-------|
| deepseek-r1:671b | ⭐⭐⭐⭐⭐ | 40+ GB | Slow |
| deepseek-r1:32b | ⭐⭐⭐⭐ | 20+ GB | Medium |
| deepseek-r1:14b | ⭐⭐⭐ | 10+ GB | Fast |
| deepseek-r1:8b | ⭐⭐ | 6+ GB | Very Fast |

**Default:** deepseek-r1:671b (highest quality)

---

## ✨ What Was Fixed

1. ✅ Removed Node.js `claw` package (no slash commands)
2. ✅ Created wrapper to call Python CLI
3. ✅ Updated default model to `deepseek-r1:671b`
4. ✅ Added slash command support to web UI
5. ✅ All 26 tools working
6. ✅ Session persistence working
7. ✅ Token tracking working

---

**Now just type `claw` and start coding!** 🎉
