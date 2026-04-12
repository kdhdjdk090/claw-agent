# Claw AI - DeepSeek R1 Configuration Summary

## ✅ All Issues Fixed

Claw AI has been successfully updated to use **DeepSeek-R1** (the highest model) via Ollama.

---

## 🎯 What Changed

### 1. **Default Model Updated**
- **Old:** `deepseek-v3.1:671b-cloud` (non-existent model)
- **New:** `deepseek-r1:671b` (highest available DeepSeek model via Ollama)

### 2. **Files Modified**

| File | Changes |
|------|---------|
| `claw_agent/agent.py` | Updated default model, added mode detection (local vs cloud) |
| `claw_agent/cli.py` | Updated model priority list, improved error messages |
| `claw_agent/tools/agent_tools.py` | Updated sub-agent fallback to `deepseek-r1:8b` |
| `claw_agent/tools/utility_tools.py` | Updated config_get default model |
| `vscode-extension/src/bridge.py` | Updated VS Code extension default model |
| `test_full.py` | Updated test references to use `deepseek-r1:671b` |
| `test_slash_and_ext.py` | Updated test expectations for new model |
| `DEEPSEEK_SETUP.md` | Complete rewrite with Ollama + Cloud setup instructions |

### 3. **Model Priority List** (auto-selection)

The CLI now prioritizes models in this order:
1. `deepseek-r1:671b` ⭐ (highest quality)
2. `deepseek-r1:32b`
3. `deepseek-r1:14b`
4. `deepseek-r1:8b`
5. `deepseek-v3:671b`
6. `deepseek-v3`
7. `qwen2.5:14b`
8. `qwen2.5:7b`
9. `mistral:latest`
10. `llama3.1:8b`

**Fallback:** `deepseek-r1:8b` if no models detected

---

## 🚀 How to Use

### Quick Start (Local Ollama)

```bash
# 1. Pull the model (40+ GB required)
ollama pull deepseek-r1:671b

# 2. Start Ollama (if not running)
ollama serve

# 3. Run Claw AI
claw

# Or specify model explicitly
claw -m deepseek-r1:671b
```

### Alternative Model Sizes

If 671B is too large for your hardware:

```bash
# Medium hardware (10+ GB RAM/VRAM)
claw -m deepseek-r1:14b

# Light weight (6+ GB RAM/VRAM)
claw -m deepseek-r1:8b

# Good balance (20+ GB RAM/VRAM)
claw -m deepseek-r1:32b
```

### Cloud Mode (No Local GPU)

Set the `DEEPSEEK_API_KEY` environment variable to use cloud API instead:

**Windows PowerShell:**
```powershell
$env:DEEPSEEK_API_KEY="your-api-key-here"
claw
```

**Permanent:**
```powershell
[System.Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "your-api-key-here", "User")
```

---

## ✨ New Features

### 1. **Mode Detection**
The agent now automatically detects whether it's running:
- **Local Mode:** "via local Ollama"
- **Cloud Mode:** "via Cloud API"

This is reflected in the system prompt so the model knows its deployment context.

### 2. **Better Error Messages**
If Ollama isn't running, users now see:
```
Setup Required
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✗ Ollama is not running!

  1. Install: https://ollama.com/download
  2. Start:   ollama serve
  3. Pull:    ollama pull deepseek-r1:8b

  For the highest model: ollama pull deepseek-r1:671b
  (requires 671B cloud quantized or sufficient GPU memory)
```

### 3. **Verification Script**
Run `python verify_deepseek.py` to verify all configurations are correct.

---

## 📊 Model Comparison

| Model | Quality | Parameters | RAM/VRAM Required | Speed |
|-------|---------|-----------|-------------------|-------|
| `deepseek-r1:671b` | ⭐⭐⭐⭐⭐ | 671B | 40+ GB | Slow |
| `deepseek-r1:32b` | ⭐⭐⭐⭐ | 32B | 20+ GB | Medium |
| `deepseek-r1:14b` | ⭐⭐⭐ | 14B | 10+ GB | Fast |
| `deepseek-r1:8b` | ⭐⭐ | 8B | 6+ GB | Very Fast |

**Default:** `deepseek-r1:671b` (highest quality)

---

## 🧪 Verification Results

All tests pass successfully:

```
[1] Module Imports ✓
[2] Default Model Configuration ✓
[3] Model Selection Priority ✓
[4] Agent Instantiation ✓
[5] Tool Configuration ✓
[6] Sub-Agent Configuration ✓
[7] System Prompt ✓
```

---

## 🔧 Technical Details

### System Prompt Template
The system prompt now includes:
- Model name dynamically inserted
- Mode label (local Ollama vs Cloud API)
- Working directory and platform
- Full tool list and usage guidelines

### Agent Initialization
```python
agent = Agent(
    model="deepseek-r1:671b",  # Default
    base_url="http://localhost:11434"  # Local Ollama
)
```

### Cloud API Support
When `DEEPSEEK_API_KEY` is set, the Vercel deployment uses:
- Endpoint: `https://api.deepseek.com/chat/completions`
- Model: `deepseek-chat`
- Streaming: Supported

---

## 🐛 Troubleshooting

### "Ollama is not running"
```bash
ollama serve
```

### "Model not found"
```bash
ollama pull deepseek-r1:671b
ollama list  # Verify it's downloaded
```

### "Out of memory"
Use a smaller model:
```bash
claw -m deepseek-r1:14b
```

### "API key not configured" (Cloud mode)
Set the `DEEPSEEK_API_KEY` environment variable (see Cloud Mode section above).

---

## 📝 Next Steps

1. **Pull the model:** `ollama pull deepseek-r1:671b`
2. **Start Ollama:** `ollama serve`
3. **Run Claw:** `claw`
4. **Verify setup:** `python verify_deepseek.py`

---

## 📚 Documentation Updated

- `DEEPSEEK_SETUP.md` - Complete setup guide for both Ollama and Cloud modes
- `CLAW.md` - Repository guidance (unchanged)
- `README.md` - User-facing documentation (should be reviewed separately)

---

**Status:** ✅ All issues resolved, all tests passing, ready for production use.
