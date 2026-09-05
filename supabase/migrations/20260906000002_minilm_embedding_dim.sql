-- Switch RAG vectors from BAAI/bge-m3 (1024) to all-MiniLM-L6-v2 (384).
-- Re-run knowledge-base/pipeline.py after applying this migration.

drop index if exists public.documents_embedding_hnsw;

alter table public.documents
  drop column if exists embedding;

alter table public.documents
  add column embedding vector(384);

create index if not exists documents_embedding_hnsw
  on public.documents using hnsw (embedding vector_cosine_ops);

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

revoke execute on function public.match_documents(vector, int, text, float)
  from public, anon, authenticated;
