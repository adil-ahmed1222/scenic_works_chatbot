# Admin Guide

## Knowledge updates

The chatbot only knows what is stored in `documents`.

**Automatic:** GitHub Action at 01:00 UTC crawls changed pages and re-embeds them.

**Manual:**

```bash
python -m scraper.run          # incremental
python -m scraper.run --full   # recrawl everything
python knowledge-base/pipeline.py
```

Crawl status lives at `scraper/data/crawl_status.json` (hash per URL, last run, failures).

## Leads

Qualified buying intent (quotation, proposal, exhibition stand, event setup, pricing) opens a form. Rows land in Supabase table `leads`:

- name, email, phone, company, requirements, session_id, created_at

Export with:

```sql
select * from leads order by created_at desc;
```

## Chat history

`chat_history` stores user and assistant turns by `session_id`. The API sends the last 10 messages to Groq.

Purge old sessions if needed:

```sql
delete from chat_history where created_at < now() - interval '90 days';
```

## Hallucination policy

If retrieval returns nothing below `RAG_MIN_SIMILARITY`, or Groq cannot ground an answer, the assistant must say it could not find the information. Do not add unofficial PDFs or sales decks unless you want those facts in the bot.

## Voice

`POST /voice` synthesizes the last assistant reply with ElevenLabs. English and Arabic use separate voice IDs. Files go to the `tts-audio` bucket (or `backend/static/audio` as fallback).

## Health

```
GET /health  →  { "status": "ok" }
```

Use this for Railway health checks and uptime monitors.

## Evaluation

```bash
python tests/generate_questions.py
python tests/run_eval.py --base-url https://YOUR-API
```

Reports write to `tests/reports/eval.json` (accuracy, fallback correctness, lead triggers, latency).
