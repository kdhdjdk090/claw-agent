# 🦞 Claw AI - Quick Reference Card

## 🚀 Start Claw AI
```bash
cd c:\Users\Sinwa\Pictures\ClaudeAI\claw-agent
python -m claw_agent
```

## 💬 Chat Commands

| Type | Command | Example |
|------|---------|---------|
| **Normal Chat** | Just type | `How do I reverse a string in Python?` |
| **Force ensemble** | `/models` | `/models Explain quantum computing` |
| **Single Model** | `/noensemble` | `/noensemble What is 2+2?` |
| **Show Models** | `/models` | Shows all 6 ensemble models |

## 🏛️ ensemble models (6 Total - ALL FREE!)

1. **GPT-4o-mini** (OpenAI) - General reasoning & coding
2. **Claude 3 Haiku** (Anthropic) - Natural language
3. **Gemini Flash 1.5** (Google) - Speed & multi-modal
4. **Qwen 2.5 Coder 32B** (Alibaba) - Code generation
5. **Llama 3.3 70B** (Meta) - Knowledge powerhouse
6. **Mistral Small 24B** (Mistral) - Efficient reasoning

## 📊 Understanding Responses

### High Consensus (Good!)
```
[model agreement (83% - 5/6 models agree)]

Here's the solution...
```
✅ **Trust this answer** - models agree!

### Low Consensus (Diverse views)
```
[ensemble Vote - No consensus (33%)]

**Majority:** Use recursion...

**Alternatives:**
[GPT-4o-mini] Try iteration instead...
[Claude Haiku] Consider dynamic programming...
```
⚠️ **Models disagree** - review alternatives

## ⚡ Performance

| Metric | Single Model | ensemble (6 models) |
|--------|--------------|---------------------|
| **Speed** | 2-5 seconds | 5-10 seconds |
| **Accuracy** | Good | **Excellent** |
| **Cost** | Free tier | **FREE** |
| **Reliability** | Medium | **High** |

## 🎯 When to Use What

| Task | Mode | Why |
|------|------|-----|
| **Coding questions** | ensemble (auto) | Cross-validated solutions |
| **Simple facts** | /noensemble | Faster, all models agree anyway |
| **Analysis** | ensemble (auto) | Multiple perspectives |
| **Creative tasks** | ensemble (auto) | Diverse ideas |
| **Quick checks** | /noensemble | Speed over accuracy |

## 🔧 Configuration (.env.local)

```bash
# API Key (already configured!)
NVIDIA NIM_API_KEY="sk-or-v1-..."

# Customize models (optional)
ensemble_MODELS="openai/gpt-4o-mini,..."

# Adjust consensus threshold (optional)
ensemble_THRESHOLD=0.6  # 60% agreement required
```

## 🌐 Deploy to Cloud

```bash
vercel --prod
```

ensemble works identically in the cloud! ☁️

## 📚 Documentation

| File | What's Inside |
|------|---------------|
| **ensemble_GUIDE.md** | Complete feature documentation |
| **MIGRATION.md** | Migration from old setup |
| **UPGRADE_COMPLETE.md** | Summary of all changes |
| **README.md** | General project info |

## ✅ Quick Checklist

Before you start:
- [x] NVIDIA NIM API key configured
- [x] 6 ensemble models loaded
- [x] ensemble mode enabled (automatic)
- [x] All tests passing

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| "All models failed" | Check internet & API key |
| Slow responses | Normal for 6 models, use `/noensemble` |
| Want single model | Use `/noensemble` command |
| ensemble not working | Check `NVIDIA NIM_API_KEY` in `.env.local` |

## 💡 Pro Tips

1. **Trust high consensus** - 80%+ is very reliable
2. **Read alternatives** - Low consensus shows different approaches
3. **Use /noensemble for speed** - When you need fast answers
4. **Code = high consensus** - Models usually agree on code
5. **Opinions vary** - Analysis questions show diverse views

## 🎉 You're Ready!

**Just start chatting - the ensemble works automatically!**

```
You: How do I sort a list in Python?
Claw: [model agreement (83% - 5/6 models agree)]
      Here are the best approaches...
```

---

**Powered by 6 FREE AI models via NVIDIA NIM**  
**Inspired by Karpathy's ll-ensemble**  
**Consensus-validated for accuracy** 🦞✨
