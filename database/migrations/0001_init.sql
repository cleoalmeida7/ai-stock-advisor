-- Milestone 1: instruments (NSE/BSE master) + holdings (manual portfolio entry)
-- Run this in the Supabase SQL editor for your project. No backend code runs
-- this automatically - there is no service-role key in the application
-- (see docs/architecture-decisions.md ADR-005), so schema changes are applied
-- by hand via this file for now.

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- instruments: the NSE/BSE security master.
--
-- data_source distinguishes how a row got here. Today only 'dev_seed' exists
-- (see database/seed/instruments_seed.sql, ~20 symbols for development only).
-- A future bulk import (e.g. 'nse_bhavcopy_import') extends this same table -
-- it does not require a schema change, and no code or doc may treat the
-- dev seed as a complete exchange listing. See docs/known-limitations.md.
-- ---------------------------------------------------------------------------
create table if not exists public.instruments (
    id uuid primary key default gen_random_uuid(),
    exchange text not null check (exchange in ('NSE', 'BSE')),
    symbol text not null,
    company_name text not null,
    data_source text not null default 'dev_seed',
    verified_at timestamptz,
    created_at timestamptz not null default now(),
    unique (exchange, symbol)
);

alter table public.instruments enable row level security;

-- Public read for any authenticated user; no client-side insert/update/delete.
-- Seeding/maintaining this table is a manual, out-of-band operation (SQL
-- editor) precisely because the app holds no privileged key to do it itself.
create policy "instruments are readable by authenticated users"
    on public.instruments
    for select
    to authenticated
    using (true);

-- RLS policies only restrict *which rows* a role can see - the role still
-- needs a base table-level GRANT to query the table at all. Some Supabase
-- projects pre-configure default privileges so new tables grant to
-- anon/authenticated automatically; this one doesn't, so it's explicit here.
grant select on public.instruments to authenticated;

-- ---------------------------------------------------------------------------
-- holdings: a user's manually-entered positions (Milestone 1 scope).
--
-- total_cost is a GENERATED column, not independently stored - it can never
-- drift from quantity * average_buy_price because there is no way to set it
-- directly. See docs/architecture-decisions.md ADR-006 and
-- docs/metrics-and-scoring.md for the future (not yet implemented)
-- weighted-average-cost derivation once a transactions ledger exists.
--
-- source = 'manual' today; a later transactions-ledger milestone introduces
-- source = 'computed' rows without needing a schema break here.
-- ---------------------------------------------------------------------------
create table if not exists public.holdings (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id) on delete cascade,
    instrument_id uuid not null references public.instruments (id),
    quantity numeric not null check (quantity > 0),
    average_buy_price numeric not null check (average_buy_price > 0),
    total_cost numeric generated always as (quantity * average_buy_price) stored,
    source text not null default 'manual' check (source in ('manual', 'computed')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id, instrument_id)
);

alter table public.holdings enable row level security;

create policy "users can select their own holdings"
    on public.holdings
    for select
    to authenticated
    using (auth.uid() = user_id);

create policy "users can insert their own holdings"
    on public.holdings
    for insert
    to authenticated
    with check (auth.uid() = user_id);

create policy "users can update their own holdings"
    on public.holdings
    for update
    to authenticated
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

create policy "users can delete their own holdings"
    on public.holdings
    for delete
    to authenticated
    using (auth.uid() = user_id);

create index if not exists holdings_user_id_idx on public.holdings (user_id);

-- See the comment above the instruments GRANT: RLS alone does not grant
-- table access, it only filters rows once access is already granted.
grant select, insert, update, delete on public.holdings to authenticated;
