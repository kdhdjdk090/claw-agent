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
| **Force Council** | `/council` | `/council Explain quantum computing` |
| **Single Model** | `/nocouncil` | `/nocouncil What is 2+2?` |
| **Show Models** | `/models` | Shows all 6 council models |

## 🏛️ Council Models (6 Total - ALL FREE!)

1. **GPT-4o-mini** (OpenAI) - General reasoning & coding
2. **Claude 3 Haiku** (Anthropic) - Natural language
3. **Gemini Flash 1.5** (Google) - Speed & multi-modal
4. **Qwen 2.5 Coder 32B** (Alibaba) - Code generation
5. **Llama 3.3 70B** (Meta) - Knowledge powerhouse
6. **Mistral Small 24B** (Mistral) - Efficient reasoning

## 📊 Understanding Responses

### High Consensus (Good!)
```
[Council Consensus (83% - 5/6 models agree)]

Here's the solution...
```
✅ **Trust this answer** - models agree!

### Low Consensus (Diverse views)
```
[Council Vote - No consensus (33%)]

**Majority:** Use recursion...

**Alternatives:**
[GPT-4o-mini] Try iteration instead...
[Claude Haiku] Consider dynamic programming...
```
⚠️ **Models disagree** - review alternatives

## ⚡ Performance

| Metric | Single Model | Council (6 models) |
|--------|--------------|---------------------|
| **Speed** | 2-5 seconds | 5-10 seconds |
| **Accuracy** | Good | **Excellent** |
| **Cost** | Free tier | **FREE** |
| **Reliability** | Medium | **High** |

## 🎯 When to Use What

| Task | Mode | Why |
|------|------|-----|
| **Coding questions** | Council (auto) | Cross-validated solutions |
| **Simple facts** | /nocouncil | Faster, all models agree anyway |
| **Analysis** | Council (auto) | Multiple perspectives |
| **Creative tasks** | Council (auto) | Diverse ideas |
| **Quick checks** | /nocouncil | Speed over accuracy |

## 🔧 Configuration (.env.local)

```bash
# API Key (already configured!)
OPENROUTER_API_KEY="sk-or-v1-..."

# Customize models (optional)
COUNCIL_MODELS="openai/gpt-4o-mini,..."

# Adjust consensus threshold (optional)
COUNCIL_THRESHOLD=0.6  # 60% agreement required
```

## 🌐 Deploy to Cloud

```bash
vercel --prod
```

Council works identically in the cloud! ☁️

## 📚 Documentation

| File | What's Inside |
|------|---------------|
| **COUNCIL_GUIDE.md** | Complete feature documentation |
| **MIGRATION.md** | Migration from old setup |
| **UPGRADE_COMPLETE.md** | Summary of all changes |
| **README.md** | General project info |

## ✅ Quick Checklist

Before you start:
- [x] OpenRouter API key configured
- [x] 6 council models loaded
- [x] Council mode enabled (automatic)
- [x] All tests passing

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| "All models failed" | Check internet & API key |
| Slow responses | Normal for 6 models, use `/nocouncil` |
| Want single model | Use `/nocouncil` command |
| Council not working | Check `OPENROUTER_API_KEY` in `.env.local` |

## 💡 Pro Tips

1. **Trust high consensus** - 80%+ is very reliable
2. **Read alternatives** - Low consensus shows different approaches
3. **Use /nocouncil for speed** - When you need fast answers
4. **Code = high consensus** - Models usually agree on code
5. **Opinions vary** - Analysis questions show diverse views

## 🎉 You're Ready!

**Just start chatting - the council works automatically!**

```
You: How do I sort a list in Python?
Claw: [Council Consensus (83% - 5/6 models agree)]
      Here are the best approaches...
```

---

**Powered by 6 FREE AI models via OpenRouter**  
**Inspired by Karpathy's ll-council**  
**Consensus-validated for accuracy** 🦞✨
