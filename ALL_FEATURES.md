# 🦅 Claw AI - Complete Feature List

## ✅ ALL Claude Code Features + More!

---

## 🎯 Core Features (Like Claude Code)

### 1. Skills System
```bash
/skills                    # List all skills
/skill install web-dev     # Install web development skill
/skill install data-science # Install data science skill
/skill install devops      # Install DevOps skill
/skill install security    # Install security skill
/skill install api-dev     # Install API development skill
/skill uninstall <name>    # Remove a skill
```

### 2. MCP Server Support
```bash
/mcp                       # List MCP servers
/mcp add <name> <cmd>      # Add MCP server
/mcp remove <name>         # Remove MCP server
```

### 3. Approval Modes
```bash
/approval                  # View current mode
/approval auto             # Auto-approve all (yolo)
/approval default          # Ask on dangerous tools
/approval ask              # Always ask
```

---

## 💻 Complete Command Reference

### Core Commands
- `/help` - Show all commands
- `/model <name>` - Switch AI model
- `/models` - List available models
- `/tools` - List all 26 tools
- `/cost` - Token usage & timing
- `/compact` - Compress conversation

### Session Management
- `/save` - Save current session
- `/sessions` - List saved sessions
- `/resume <id>` - Resume session
- `/continue` - Quick-resume last
- `/delete <id>` - Delete session
- `/export` - Export to markdown

### Workspace & Git
- `/diff` - Git diff
- `/status` - Workspace info
- `/config` - Agent config
- `/permissions` - Permission mode
- `/memory` - Context usage
- `/undo` - Undo file write
- `/init` - Generate .claw config

### Skills & MCP ✨
- `/skills` - List skills
- `/skill install <name>` - Install skill
- `/skill uninstall <name>` - Uninstall skill
- `/mcp` - List MCP servers
- `/mcp add <name> <cmd>` - Add MCP server
- `/mcp remove <name>` - Remove MCP server

### Settings ✨
- `/approval <mode>` - Set approval mode

### Diagnostics
- `/version` - Version info
- `/doctor` - Run diagnostics
- `/bug` - Debug info

### Control
- `/clear` - Clear conversation
- `/quit` - Exit

---

## 🔧 Installation (Any PC)

### Windows:
```powershell
pip install git+https://github.com/kdhdjdk090/claw-agent.git
$env:DEEPSEEK_API_KEY="your-key"
claw
```

### Linux:
```bash
pip3 install git+https://github.com/kdhdjdk090/claw-agent.git
export DEEPSEEK_API_KEY="your-key"
claw
```

### macOS:
```bash
pip3 install git+https://github.com/kdhdjdk090/claw-agent.git
export DEEPSEEK_API_KEY="your-key"
claw
```

---

## 🌐 Web UI (No Install)

**URL:** https://clean-claw-ai.vercel.app

Commands:
- `/help` - Show help
- `/clear` - Clear chat
- `/model <name>` - Switch model
- `/status` - Show status

---

## 📊 Model Options

| Model | Use Case |
|-------|----------|
| deepseek-reasoner | Largest, most capable (default) |
| deepseek-chat | Fast, very capable |
| deepseek-coder | Code specialized |

---

## ✅ Status: Production Ready!

- ✅ All Claude Code features
- ✅ Skills system
- ✅ MCP support
- ✅ Approval modes
- ✅ 26 tools
- ✅ Cloud API (no Ollama needed)
- ✅ Works on Windows, Linux, macOS
- ✅ Web UI available

**Ready to use!** 🚀
