# 🐧 Claw AI - Linux Installation & Quick Start

## ✅ Install in 3 Steps (No Ollama Required!)

### Step 1: Install Claw AI
```bash
pip3 install --force-reinstall --no-cache-dir git+https://github.com/kdhdjdk090/claw-agent.git
```

### Step 2: Set Your DeepSeek API Key
```bash
export DEEPSEEK_API_KEY="sk-41fba01c85af484e8623d4d96261fa58"
```

**Make it permanent:**
```bash
echo 'export DEEPSEEK_API_KEY="sk-41fba01c85af484e8623d4d96261fa58"' >> ~/.bashrc
source ~/.bashrc
```

### Step 3: Run Claw!
```bash
claw
```

---

## 🎯 What You Get

✅ **All Claude Code Features:**
- Skills system (web-dev, data-science, devops, security, api-dev)
- MCP server support
- Approval modes (auto/default/ask)
- Session management
- 26 powerful tools

✅ **Cloud-Powered:**
- Uses DeepSeek's largest model (deepseek-reasoner)
- No Ollama needed
- No GPU required
- No local setup

✅ **Professional Interface:**
- Beautiful Claude-like banner
- Enhanced /help with all commands
- Color-coded output
- Token tracking

---

## 💬 Test It

```bash
# Start Claw
claw

# Try slash commands
/help
/skills
/skill install web-dev
/mcp
/approval

# Ask a question
"Write a Python function to calculate fibonacci"
```

---

## 🔧 Available Skills

```bash
# Install any skill
/skill install web-dev       # Web development
/skill install data-science  # Data science & ML
/skill install devops        # Docker, K8s, CI/CD
/skill install security      # Security auditing
/skill install api-dev       # API development
```

---

## 📋 All Slash Commands

```
/help                      Show all commands
/skills                    List installed skills
/skill install <name>      Install a skill
/skill uninstall <name>    Remove a skill
/mcp                       List MCP servers
/mcp add <name> <cmd>      Add MCP server
/approval <mode>           Set approval mode
/model <name>              Switch model
/tools                     List all 26 tools
/cost                      Token usage
/save                      Save session
/sessions                  List sessions
/quit                      Exit
```

---

## 🌐 Web UI Alternative

No installation needed! Just open:
**https://clean-claw-ai.vercel.app**

---

## ❓ Troubleshooting

**"command not found: claw"**
```bash
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

**"API key not configured"**
```bash
export DEEPSEEK_API_KEY="your-key-here"
```

**"Module not found"**
```bash
pip3 install --force-reinstall git+https://github.com/kdhdjdk090/claw-agent.git
```

---

**Status: ✅ Ready for Linux!**

Just install and run! 🚀
