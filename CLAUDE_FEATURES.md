# 🦅 Claw AI - Complete Claude Code Feature Guide

## ✅ All Claude Features Now Available!

Claw AI now has **ALL** Claude Code features plus more!

---

## 🎯 New Features Added

### 1. **Skills System** (Like Claude Skills)

Install specialized toolkits for different tasks:

```bash
# List available skills
/skills

# Install a skill
/skill install web-dev
/skill install data-science
/skill install devops
/skill install security
/skill install api-dev

# Uninstall a skill
/skill uninstall web-dev
```

**Available Skills:**
- **web-dev** - Web development (React, Vue, HTML, CSS, JS)
- **data-science** - Data analysis (pandas, numpy, ML, visualizations)
- **devops** - DevOps tools (Docker, K8s, CI/CD, cloud)
- **security** - Security auditing and code review
- **api-dev** - API development (REST, GraphQL, OpenAPI)

---

### 2. **MCP Server Support** (Model Context Protocol)

Connect external tools and services:

```bash
# List MCP servers
/mcp

# Add an MCP server
/mcp add filesystem npx -y @modelcontextprotocol/server-filesystem /path/to/dir

# Remove an MCP server
/mcp remove filesystem
```

**Popular MCP Servers:**
- Filesystem access
- Database connections
- Git operations
- Web scraping
- Custom tools

---

### 3. **Approval Modes** (Like Claude Code)

Control how tool calls are approved:

```bash
# View current mode
/approval

# Set approval mode
/approval auto     # Auto-approve all (yolo mode)
/approval default  # Ask on dangerous tools
/approval ask      # Always ask for confirmation
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

## 🚀 Installation (Any PC)

### Windows:
```powershell
pip install git+https://github.com/kdhdjdk090/claw-agent.git
$env:DEEPSEEK_API_KEY="your-key-here"
claw
```

### Linux:
```bash
pip3 install git+https://github.com/kdhdjdk090/claw-agent.git
export DEEPSEEK_API_KEY="your-key-here"
claw
```

### macOS:
```bash
pip3 install git+https://github.com/kdhdjdk090/claw-agent.git
export DEEPSEEK_API_KEY="your-key-here"
claw
```

---

## 💡 Usage Examples

### Example 1: Web Development with Skills
```bash
# Install web-dev skill
/skill install web-dev

# Now Claw has web development capabilities
"Create a React component with TypeScript for a todo list"
```

### Example 2: Data Science Workflow
```bash
# Install data-science skill
/skill install data-science

# Analyze data
"Analyze this CSV file and create visualizations"
```

### Example 3: DevOps Automation
```bash
# Install devops skill
/skill install devops

# Create Docker setup
"Dockerize this Node.js application"
```

### Example 4: Security Audit
```bash
# Install security skill
/skill install security

# Run security audit
"Perform a security audit of this codebase"
```

### Example 5: Using MCP Servers
```bash
# Add filesystem MCP server
/mcp add files npx -y @modelcontextprotocol/server-filesystem /home/user/projects

# Now Claw can use filesystem tools via MCP
"List all Python files in /home/user/projects"
```

---

## 🔧 Configuration Files

### Skills Location:
```
~/.claw-agent/skills/
├── web-dev/
│   └── skill.json
├── data-science/
│   └── skill.json
└── devops/
    └── skill.json
```

### MCP Configuration:
```
~/.claw-agent/mcp/
└── config.json
```

### Sessions:
```
~/.claw-agent/sessions/
└── *.json
```

---

##  CLI Interface

When you start Claw, you'll see:

```
✓ Cloud Mode (using DeepSeek API)

╭────────────────────────────────────────────────────────────╮
│  Claw AI v0.2.0                                          │
│                                                            │
│ /home/user/projects                                        │
│ ☁️ Cloud • deepseek-reasoner                               │
│ 26 tools available                                         │
│                                                            │
│ 💡 Type /help for commands                                 │
│  Try: Write a Python function                              │
╰────────────────────────────────────────────────────────────╯

projects ❯
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
A: Skills are installable capability packs that give Claw specialized knowledge and tools for specific domains (web dev, data science, etc.)

**Q: What is MCP?**  
A: Model Context Protocol allows Claw to connect to external tools and services through a standardized interface.

**Q: Do I need Ollama?**  
A: No! Set `DEEPSEEK_API_KEY` and Claw works with the cloud API. No local setup needed.

**Q: Can I create custom skills?**  
A: Yes! Create a directory in `~/.claw-agent/skills/` with a `skill.json` manifest.

**Q: How do I add an MCP server?**  
A: Use `/mcp add <name> <command>` to configure an MCP server.

---

**Status: ✅ All Claude Code Features + More!**

Claw AI now has everything Claude Code has, plus additional features! 🚀
