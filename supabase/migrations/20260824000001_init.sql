-- Scenic Works Chatbot - initial schema (pgvector)

create extension if not exists vector;
create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- documents: RAG chunks
-- ---------------------------------------------------------------------------
create table if not exists public.documents (
  id text primary key,
  content text not null,
  embedding vector(384),
  source_url text,
  language text,
  category text,
  title text,
  metadata jsonb not null default '{}'::jsonb,
  content_hash text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists documents_embedding_hnsw
  on public.documents using hnsw (embedding vector_cosine_ops);

create index if not exists documents_source_url_idx on public.documents (source_url);
create index if not exists documents_language_idx on public.documents (language);
create index if not exists documents_category_idx on public.documents (category);

-- ---------------------------------------------------------------------------
-- chat_history
-- ---------------------------------------------------------------------------
create table if not exists public.chat_history (
  id uuid primary key default gen_random_uuid(),
  session_id text not null,
  role text not null check (role in ('user', 'assistant', 'system')),
  message text not null,
  language text,
  created_at timestamptz not null default now()
);

create index if not exists chat_history_session_idx
  on public.chat_history (session_id, created_at);

-- ---------------------------------------------------------------------------
-- leads
-- ---------------------------------------------------------------------------
create table if not exists public.leads (
  id uuid primary key default gen_random_uuid(),
  session_id text,
  name text not null,
  email text not null,
  phone text,
  company text,
  requirements text,
  language text,
  created_at timestamptz not null default now()
);

create index if not exists leads_email_idx on public.leads (email);
create index if not exists leads_created_at_idx on public.leads (created_at desc);

-- ---------------------------------------------------------------------------
-- crawl_status (incremental crawls)
-- ---------------------------------------------------------------------------
create table if not exists public.crawl_status (
  url text primary key,
  content_hash text,
  title text,
  language text,
  changed boolean default true,
  ok boolean default true,
  error text,
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- Similarity search RPC
-- ---------------------------------------------------------------------------
create or replace function public.match_documents(
  query_embedding vector(384),
  match_count int default 5,
  filter_language text default null,
  min_similarity float default 0.0
)
returns table (
  id text,
  content text,
  source_url text,
  language text,
  category text,
  title text,
  similarity float
)
language plpgsql
stable
as $$
begin
  return query
  select
    d.id,
    d.content,
    d.source_url,
    d.language,
    d.category,
    d.title,
    (1 - (d.embedding <=> query_embedding))::float as similarity
  from public.documents d
  where d.embedding is not null
    and (filter_language is null or d.language = filter_language)
    and (1 - (d.embedding <=> query_embedding)) >= min_similarity
  order by d.embedding <=> query_embedding
  limit match_count;
end;
$$;

-- ---------------------------------------------------------------------------
-- Row Level Security: backend uses the service role (bypasses RLS).
-- Anon/authenticated clients cannot read embeddings, chats, or leads.
-- ---------------------------------------------------------------------------
alter table public.documents enable row level security;
alter table public.chat_history enable row level security;
alter table public.leads enable row level security;
alter table public.crawl_status enable row level security;

revoke all on public.documents from anon, authenticated;
revoke all on public.chat_history from anon, authenticated;
revoke all on public.leads from anon, authenticated;
revoke all on public.crawl_status from anon, authenticated;
revoke execute on function public.match_documents(vector, int, text, float) from public, anon, authenticated;

-- ---------------------------------------------------------------------------
-- Storage bucket for ElevenLabs audio (public read of generated files only)
-- ---------------------------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('tts-audio', 'tts-audio', true)
on conflict (id) do nothing;
