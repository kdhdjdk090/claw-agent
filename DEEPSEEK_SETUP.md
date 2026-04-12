# DeepSeek Setup for Claw AI

Claw AI supports **both** local Ollama and cloud DeepSeek API.

## Option 1: Local Ollama (Recommended for Privacy)

### 1. Install Ollama

Download from: https://ollama.com/download

### 2. Pull DeepSeek Model

Choose the model size based on your hardware:

```bash
# Best quality (requires 40+ GB RAM/VRAM)
ollama pull deepseek-r1:671b

# Good balance (requires 20+ GB RAM/VRAM)
ollama pull deepseek-r1:32b

# Medium quality (requires 10+ GB RAM/VRAM)
ollama pull deepseek-r1:14b

# Light weight (requires 6+ GB RAM/VRAM)
ollama pull deepseek-r1:8b
```

### 3. Start Ollama

```bash
ollama serve
```

### 4. Run Claw AI

```bash
claw                          # Interactive mode (auto-detects best model)
claw -m deepseek-r1:671b      # Specify model explicitly
claw prompt "ask me anything" # One-shot mode
```

## Option 2: Cloud DeepSeek API (Faster, No Local GPU Required)

### 1. Get a DeepSeek API Key

1. Go to https://platform.deepseek.com
2. Sign up or log in
3. Go to **API Keys** section
4. Create a new API key
5. Copy the key

### 2. Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:DEEPSEEK_API_KEY="your-api-key-here"
```

**Windows (cmd):**
```cmd
set DEEPSEEK_API_KEY=your-api-key-here
```

**Permanent (System-wide):**
```powershell
[System.Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "your-api-key-here", "User")
```

### 3. Use Cloud Mode

When `DEEPSEEK_API_KEY` is set, Claw AI will automatically use the cloud API instead of local Ollama.

## Features

✅ Local Ollama: 100% private, no data leaves your machine
✅ Cloud DeepSeek: Faster inference, no GPU required
✅ Automatic model detection and selection
✅ Token usage tracking
✅ Full reasoning capabilities
✅ Session persistence

## Troubleshooting

### "Ollama is not running"
- Start Ollama: `ollama serve`
- Check status: Visit http://localhost:11434 in browser
- Reinstall if needed: https://ollama.com/download

### "Model not found"
- Pull the model: `ollama pull deepseek-r1:671b`
- List models: `ollama list`
- Check available: `claw /models`

### "API key not configured" (Cloud mode)
- Set `DEEPSEEK_API_KEY` environment variable
- Restart your terminal/IDE after setting

### Slow performance
- Use a smaller model: `deepseek-r1:8b` or `deepseek-r1:14b`
- Close other GPU applications
- Check GPU memory: Task Manager → Performance → GPU

## Model Comparison

| Model | Quality | RAM/VRAM | Speed |
|-------|---------|----------|-------|
| deepseek-r1:671b | ⭐⭐⭐⭐⭐ | 40+ GB | Slow |
| deepseek-r1:32b | ⭐⭐⭐⭐ | 20+ GB | Medium |
| deepseek-r1:14b | ⭐⭐⭐ | 10+ GB | Fast |
| deepseek-r1:8b | ⭐⭐ | 6+ GB | Very Fast |

Default: **deepseek-r1:671b** (highest quality)
