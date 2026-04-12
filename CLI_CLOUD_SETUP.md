# 🌍 Claw AI CLI - Use from ANY PC (No Ollama Required!)

## ✅ Now Uses DeepSeek API Directly!

The CLI can now connect to the **DeepSeek Cloud API** - no local Ollama needed!

---

## 🚀 Quick Install & Setup (Any PC)

### Step 1: Install (One Command)

```bash
pip install git+https://github.com/kdhdjdk090/claw-agent.git
```

### Step 2: Set Your DeepSeek API Key

**Windows (PowerShell):**
```powershell
$env:DEEPSEEK_API_KEY="your-api-key-here"
```

**Windows (cmd):**
```cmd
set DEEPSEEK_API_KEY=your-api-key-here
```

**Linux/macOS:**
```bash
export DEEPSEEK_API_KEY="your-api-key-here"
```

### Step 3: Run Claw!

```bash
claw
```

**That's it! No Ollama, no GPU, no local setup needed!**

---

## 📊 Two Modes

| Mode | Requirements | Command |
|------|-------------|---------|
| **☁️ Cloud Mode** (Recommended) | Just API key | Set `DEEPSEEK_API_KEY` → Run `claw` |
| **💻 Local Mode** | Ollama running locally | Run `ollama serve` → Run `claw` |

**Cloud mode is automatic** - if `DEEPSEEK_API_KEY` is set, it uses the cloud API!

---

## ✨ What You Get

✅ **No Ollama installation needed**  
✅ **No local GPU required**  
✅ **No model downloads**  
✅ **Works on any PC**  
✅ **Uses DeepSeek's most powerful model**  
✅ **All 26 tools available**  
✅ **All slash commands working**  
✅ **Session persistence**  
✅ **Token tracking**  

---

## 💬 Usage Examples

### Interactive Mode
```bash
# Set API key (Windows PowerShell)
$env:DEEPSEEK_API_KEY="your-key-here"

# Run Claw
claw
```

### One-Shot Mode
```bash
$env:DEEPSEEK_API_KEY="your-key-here"
claw prompt "Write a Python function to calculate fibonacci"
```

### Yolo Mode (Auto-approve tools)
```bash
$env:DEEPSEEK_API_KEY="your-key-here"
claw --yolo prompt "Create a new Python project structure"
```

---

## 🎯 Slash Commands (All Working!)

Once inside the CLI:

```
/help              Show all commands
/tools             List all 26 tools
/cost              Token usage stats
/status            Workspace status
/model             Show current model
/clear             Clear conversation
/save              Save session
/sessions          List sessions
/resume <id>       Resume session
/doctor            Diagnostics
/quit              Exit
```

---

## 🔧 Make API Key Permanent (Windows)

To avoid setting it every time:

```powershell
# Set permanently for your user
[System.Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "your-key-here", "User")

# Then restart terminal and just type:
claw
```

---

## 🌐 Use from Multiple PCs

The same API key works on any machine:

**PC 1:**
```powershell
$env:DEEPSEEK_API_KEY="your-key"
claw
```

**PC 2:**
```powershell
$env:DEEPSEEK_API_KEY="your-key"
claw
```

**Laptop:**
```bash
export DEEPSEEK_API_KEY="your-key"
claw
```

---

## ❓ FAQ

**Q: Do I need Ollama?**  
A: No! Just set `DEEPSEEK_API_KEY` and you're done.

**Q: Which model does it use?**  
A: `deepseek-chat` (DeepSeek's most capable model)

**Q: Can I use it offline?**  
A: No, cloud mode requires internet. For offline use, use local Ollama mode.

**Q: Is it fast?**  
A: Yes! DeepSeek's cloud API is optimized for fast responses.

**Q: How much does it cost?**  
A: Depends on your DeepSeek API plan. Check your usage at https://platform.deepseek.com

---

## 📝 Quick Reference

```bash
# Install
pip install git+https://github.com/kdhdjdk090/claw-agent.git

# Set API key (Windows PowerShell)
$env:DEEPSEEK_API_KEY="your-key-here"

# Run
claw

# One-shot
claw prompt "Your question here"

# Check status
claw --yolo prompt "Say hello"
```

---

**Status: ✅ READY FOR GLOBAL USE!**

No Ollama. No GPU. Just install, set API key, and run! 🚀
