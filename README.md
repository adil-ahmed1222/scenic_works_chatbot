# Scenic Works AI Chatbot

Production-ready multilingual RAG chatbot for [Scenic Works](https://adroitiame.com). It answers only from official website content, supports English and Arabic, captures qualified leads, and can be embedded on the existing site with a single script tag.

## Architecture

```
Website (adroitiame.com)
        │
        ▼
  Crawl4AI scraper  ──►  knowledge-base/raw
        │
        ▼
  Processor / Chunker / bge-m3 embeddings
        │
        ▼
  Supabase PostgreSQL + pgvector
        │
User ──► Next.js widget ──► FastAPI ──► Groq (gpt-oss-120b)
                                │
                                ├── ElevenLabs TTS
                                └── Leads table
```

## Repository layout

| Path | Purpose |
| --- | --- |
| `scraper/` | Domain crawler (Crawl4AI, sitemap, incremental, retries) |
| `knowledge-base/` | Cleaning, chunking, embeddings |
| `backend/` | FastAPI RAG API |
| `frontend/` | Next.js 15 widget + `widget.js` |
| `supabase/migrations/` | Database schema |
| `scheduler/` | Daily 01:00 UTC knowledge refresh |
| `tests/` | 100 EN + 100 AR eval questions and unit tests |
| `docs/` | Deployment, env, admin, integration guides |

## Quick start

1. Copy `.env.example` to `.env` and fill Groq, Supabase, ElevenLabs, `WIDGET_API_SECRET`, and `SESSION_SIGNING_KEY`. For production, put the same widget secret on Vercel as a **server** env var (never `NEXT_PUBLIC_*`).
2. Apply `supabase/migrations/20260824000001_init.sql` in the Supabase SQL editor.
3. Index website knowledge (uses seed pages if you have not crawled yet):

```bash
python knowledge-base/pipeline.py --skip-embed   # local inspect
python knowledge-base/pipeline.py                # write embeddings
```

4. Run the API:

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

5. Run the widget:

```bash
cd frontend
npm install
npm run dev
```

6. Open http://localhost:3000 — the floating assistant appears in the bottom-right.

## Embed on adroitiame.com

```html
<script src="https://chat.adroitiame.com/widget.js"></script>
```

No website rebuild is required. See [docs/INTEGRATION.md](docs/INTEGRATION.md).

## Guardrails

The model is instructed to never invent services, projects, locations, clients, pricing, or company facts. If retrieval misses, it replies:

> I couldn't find that information in Scenic Works' knowledge base. Please contact Scenic Works directly for assistance.

Arabic equivalent:

> لم أتمكن من العثور على هذه المعلومات في قاعدة معرفة سينيك ووركس. يُرجى التواصل مع سينيك ووركس مباشرة للمساعدة.

## Documentation

- [Deployment](docs/DEPLOYMENT.md)
- [Environment variables](docs/ENVIRONMENT.md)
- [Admin guide](docs/ADMIN.md)
- [Website integration](docs/INTEGRATION.md)
