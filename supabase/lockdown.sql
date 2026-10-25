-- Run ONCE in Supabase > SQL Editor, AFTER the app has started and created its tables.
-- Why: Supabase exposes every table in the "public" schema through its own REST API.
-- Turning on Row Level Security with no policies blocks that route. Your app connects directly
-- as the database owner, so it keeps working.
do $$ declare t record; begin
  for t in select tablename from pg_tables where schemaname='public' loop
    execute format('alter table public.%I enable row level security', t.tablename);
  end loop;
end $$;
