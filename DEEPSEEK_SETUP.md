# DeepSeek API Setup for Vercel

Your Claw AI is now using the **DeepSeek API** instead of local Ollama.

## Setup Steps

### 1. Get a DeepSeek API Key

1. Go to https://platform.deepseek.com
2. Sign up or log in
3. Go to **API Keys** section
4. Create a new API key
5. Copy the key

### 2. Add to Vercel Environment Variables

1. Go to https://vercel.com/dashboard
2. Select your **clean-claw-ai** project
3. Go to **Settings** → **Environment Variables**
4. Add new variable:
   - **Name:** `DEEPSEEK_API_KEY`
   - **Value:** (paste your API key here)
5. Save

### 3. Redeploy

```bash
cd c:\Users\Sinwa\Pictures\ClaudeAI\claw-agent
vercel deploy --prod
```

## Features

✅ Uses DeepSeek's advanced chat model  
✅ No local Ollama required  
✅ Works globally from Vercel edge  
✅ Token usage tracking  
✅ Full reasoning capabilities  

## CLI Usage (Local Ollama Still Works)

The CLI still uses local Ollama:
```bash
claw                    # Interactive mode
claw prompt "ask me"    # One-shot mode
```

## Troubleshooting

- **"API key not configured"** → Add DEEPSEEK_API_KEY to Vercel env vars
- **"Cannot reach DeepSeek API"** → Check internet connection
- **Timeout errors** → DeepSeek may be slow, try again
