-- Milestone 2: historical prices + a primary sector per instrument.
-- Run this in the Supabase SQL editor for your project, after 0001_init.sql.
-- Like 0001, this app has no service-role key, so this file is applied by
-- hand - except price_history will later be WRITTEN ONLY by the offline
-- ingestion job (see backend/scripts/ingest_prices.py), which runs with its
-- own service-role credential that exists ONLY as a GitHub Actions secret,
-- never in this application. See docs/architecture-decisions.md ADR-009.

alter table public.instruments add column if not exists sector text;

create table if not exists public.price_history (
    id uuid primary key default gen_random_uuid(),
    instrument_id uuid not null references public.instruments (id),
    price_date date not null,
    open numeric,
    high numeric,
    low numeric,
    close numeric not null,
    adjusted_close numeric not null,
    volume bigint,
    source text not null default 'yfinance',
    retrieved_at timestamptz not null default now(),
    unique (instrument_id, price_date)
);

create index if not exists price_history_instrument_date_idx
    on public.price_history (instrument_id, price_date);

alter table public.price_history enable row level security;

drop policy if exists "price_history is readable by authenticated users" on public.price_history;

create policy "price_history is readable by authenticated users"
    on public.price_history
    for select
    to authenticated
    using (true);

grant select on public.price_history to authenticated;
