# Deployment

## Target

Deploy the NVIDIA-first Claw AI runtime.

## Pre-deploy checks

```bash
python -m unittest discover -s tests -p "test_*.py"
node --check api/index.js
```

## Required environment variables

- NVIDIA_API_KEY

Optional:
- DASHSCOPE_API_KEY
- OPENAI_API_KEY
- COMETAPI_KEY
- DEEPSEEK_API_KEY

## Vercel

Dashboard path:
- `Project -> Settings -> Environment Variables`

Add:
- `NVIDIA_API_KEY` for `Production`, `Preview`, and `Development`
- `NIM_API_KEY` only if you want a compatibility alias

Vercel CLI:

```bash
vercel env add NVIDIA_API_KEY production
vercel env add NVIDIA_API_KEY preview
vercel env add NVIDIA_API_KEY development
```

If you update the secret later:

```bash
vercel env update NVIDIA_API_KEY production
vercel env update NVIDIA_API_KEY preview
vercel env update NVIDIA_API_KEY development
```

Pull the Vercel development values locally:

```bash
vercel env pull .env.local
```

Important:
- do not commit `.env.local`
- redeploy after changing env vars
- rotate the key if it was ever pasted into logs, chat, or commits

## Deploy notes

- API server uses https://integrate.api.nvidia.com for NVIDIA paths.
- Chrome extension CSP/connect-src must include NVIDIA endpoint.
- Ensure no hardcoded keys remain in repository files.

## Smoke test

- GET /api/health
- GET /api/models
- POST /api/chat
- GET /api/status
