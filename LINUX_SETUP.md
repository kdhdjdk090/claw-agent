# 🐧 Claw AI CLI - Linux Installation Guide

## ✅ Use DeepSeek's LARGEST Model from Any Linux PC!

**Model:** `deepseek-reasoner` (DeepSeek's most powerful model with advanced reasoning)  
**No Ollama Required!** Just install, set API key, and run!

---

## 🚀 Quick Install (Ubuntu/Debian)

### Step 1: Install Python & pip

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git

# Fedora/RHEL
sudo dnf install -y python3 python3-pip git

# Arch Linux
sudo pacman -S python python-pip git
```

### Step 2: Install Claw AI

```bash
# Install globally
pip3 install git+https://github.com/kdhdjdk090/claw-agent.git

# Or install in virtual environment (recommended)
mkdir -p ~/claw-ai && cd ~/claw-ai
python3 -m venv venv
source venv/bin/activate
pip install git+https://github.com/kdhdjdk090/claw-agent.git
```

### Step 3: Set DeepSeek API Key

```bash
# Temporary (current session only)
export DEEPSEEK_API_KEY="your-api-key-here"

# OR make it permanent (recommended)
echo 'export DEEPSEEK_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc

# For zsh users
echo 'export DEEPSEEK_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### Step 4: Run Claw AI!

```bash
claw
```

**That's it!** No Ollama, no GPU setup needed! ✨

---

## 🎯 Verify Installation

```bash
# Check if claw is installed
which claw
claw --help

# Verify API key is set
echo $DEEPSEEK_API_KEY

# Test one-shot mode
claw --yolo prompt "Say hello and tell me what model you're using"
```

You should see:
```
✓ Cloud Mode (using DeepSeek API)
```

---

## 💬 Usage Examples

### Interactive Mode (Full REPL)
```bash
claw
```

### One-Shot Mode
```bash
claw prompt "Write a Python function to calculate fibonacci"
```

### Auto-Approve Mode
```bash
claw --yolo prompt "Create a REST API with FastAPI"
```

### Use Specific Model
```bash
# Use DeepSeek's reasoner (largest, most capable)
claw -m deepseek-reasoner

# Use DeepSeek chat (fast, still very capable)
claw -m deepseek-chat
```

---

## 📊 Available DeepSeek Models

| Model | Capabilities | Speed | Use Case |
|-------|-------------|-------|----------|
| **deepseek-reasoner** ⭐ | Largest, best reasoning | Slower | Complex coding, analysis |
| **deepseek-chat** | Fast, very capable | Fast | General coding, Q&A |
| **deepseek-coder** | Code specialized | Fast | Programming tasks |

**Default:** `deepseek-reasoner` (largest model)

---

## 🔧 Advanced Setup

### Create Systemd Service (Auto-start)

Create a service file:
```bash
sudo nano /etc/systemd/system/claw-ai.service
```

Add this content:
```ini
[Unit]
Description=Claw AI Agent
After=network.target

[Service]
Type=simple
User=$USER
Environment=DEEPSEEK_API_KEY=your-api-key-here
ExecStart=/usr/bin/python3 -m claw_agent.cli --yolo
WorkingDirectory=/home/$USER
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable claw-ai
sudo systemctl start claw-ai
sudo systemctl status claw-ai
```

### Create Alias for Easy Access

Add to `~/.bashrc` or `~/.zshrc`:
```bash
# Claw AI aliases
alias claw='DEEPSEEK_API_KEY="your-key" claw'
alias claw-fast='claw -m deepseek-chat'
alias claw-smart='claw -m deepseek-reasoner'
```

Then:
```bash
source ~/.bashrc
claw          # Uses reasoner (default)
claw-fast     # Uses chat (faster)
claw-smart    # Explicit reasoner
```

---

## 🌐 Use from Multiple Linux Machines

The same setup works on any Linux machine:

**Laptop:**
```bash
export DEEPSEEK_API_KEY="your-key"
pip3 install git+https://github.com/kdhdjdk090/claw-agent.git
claw
```

**Server:**
```bash
export DEEPSEEK_API_KEY="your-key"
pip3 install git+https://github.com/kdhdjdk090/claw-agent.git
claw --yolo prompt "Analyze this codebase"
```

**Workstation:**
```bash
# Just run claw!
claw
```

---

## 🔍 Troubleshooting

### "command not found: claw"
```bash
# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Or use full path
python3 -m claw_agent.cli
```

### "ModuleNotFoundError"
```bash
# Reinstall
pip3 install --upgrade --force-reinstall git+https://github.com/kdhdjdk090/claw-agent.git
```

### "API key not configured"
```bash
# Check if key is set
echo $DEEPSEEK_API_KEY

# Set it
export DEEPSEEK_API_KEY="your-key-here"
```

### "Connection timeout"
```bash
# Test API connectivity
curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
     https://api.deepseek.com/v1/models

# Check firewall
sudo ufw allow out 443/tcp
```

---

## 🎯 Quick Reference Card

```bash
┌─────────────────────────────────────────────────┐
│  🦅 Claw AI - Linux Quick Start                 │
├─────────────────────────────────────────────────┤
│  Install:                                       │
│    pip3 install git+URL                         │
│                                                 │
│  Set API Key:                                   │
│    export DEEPSEEK_API_KEY="your-key"           │
│    echo 'export ...' >> ~/.bashrc               │
│                                                 │
│  Run:                                           │
│    claw              # Interactive               │
│    claw prompt "Q"   # One-shot                  │
│    claw --yolo ...   # Auto-approve              │
│                                                 │
│  Models:                                        │
│    deepseek-reasoner ⭐  (largest, default)      │
│    deepseek-chat       (faster)                  │
└─────────────────────────────────────────────────┘
```

---

## 📝 Docker Usage (Optional)

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

RUN pip install git+https://github.com/kdhdjdk090/claw-agent.git

ENV DEEPSEEK_API_KEY=""

ENTRYPOINT ["claw"]
```

Build and run:
```bash
docker build -t claw-ai .
docker run -it --env DEEPSEEK_API_KEY="your-key" claw-ai
```

---

## ✨ What You Get

✅ **DeepSeek's LARGEST model** (`deepseek-reasoner`)  
✅ **No Ollama required**  
✅ **No GPU/CPU setup**  
✅ **No model downloads**  
✅ **Works on any Linux distro**  
✅ **All 26 tools available**  
✅ **All slash commands working**  
✅ **Session persistence**  
✅ **Token tracking**  
✅ **Systemd service support**  
✅ **Docker support**  

---

## ❓ FAQ

**Q: Which model does it use?**  
A: `deepseek-reasoner` by default (DeepSeek's largest, most capable model)

**Q: Can I use a faster model?**  
A: Yes! Run `claw -m deepseek-chat` for faster responses

**Q: Do I need a GPU?**  
A: No! All inference happens on DeepSeek's cloud servers

**Q: Does it work on Raspberry Pi?**  
A: Yes! Since it uses the cloud API, any device with Python works

**Q: How do I check my API usage?**  
A: Visit https://platform.deepseek.com and check your dashboard

---

**Status: ✅ READY FOR ANY LINUX MACHINE!**

Install once, use everywhere! 🐧🚀
