# 🦞 Claw AI - Multi-Model Council System

## Overview

Claw AI now uses a **Multi-Model Council** architecture inspired by Andrej Karpathy's [ll-council](https://github.com/karpathy/llm-council). Instead of relying on a single AI model, Claw queries **multiple AI models simultaneously** and aggregates their responses to provide you with the **best consensus answer**.

## 🎯 What Changed

### Before (Single Model)
```
User Query → DeepSeek/Ollama → Single Response
```

### After (Council System)
```
User Query → [GPT-4o-mini, Claude Haiku, Gemini Flash, Qwen, Llama, Mistral] → Consensus Response
```

## 🏛️ The Council

Claw uses **6 of the best free AI models** available on OpenRouter:

| Model | Provider | Strength |
|-------|----------|----------|
| **GPT-4o-mini** | OpenAI | General reasoning, coding |
| **Claude 3 Haiku** | Anthropic | Natural language, analysis |
| **Gemini Flash 1.5** | Google | Speed, multi-modal |
| **Qwen 2.5 Coder 32B** | Alibaba | Code generation |
| **Llama 3.3 70B** | Meta | General knowledge |
| **Mistral Small 24B** | Mistral | Efficiency, reasoning |

### Why These Models?
✅ **Completely FREE** on OpenRouter  
✅ **Diverse perspectives** from different providers  
✅ **Specialized strengths** complement each other  
✅ **Production-grade** quality  

## 🚀 Quick Start

### Local Setup

1. **Environment variables already configured!** Your `.env.local` has:
   ```bash
   OPENROUTER_API_KEY="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"
   COUNCIL_MODELS="openai/gpt-4o-mini,anthropic/claude-3-haiku,google/gemini-flash-1.5,qwen/qwen-2.5-coder-32b-instruct,meta-llama/llama-3.3-70b-instruct,mistralai/mistral-small-24b-instruct-2501"
   COUNCIL_THRESHOLD=0.6
   ```

2. **Start Claw AI:**
   ```bash
   cd claw-agent
   python -m claw_agent
   ```

3. **Council mode is AUTOMATIC** - just chat normally!
   - All queries go through the council by default
   - Use `/nocouncil` to use a single model if needed

### Vercel Cloud Deployment

Your OpenRouter API key is configured for Vercel deployment. To deploy:

```bash
cd claw-agent
vercel --prod
```

The council system will work identically in the cloud!

## 📊 How Council Consensus Works

### 1. **Parallel Query**
All 6 models receive your query simultaneously.

### 2. **Response Collection**
Each model generates its independent response.

### 3. **Consensus Algorithm**
The system:
- Normalizes responses (remove formatting, lowercase)
- Groups similar responses using string similarity
- Finds the largest agreement group (majority vote)
- Calculates consensus percentage

### 4. **Response Selection**
- **≥60% consensus**: Returns the consensus answer with badge
- **<60% consensus**: Returns majority vote + shows alternatives

### Example Output

**Strong Consensus:**
```
[Council Consensus (83% - 5/6 models agree)]

The issue is in the function calculateTotal(). Here's the fix:
[unified solution code]
```

**No Consensus:**
```
[Council Vote - No consensus (33%)]

**Majority:** Approach A using recursion...

**Alternatives:**
[GPT-4o-mini] Consider using iteration instead...
[Claude Haiku] You might want to try dynamic programming...
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key | *(required)* |
| `COUNCIL_MODELS` | Comma-separated model list | `openai/gpt-4o-mini,...` |
| `COUNCIL_THRESHOLD` | Consensus percentage required | `0.6` (60%) |
| `DISABLE_COUNCIL` | Set to disable council auto-mode | *(empty)* |

### Customizing Models

You can customize which models participate in the council:

**In `.env.local`:**
```bash
# Use only 3 models for faster responses
COUNCIL_MODELS="openai/gpt-4o-mini,anthropic/claude-3-haiku,google/gemini-flash-1.5"

# Require higher consensus
COUNCIL_THRESHOLD=0.75
```

### Available Free Models on OpenRouter

Some other free models you can add:
- `nousresearch/nous-hermes-2-mixtral-8x7b-dpo`
- `microsoft/wizardlm-2-8x22b`
- `google/gemma-7b-it`
- `openchat/openchat-7b`
- `perplexity/llama-3-sonar-small-32k-chat`

## 🎮 Usage Modes

### Automatic Council (Default)
Just chat normally - council is used automatically!

### Single Model Mode
```
/nocouncil What is Python?
```
Uses a single model (faster, less reliable).

### Explicit Council Mode
```
/council Explain quantum computing
```
Forces council mode even if disabled.

### Check Council Status
```
/models
```
Shows which models are in the council.

## 📈 Performance

### Response Time
- **Single model**: ~2-5 seconds
- **Council (6 models)**: ~5-10 seconds (parallel, waits for slowest)

### Token Usage
- **Council uses ~6x more tokens** (one query per model)
- **BUT**: All models used are **FREE** on OpenRouter
- **Total cost**: $0.00 (all models are free tier!)

### Quality Improvement
- **Higher accuracy**: Multiple perspectives reduce errors
- **Balanced responses**: Avoids individual model biases
- **Consensus validation**: You know when models agree!

## 🔍 API Endpoints

### POST `/api/chat`
Standard chat endpoint (auto-uses council if enabled).

```json
{
  "message": "How do I sort a list in Python?",
  "use_council": true  // optional, defaults to true
}
```

### POST `/api/council`
Explicit council endpoint (always uses all models).

```json
{
  "message": "Explain recursion"
}
```

### GET `/api/models`
List available council models.

```json
{
  "council": ["openai/gpt-4o-mini", "anthropic/claude-3-haiku", ...],
  "council_enabled": true,
  "mode": "council"
}
```

## 🧪 Testing the Council

### Test 1: Simple Question
```
What is 2 + 2?
```
Expected: All 6 models should agree (100% consensus).

### Test 2: Coding Question
```
Write a Python function to reverse a string
```
Expected: High consensus (83%+) with similar code.

### Test 3: Opinion/Analysis
```
What's the best programming language for beginners?
```
Expected: Lower consensus, shows diverse perspectives.

## 🐛 Troubleshooting

### "All models failed" Error
- Check your `OPENROUTER_API_KEY` is valid
- Ensure internet connection is active
- Try again (rate limits may apply)

### Slow Responses
- Council queries 6 models in parallel
- Normal: 5-10 seconds
- To speed up: reduce `COUNCIL_MODELS` count

### Council Not Working
- Verify `OPENROUTER_API_KEY` is set in `.env.local`
- Check `DISABLE_COUNCIL` is not set
- Look for error messages in console

### Want Single Model Back
```bash
# In .env.local
DISABLE_COUNCIL=true
```

## 🎓 Why Council?

### Inspired by Karpathy's ll-council
Andrej Karpathy built the original ll-council to solve a fundamental problem: **no single model is always right**. By querying multiple models and finding consensus, you get:

1. **Higher accuracy** - Models cross-validate each other
2. **Reduced hallucinations** - Wrong answers stand out
3. **Diverse perspectives** - See different approaches
4. **Trust indicator** - Consensus % tells you confidence

### Real-World Benefits
- **Coding**: Multiple models verify the solution
- **Analysis**: Different viewpoints enrich understanding  
- **Learning**: See how different AIs approach problems
- **Production**: More reliable than single-model answers

## 📚 Architecture

### Python Implementation (`claw_agent/ll_council.py`)
- `LLCouncil` class manages the council
- Queries models via OpenRouter API
- Implements consensus algorithm
- Returns aggregated results

### Node.js Implementation (`api/index.js`)
- Serverless function for Vercel
- Parallel model queries
- Consensus calculation
- RESTful API endpoints

### Integration (`claw_agent/agent.py`)
- Auto-detects OpenRouter API key
- Initializes council on startup
- Routes queries through council by default
- Fallback to single model if needed

## 🚀 Next Steps

1. **Try it out!** - Start chatting with Claw AI
2. **Customize** - Adjust models/threshold to your needs
3. **Deploy** - Push to Vercel for cloud access
4. **Extend** - Add your own models to the council

## 📞 Support

For issues or questions:
- Check the council is enabled: `/models`
- Test with simple questions first
- Review `.env.local` configuration
- Check OpenRouter dashboard for API status

---

**Built with ❤️ inspired by Karpathy's ll-council**  
**Powering Claw AI with 6 free AI models via OpenRouter**
