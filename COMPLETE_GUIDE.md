# 🦅 Claw AI - Complete Installation & Usage Guide

## ✅ **ALL Claude Code Features Added!**

Claw AI now has everything Claude Code has, plus more!

---

## 🚀 Quick Install (Linux/Any PC)

### **Step 1: Install**
```bash
pip3 install --force-reinstall --no-cache-dir git+https://github.com/kdhdjdk090/claw-agent.git
```

### **Step 2: Set API Key**
```bash
export DEEPSEEK_API_KEY="sk-41fba01c85af484e8623d4d96261fa58"
```

### **Step 3: Run**
```bash
claw
```

**That's it!** No Ollama, no GPU, no local setup needed!

---

## 🎯 What's New - All Claude Features

### ✨ 1. Skills System
Install specialized capabilities:
```bash
/skills                          # List all skills
/skill install web-dev           # Web development toolkit
/skill install data-science      # Data science & ML
/skill install devops            # Docker, K8s, CI/CD
/skill install security          # Security auditing
/skill install api-dev           # API development
/skill uninstall <name>          # Remove a skill
```

### ✨ 2. MCP Server Support
Connect external tools:
```bash
/mcp                             # List MCP servers
/mcp add <name> <command>        # Add MCP server
/mcp remove <name>               # Remove MCP server
```

### ✨ 3. Approval Modes (Like Claude)
Control tool execution:
```bash
/approval                        # View current mode
/approval auto                   # Auto-approve all
/approval default                # Ask on dangerous tools
/approval ask                    # Always ask
```

---

## 📋 Complete Command Reference

### Core Commands
```
/help                      Show all commands
/model <name>              Switch AI model
/models                    List available models
/tools                     List all 26 tools
/cost                      Token usage & timing
/compact                   Compress conversation
```

### Session Management
```
/save                      Save current session
/sessions                  List saved sessions
/resume <id>               Resume session by ID
/continue                  Quick-resume last session
/delete <id>               Delete a session
/export                    Export to markdown
```

### Workspace & Git
```
/diff                      Git diff of changes
/status                    Workspace & project info
/config                    Agent configuration
/permissions [mode]        Permission mode
/memory                    Context window usage
/undo                      Undo last file write
/init                      Generate .claw config
```

### Skills & MCP ✨ NEW
```
/skills                    List installed skills
/skill install <name>      Install a skill
/skill uninstall <name>    Remove a skill
/mcp                       List MCP servers
/mcp add <name> <cmd>      Add MCP server
/mcp remove <name>         Remove MCP server
```

### Settings ✨ NEW
```
/approval <mode>           Set approval mode (auto/default/ask)
```

### Diagnostics
```
/version                   Version & platform info
/doctor                    Run system diagnostics
/bug                       Debug information
```

### Control
```
/clear                     Clear conversation
/quit                      Exit (also /exit, /q)
```

---

## 💡 Usage Examples

### Example 1: Web Development
```bash
claw
/skill install web-dev
"Create a React component with TypeScript for a todo list"
```

### Example 2: Data Science
```bash
claw
/skill install data-science
"Analyze this CSV file and create visualizations"
```

### Example 3: DevOps
```bash
claw
/skill install devops
"Dockerize this Node.js application"
```

### Example 4: Security
```bash
claw
/skill install security
"Perform a security audit of this codebase"
```

### Example 5: MCP Servers
```bash
claw
/mcp add files npx -y @modelcontextprotocol/server-filesystem /path/to/dir
"List all Python files in /path/to/dir"
```

---

## 🌐 Web UI Alternative

No installation needed! Just open:
**https://clean-claw-ai.vercel.app**

Web UI commands:
- `/help` - Show help
- `/clear` - Clear chat
- `/model <name>` - Switch model
- `/status` - Show status

---

## 🔧 Configuration Files

### Skills Location:
```
~/.claw-agent/skills/
├── web-dev/skill.json
├── data-science/skill.json
└── devops/skill.json
```

### MCP Configuration:
```
~/.claw-agent/mcp/config.json
```

### Sessions:
```
~/.claw-agent/sessions/*.json
```

---

## 📊 Feature Comparison

| Feature | Claude Code | Claw AI |
|---------|------------|---------|
| Skills System | ✅ | ✅ |
| MCP Support | ✅ | ✅ |
| Approval Modes | ✅ | ✅ |
| Session Management | ✅ | ✅ |
| Token Tracking | ✅ | ✅ |
| Git Integration | ✅ | ✅ |
| File Editing | ✅ | ✅ |
| Shell Commands | ✅ | ✅ |
| Web Search | ✅ | ✅ |
| Cloud API | ✅ | ✅ |
| Local Mode | ❌ | ✅ |
| 26 Tools | ❌ | ✅ |
| Free to Use | ❌ | ✅ |

---

## ❓ FAQ

**Q: What are skills?**  
A: Skills are installable capability packs that give Claw specialized knowledge and tools for specific domains.

**Q: What is MCP?**  
A: Model Context Protocol allows Claw to connect to external tools and services through a standardized interface.

**Q: Do I need Ollama?**  
A: No! Set `DEEPSEEK_API_KEY` and Claw works with the cloud API. No local setup needed.

**Q: Can I create custom skills?**  
A: Yes! Create a directory in `~/.claw-agent/skills/` with a `skill.json` manifest.

**Q: How do I add an MCP server?**  
A: Use `/mcp add <name> <command>` to configure an MCP server.

**Q: Which model does it use?**  
A: `deepseek-reasoner` (DeepSeek's largest, most capable model)

**Q: Can I use a faster model?**  
A: Yes! Use `/model deepseek-chat` for faster responses.

---

## 🎯 Quick Start on Your Linux Server

```bash
# Install
pip3 install --force-reinstall --no-cache-dir git+https://github.com/kdhdjdk090/claw-agent.git

# Set API key
export DEEPSEEK_API_KEY="sk-41fba01c85af484e8623d4d96261fa58"

# Run
claw

# Try commands
/help
/skills
/skill install web-dev
/mcp
/approval
```

---

**Status: ✅ Production Ready!**

All Claude Code features + more! Ready to use on any PC! 🚀
