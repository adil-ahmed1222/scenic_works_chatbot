# Environment Variables Guide

Copy `.env.example` to `.env`. **Never** put `GROQ_API_KEY`, `ELEVENLABS_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `WIDGET_API_SECRET`, or `SESSION_SIGNING_KEY` in Next.js `NEXT_PUBLIC_*` variables or `widget.js`.

## Backend (Railway)

| Variable | Required | Notes |
| --- | --- | --- |
| `APP_ENV` | yes | `production` disables `/docs` and requires `WIDGET_API_SECRET` |
| `LOG_LEVEL` | no | `INFO` |
| `ALLOWED_ORIGINS` | yes | Comma-separated widget + website origins |
| `BACKEND_URL` | yes | Public API URL (used for local audio fallback URLs) |
| `GROQ_API_KEY` | yes | Groq console |
| `GROQ_MODEL` | no | Default `openai/gpt-oss-120b` (Groq retired Llama 3.3 on 16 Aug 2026) |
| `GROQ_TEMPERATURE` | no | Keep `0.1` to reduce hallucination |
| `ELEVENLABS_API_KEY` | yes | Voice playback |
| `ELEVENLABS_MODEL` | no | `eleven_multilingual_v2` |
| `ELEVENLABS_VOICE_EN` | no | English voice id |
| `ELEVENLABS_VOICE_AR` | no | Arabic-capable multilingual voice id |
| `SUPABASE_URL` | yes | `https://xxxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | yes | Server only |
| `SUPABASE_STORAGE_BUCKET` | no | `tts-audio` |
| `EMBEDDING_MODEL` | no | `BAAI/bge-m3` |
| `EMBEDDING_DIM` | no | `1024` |
| `EMBEDDING_PROVIDER` | no | `local` or `huggingface` |
| `HF_API_TOKEN` | if HF | Hugging Face Inference |
| `RAG_TOP_K` | no | `5` |
| `RAG_MIN_SIMILARITY` | no | `0.35` |
| `CHAT_HISTORY_LIMIT` | no | `10` |
| `RATE_LIMIT_CHAT` | no | `30/minute` |
| `RATE_LIMIT_VOICE` | no | `10/minute` |
| `RATE_LIMIT_LEAD` | no | `8/minute` |
| `TRUST_PROXY` | no | Set `true` only behind a reverse proxy that overwrites `X-Forwarded-For`. Production (`APP_ENV=production`) already trusts the proxy. |
| `WIDGET_API_SECRET` | yes in production | Shared with the Next.js server. Sent as `X-Widget-Key`. |
| `SESSION_SIGNING_KEY` | yes in production | HMAC key for chat session tokens. Use a different value from the widget secret. |

## Frontend (Vercel)

| Variable | Public? | Notes |
| --- | --- | --- |
| `BACKEND_URL` | no | FastAPI origin used only by Next.js server routes |
| `WIDGET_API_SECRET` | no | Same value as Railway. Never prefix with `NEXT_PUBLIC_` |
| `NEXT_PUBLIC_WIDGET_TITLE` | yes | Header label |
| `NEXT_PUBLIC_BRAND_NAME` | yes | Display name |

The browser talks only to same-origin `/api/chat`, `/api/voice`, and `/api/lead`. Those routes attach `X-Widget-Key` on the server.

## Scraper / GitHub Actions

| Variable | Notes |
| --- | --- |
| `CRAWL_BASE_URL` | `https://adroitiame.com` |
| `CRAWL_MAX_PAGES` | Default `500` |
| `CRAWL_MAX_DEPTH` | Default `6` |
| `CRAWL_DELAY_SECONDS` | Be polite; default `1.0` |

## Secret handling

- Railway / GitHub Actions / local `.env` only.
- Rotate keys if they ever appear in client bundles or git history.
- Supabase **anon** key is unused by this API on purpose; the service role stays on the server.
- After changing `WIDGET_API_SECRET` or `SESSION_SIGNING_KEY`, restart FastAPI and redeploy Vercel. Existing browser session tokens become invalid and a new chat session starts.
