# Deployment Guide

## Render (client testing URL)

Use **Native Python**, not Docker, unless you set the Dockerfile path yourself.

The failure `open Dockerfile: no such file or directory` happens when Render's root is the GitHub repo root and Environment is Docker. There is now a root `Dockerfile` as a fallback, but **Free Tier should use Python**.

### Service A — API

| Field | Value |
| --- | --- |
| Environment | **Python 3** |
| Root Directory | `backend` |
| Build Command | `pip install -r requirements-render.txt` |
| Start Command | `python start.py` |
| Health Check | `/health` |

### Service B — Widget (the URL you send the client)

| Field | Value |
| --- | --- |
| Environment | **Node** |
| Root Directory | `frontend` |
| Build Command | `npm ci && npm run build` |
| Start Command | `npm run start` |

Or connect the repo as a **Blueprint** (`render.yaml`) to create both services.

Required API env vars: `APP_ENV=production`, `EMBEDDING_PROVIDER=huggingface`, `HF_API_TOKEN`, `GROQ_API_KEY`, `ELEVENLABS_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `WIDGET_API_SECRET`, `SESSION_SIGNING_KEY`, `FRONTEND_URL`, `BACKEND_URL`, `ALLOWED_ORIGINS`.

Required web env vars: `BACKEND_URL` (API `onrender.com` URL), `WIDGET_API_SECRET` (same value).

Do not use `EMBEDDING_PROVIDER=local` on the Free tier. Local `bge-m3` + torch will exceed memory.

---

This stack deploys as three services:

| Layer | Platform | Directory |
| --- | --- | --- |
| Widget + embed script | Vercel | `frontend/` |
| RAG API | Railway | `backend/` |
| Database + storage | Supabase | `supabase/migrations/` |

## 1. Supabase

1. Create a project.
2. Open **SQL Editor** and run `supabase/migrations/20260824000001_init.sql`.
3. If the project already existed, also run `supabase/migrations/20260906000001_revoke_match_documents.sql`.
5. Confirm the `vector` extension, tables (`documents`, `chat_history`, `leads`, `crawl_status`), and `match_documents` RPC exist.
6. In **Storage**, confirm bucket `tts-audio` is public.
7. Copy **Project URL** and **service_role** key into Railway (never into Vercel / the browser).

## 2. Railway (FastAPI)

1. Create a new Railway service from this repo.
2. Set the root directory to `backend` (or deploy with `backend/Dockerfile`).
3. Add every backend variable from [ENVIRONMENT.md](ENVIRONMENT.md).
4. Allocate at least **2 GB RAM** if `EMBEDDING_PROVIDER=local` (BAAI/bge-m3). For smaller instances set `EMBEDDING_PROVIDER=huggingface` and `HF_API_TOKEN`.
5. Health check path: `/health`.
6. Note the public URL, e.g. `https://scenic-works-api.up.railway.app`.

## 3. Vercel (Next.js)

1. Import the repo, set the root directory to `frontend`.
2. Environment variables:

```
BACKEND_URL=https://scenic-works-api.up.railway.app
WIDGET_API_SECRET=<same secret as Railway>
NEXT_PUBLIC_WIDGET_TITLE=Scenic Works Assistant
NEXT_PUBLIC_BRAND_NAME=Scenic Works
```

3. Deploy. Custom domain: `chat.adroitiame.com`.
4. Confirm:
   - `https://chat.adroitiame.com` — demo page
   - `https://chat.adroitiame.com/embed` — iframe widget
   - `https://chat.adroitiame.com/widget.js` — embed script

## 4. First knowledge index

On a machine with Python 3.12 (or a Railway one-off job):

```bash
pip install -r scraper/requirements.txt
pip install -r knowledge-base/requirements.txt
python -m playwright install --with-deps chromium
python -m scraper.run
python knowledge-base/pipeline.py
```

Seed pages under `knowledge-base/raw/` let you index before the first crawl.

## 5. Daily refresh (01:00 UTC)

GitHub Actions workflow `.github/workflows/daily-knowledge-update.yml` runs:

Website → incremental crawl → process → chunk → bge-m3 → Supabase

Add repository secrets: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, optional `HF_API_TOKEN`.

Alternatively run `python scheduler/daily_update.py` as a Railway cron at `0 1 * * *`.

## 6. CORS

Set `ALLOWED_ORIGINS` on Railway to include:

```
https://chat.adroitiame.com,https://adroitiame.com,https://www.adroitiame.com
```

The widget iframe origin is the Vercel domain. After the Next.js proxy is in place, browsers call same-origin `/api/*` and FastAPI CORS is only needed for direct API clients.

## 7. Production secrets

On **both** Railway and Vercel set the same `WIDGET_API_SECRET`. On Railway also set a separate `SESSION_SIGNING_KEY`.

Pre-flight checks:

1. `GET /health` returns `{"status":"ok"}` without a widget key.
2. `POST /chat` without `X-Widget-Key` returns `401`.
3. The widget welcome screen loads (not the knowledge-base fallback).
4. A real question returns a Scenic Works answer and a `session_token`.
5. Play Voice returns audio.
6. The lead form saves; a filled hidden `website` field is silently ignored.
