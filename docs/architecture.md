# Architecture (Planning Stage)

Status: proposed, not yet implemented. This document will be revised as the system is built.

## Guiding principle

The quantitative engine is the source of truth for every number and score. The AI explanation service may only *explain* what the quantitative engine already produced — it cannot invent metrics, override scores, or generate independent price targets. This separation is the single most important architectural boundary in the system, because it's what keeps the AI from quietly becoming the thing users trust instead of the math.

## Components

1. **Frontend (Next.js/TypeScript)** — dashboard, portfolio views, charts, CSV upload UI. Talks only to the backend API; never calls Supabase or the AI provider directly, and never holds API keys.
2. **Backend API (FastAPI)** — the single entry point for the frontend. Owns request validation (Pydantic), auth checks, and orchestration across the other backend modules.
3. **Portfolio management** — holdings, transactions, cost basis, CSV import/validation.
4. **Market-data ingestion** — pulls OHLCV and corporate-action data from yfinance initially, normalises it, records source + retrieval timestamp. Built behind an interface so the provider can be swapped without touching callers.
5. **Instrument mapping** — NSE/BSE security master; resolves the "same company, two exchange listings" problem.
6. **Quantitative analysis engine** — pandas/NumPy modules for returns, risk metrics, fundamentals-derived ratios. Pure functions over validated inputs; independently unit-tested; versioned.
7. **Scoring engine** — deterministic, weighted, versioned scoring over the quantitative engine's outputs. Produces metric-level contributions, not just a final number. Can return "insufficient evidence."
8. **News ingestion** — pulls and deduplicates company-relevant news, retains source/timestamps.
9. **AI explanation service** — single provider initially, behind an interface (`backend/app/ai/`). Receives structured evidence from the backend, returns schema-validated JSON, never writes to the scoring tables.
10. **Analysis history** — persists each analysis run's full input snapshot, scoring version, and AI output together, so a run can be reproduced or audited later.
11. **Evaluation engine** — compares logged analysis runs against subsequent price/benchmark outcomes; tracks look-ahead bias controls.
12. **Database (Supabase/PostgreSQL)** — persistence and Row Level Security for user-owned data.

## Data flow (high level)

```
yfinance ─▶ market-data ingestion ─▶ price history (DB)
                                           │
company news sources ─▶ news ingestion ─▶ news articles (DB)
                                           │
                                           ▼
                              quantitative analysis engine
                                           │
                              ┌────────────┴────────────┐
                              ▼                          ▼
                        scoring engine            analysis snapshot (DB)
                              │                          │
                              ▼                          │
                   AI explanation service ◀──────────────┘
                   (structured evidence in, schema-validated explanation out)
                              │
                              ▼
                     analysis run + AI explanation (DB)
                              │
                              ▼
                     evaluation engine (prospective, from Week 6)
```

The frontend only ever reads from the backend API, which reads from the DB and triggers ingestion/analysis/AI calls as needed — it never talks to yfinance, the news sources, or the AI provider directly.

## API boundaries

Proposed, not all implemented immediately — see section below and `docs/architecture-decisions.md` for what ships in Milestone 1 vs later:

- ✅ `/api/portfolio/holdings` (GET/POST/DELETE) — Milestone 1
- `/api/portfolio/import` — not yet built
- ✅ `/api/instruments/search` — Milestone 1
- `/api/instruments/{id}` — not yet built (not needed; search covers lookup today)
- ✅ `/api/market/{instrument_id}/history` — Milestone 2 (range-limited, no `/overview` yet)
- ✅ `/api/analysis/{instrument_id}` — Milestone 2 (on-demand; no `/run`/`/history` persistence yet - see "Explicitly out of scope" in the Milestone 2 plan)
- `/api/news`, `/api/news/{id}` — not yet built (Weeks 5-6)
- `/api/ai/explain`, `/api/ai/explanations/{id}` — not yet built (Weeks 5-6)
- ✅ `/api/portfolio/metrics` — Milestone 2 (valuation, P/L, sector concentration, missing/stale-price flagging)
- `/api/portfolio/risk`, `/api/portfolio/benchmark` — not yet built
- `/api/evaluation/summary`, `/api/evaluation/history` — not yet built (Weeks 9-10)

## Database relationships (summary)

See the "Database Design" section of the original project brief for full detail. Core entities: `users`, `instruments`, `holdings`, `transactions`, `price_history`, `fundamentals`, `news_articles`, `analysis_runs`, `analysis_snapshots`, `scores`, `ai_explanations`, `benchmarks`, `evaluation_records`. Relationships, keys, and indexes will be formalised as a migration set at Milestone 1, not guessed here.

## Architectural decisions log

See `docs/architecture-decisions.md`.
