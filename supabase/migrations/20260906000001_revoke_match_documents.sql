-- Prevent browser/anon clients from calling similarity search directly.
-- The FastAPI service role still bypasses this grant.

revoke execute on function public.match_documents(vector, int, text, float)
  from public, anon, authenticated;
