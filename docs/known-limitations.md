# Known Limitations (Living Document)

Update this file whenever a limitation is discovered or resolved. Do not delete historical entries without noting how they were resolved.

## Data

- **yfinance** is used for prototyping only. It does not reliably provide point-in-time fundamentals (i.e., what was publicly known on a given historical date) — see `docs/evaluation-method.md`. It can also silently return incomplete or adjusted-only series. The provider is kept behind an interface so it can be replaced.
- **NSE/BSE symbol mapping** is non-trivial: the same company can be listed on both exchanges with different symbols, and symbols can be reused or changed over time. The instrument master must resolve this, not assume a 1:1 symbol-to-company mapping.
- **Corporate actions** (splits, bonuses, dividends) are not uniformly reliable in free data sources. Where confidence is low, the system must flag the data as unverified rather than silently adjusting it.
- **Fundamental data** publication dates and reporting periods are not the same thing, and free sources often blur them. This directly affects the integrity of any fundamentals-based scoring.
- **Instrument master is a ~20-symbol development seed** (`database/seed/instruments_seed.sql`), not a complete NSE/BSE listing. It exists only so Milestone 1's holding-creation validation and symbol search have real rows to work against. `instruments.data_source` distinguishes seed rows (`'dev_seed'`) from any future bulk import, which will extend the same table rather than requiring a schema change. No code or documentation should imply this seed is a complete exchange master.
- **Sector classifications are an approximate, development-only taxonomy.** `instruments.sector` (added in Milestone 2) was hand-assigned for the 20 seed symbols using a simplified GICS-like grouping (e.g. "Financial Services", "Information Technology"), not a licensed sector-data feed. It's accurate enough for Milestone 2's portfolio concentration metric but must not be presented as an authoritative classification. The column stays nullable so future, unclassified instruments aren't blocked on this.

## AI

- AI explanations are not a source of financial fact. They may only explain evidence the backend already computed or retrieved.
- No cross-model agreement is treated as evidence of correctness.
- Hallucination and unsupported-claim risk exists for any LLM provider; schema validation reduces but does not eliminate this risk.

## Evaluation

- Historical backtesting is valid only for price-based components (momentum, volatility, drawdown, returns). Fundamentals-based scoring **cannot** be claimed as historically validated using today's fundamentals data applied to past dates — this would be look-ahead bias.
- Prospective evaluation (logging real analysis runs and checking outcomes later) only begins once the full pipeline is operational (target: Week 6), so statistically meaningful evaluation results will take time to accumulate.

## Environment (as of initial inspection, 2026-11-01)

- Python is correctly installed (3.13.3) but only reachable via the `py` launcher or the full path to `Python313`; the bare `python`/`pip` commands on this machine resolve to a non-functional Microsoft Store stub. Scripts and docs should use `py` explicitly or rely on a virtual environment's own activated interpreter.
- Docker is not installed. Docker is optional per the project brief ("where it improves reproducibility") — not currently a blocker.
- GitHub CLI (`gh` 2.103.3) was installed via winget during this session; authentication is a manual step for the user (`gh auth login`), not something this assistant can complete.
- Backend dependency set (FastAPI, Pydantic v2, supabase-py, pytest, httpx, uvicorn) was verified to install and import cleanly on the already-installed Python 3.13.3 — no need for a second Python version. See `docs/architecture-decisions.md` ADR-004.
- A full browser smoke test of Milestone 1 end-to-end is not possible until the user creates their own Supabase project and supplies real anon-key credentials in `backend/.env` and `frontend/.env`. Backend correctness is instead verified by an automated test suite running against in-memory fakes (no live Supabase needed) — see `backend/tests/`.
