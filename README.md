# AI Stock Advisor

A personal CSE portfolio project: a research and educational web application that analyses Indian equity portfolios (NSE/BSE) using quantitative financial analysis, financial news intelligence, and AI-generated explanations.

**This is not a guaranteed stock-prediction system or a personalised investment advisory service.**

## Status

Milestone 1 in progress: Supabase-authenticated manual portfolio holdings, backed by an instrument master, with a backend and frontend that are each independently tested. See `docs/architecture.md` for the overall design and `docs/architecture-decisions.md` for the decisions made along the way.

## Features (planned)

- Portfolio management: manual entry, CSV import, cost basis, realised/unrealised P/L, sector allocation.
- Quantitative analysis: returns, moving averages, momentum, volatility, drawdown, beta, correlation, selected fundamentals.
- Portfolio risk analysis: Sharpe ratio, max drawdown, beta vs Nifty 50, correlation heatmap, sector concentration, benchmark comparison.
- Financial news intelligence: company-linked news, duplicate/syndication detection, source attribution.
- AI-generated explanations: schema-validated, evidence-grounded explanations of metrics, news, and portfolio movements — never a replacement for the deterministic quantitative engine.
- Experimental Buy/Hold/Sell research signals from a deterministic, versioned scoring engine (optional, introduced only after core calculations are tested).
- Analysis history and prospective evaluation against benchmarks.

## Technology stack

- **Frontend:** Next.js, TypeScript, Tailwind CSS.
- **Backend:** Python, FastAPI, Pydantic.
- **Database:** Supabase (PostgreSQL), Row Level Security.
- **Analysis:** pandas, NumPy, scikit-learn (where appropriate).
- **Market data (initial):** yfinance — prototyping only; see `docs/known-limitations.md`.
- **AI:** one provider initially, behind a swappable interface; schema-validated outputs.
- **Scheduling:** GitHub Actions.
- **Testing:** pytest + httpx (backend), Jest + React Testing Library (frontend).

## Architecture

See `docs/architecture.md`. Notably: this backend has **no privileged Supabase credential** — every request runs as the caller's own JWT, and Postgres Row Level Security enforces data ownership (see ADR-005 and ADR-007 in `docs/architecture-decisions.md`).

## Setup

### 1. Create a Supabase project

Create a free project at supabase.com. From Project Settings → API, copy the **Project URL** and the **anon/public key** (not the service-role key — this app never uses it).

### 2. Run the database migration and seed

In the Supabase SQL editor, run, in order:

1. `database/migrations/0001_init.sql`
2. `database/seed/instruments_seed.sql` (a ~20-symbol development seed, not a full NSE/BSE master — see `docs/known-limitations.md`)

### 3. Configure environment variables

```
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Fill in your Supabase URL and anon key in both files. Never commit the filled-in `.env` files (they're gitignored).

### 4. Run the backend

```
cd backend
py -3.13 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

### 5. Run the frontend

```
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` — it redirects to `/login`, then `/portfolio` after signing up/in.

## Environment variables

See `backend/.env.example` and `frontend/.env.example`. Never commit a populated `.env` file.

## Testing

```
# Backend - no live Supabase project needed; runs against in-memory fakes
cd backend && .venv\Scripts\pytest -v

# Frontend
cd frontend && npm test
```

A full browser smoke test additionally requires a real Supabase project (step 1-3 above) — the automated suites above do not depend on one.

## Known limitations

See `docs/known-limitations.md` — maintained continuously as the project evolves.
