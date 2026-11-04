# Architecture Decision Record

Each entry: context, decision, rationale, alternatives considered, status.

## ADR-001: Project repository location

- **Context:** The initialization prompt was run from `C:\Users\Cleoa`, which turned out to already be a git repository root (initialized, but with no commits) containing the user's entire Windows profile — `Documents`, `AppData`, `NTUSER.DAT` registry hive files, VPN configuration, etc., all untracked.
- **Decision:** Created a new, dedicated repository at `C:\Users\Cleoa\ai-stock-advisor` for this project. The pre-existing home-directory repository was left untouched.
- **Rationale:** Building the project at the profile root risked eventually committing personal and system files to version control (e.g., via an unscoped `git add -A`). A dedicated folder with its own `.gitignore` is the safer and more conventional structure, and avoids depending on exclusion rules to keep personal data out of history.
- **Alternatives considered:** Scoping the existing home-directory repo tightly with `.gitignore`/sparse-checkout; using a different path entirely. The user chose the dedicated-folder option.
- **Status:** Accepted (2026-11-01).

## ADR-002: Modular monolith over microservices

- **Context:** Project brief specifies a modular backend (portfolio, market data, quantitative engine, scoring, news, AI, evaluation) but is a solo educational project with a 10-week part-time timeline.
- **Decision:** Single FastAPI backend with clearly separated internal modules, not separate deployed services.
- **Rationale:** Microservices add deployment, networking, and operational complexity with no benefit at this scale; module boundaries inside one codebase give the same separation-of-concerns and testability without the overhead.
- **Status:** Accepted.

## ADR-003: Quantitative engine and AI explanation service are strictly separated

- **Context:** Project brief requires the AI to explain, not invent or override, financial metrics and scores.
- **Decision:** The scoring engine and quantitative analysis modules have no dependency on the AI module. The AI module only ever receives already-computed, validated evidence and returns schema-validated explanatory text; it cannot write to `scores` or recompute metrics.
- **Rationale:** This is the main integrity safeguard against the AI silently becoming the de facto source of financial conclusions, and it's what makes the system auditable (every number traces back to a deterministic, versioned calculation).
- **Status:** Accepted.

## ADR-004: Backend pinned to Python 3.13 (not 3.12)

- **Context:** Milestone 1 review asked that Python 3.12 compatibility be checked before choosing the backend runtime, rather than assuming the newest installed version (3.13.3) was fine. Only 3.13.3 was installed on the machine; 3.12 was available but not installed.
- **Decision:** Created the backend virtual environment on the already-installed Python 3.13.3 and installed the full planned dependency set (fastapi 0.162, pydantic 2.14, pydantic-settings 2.16, supabase-py 2.33, pytest 9.2, httpx, uvicorn). All packages installed and imported without issue.
- **Rationale:** The stated concern (3.12 compatibility) was about risk, not a fixed requirement for 3.12 itself. Testing the real dependency set is strictly better evidence than assuming either version works. Since every planned dependency installs cleanly on 3.13, downgrading to 3.12 would add an extra toolchain with no corresponding benefit.
- **Alternatives considered:** Installing Python 3.12 pre-emptively for "ecosystem maturity." Rejected — no actual incompatibility was found, so this would have been a cost (extra installed runtime, two Pythons to keep straight) with no evidence behind it. Will revisit if a specific future dependency (e.g., a pandas/scikit-learn version in Weeks 3-4) turns out to lag 3.13 support.
- **Status:** Accepted (2026-11-01).

## ADR-005: No Supabase service-role key in the application

- **Context:** The original draft plan included `SUPABASE_SERVICE_ROLE_KEY` in the backend's env config for admin-style operations (e.g., seeding instruments). Review flagged this as a privileged credential that shouldn't exist in the initial application at all.
- **Decision:** The backend never loads, stores, or uses the service-role key. Every database operation runs through a Supabase client constructed with the anon key plus the requesting user's own JWT (extracted from the `Authorization` header and verified via `auth.get_user()`), so Postgres Row Level Security — not application code — is what enforces ownership. Instrument-table seeding is done manually by the project owner via the Supabase SQL editor, not by a backend admin script.
- **Rationale:** A service-role key is a full RLS bypass; keeping it out of the codebase entirely removes an entire class of future mistake (e.g., accidentally using the privileged client in a request path) rather than relying on developer discipline to use it "only for admin scripts."
- **Status:** Accepted (2026-11-01).

## ADR-006: `holdings.total_cost` is a generated column, not a stored one

- **Context:** Review required that `average_buy_price` and a derived cost figure never be allowed to drift apart, and asked for the future derivation (once a transaction ledger exists) to be documented now.
- **Decision:** `total_cost` is declared `GENERATED ALWAYS AS (quantity * average_buy_price) STORED` in Postgres. The API accepts only `quantity` and `average_buy_price`; `total_cost` is read-only and cannot be independently set, so there is no code path that can make it inconsistent with the other two fields. The future (not-yet-implemented) rule for when a `transactions` ledger exists — a running weighted-average cost basis, recalculated on each buy, unaffected by sells except for reducing quantity — is documented in `docs/metrics-and-scoring.md` ahead of implementation so it isn't invented ad hoc later.
- **Rationale:** A generated column is the strongest guarantee against drift — it's enforced by the database engine itself, not by remembering to update two fields together in application code.
- **Status:** Accepted (2026-11-01).

## ADR-007: Backend independently verifies auth; frontend middleware is UX only

- **Context:** Review required that the Next.js `middleware.ts` auth redirect not be treated as a security boundary, and that the backend validate tokens itself with explicit tests for unauthenticated and cross-user access.
- **Decision:** Every protected FastAPI route depends on a function that calls Supabase's own `auth.get_user(token)` using the token from the `Authorization` header; the resulting user id is the only one ever used to scope a query — no route accepts a client-supplied user id. The Next.js middleware redirect is documented in code and here as a UX convenience that improves the experience for a logged-out user but is never relied on for access control.
- **Rationale:** A frontend redirect is trivially bypassable (direct API calls, curl, a modified build) and must never be the only thing standing between a request and another user's data.
- **Status:** Accepted (2026-11-01).

## ADR-008: Table-level GRANTs are required in addition to RLS policies

- **Context:** After connecting Milestone 1 to a real Supabase project, `/api/instruments/search` and `/api/portfolio/holdings` both returned `500` with Postgres error `42501 permission denied for table instruments/holdings`, even though both tables had RLS enabled with correct policies and the request carried a valid, verified user JWT. Diagnosis (reproduced directly against the live project via curl, bypassing the frontend) confirmed auth and JWT-forwarding were working correctly end-to-end; the failure was strictly at the database layer.
- **Root cause:** `0001_init.sql` enabled RLS and created policies, but never issued the underlying table-level `GRANT` to the `authenticated` role. In Postgres, RLS policies only filter *which rows* a role may see once that role already has baseline privilege on the table (`SELECT`/`INSERT`/etc.) — they do not grant that baseline privilege themselves. Some Supabase projects have `ALTER DEFAULT PRIVILEGES` pre-configured so new tables auto-grant to `anon`/`authenticated`; this project did not have that, so the explicit grant was required and had simply been omitted from the migration.
- **Decision:** `0001_init.sql` now explicitly grants `select` on `instruments` and `select, insert, update, delete` on `holdings` to the `authenticated` role, placed immediately after each table's RLS policies so the two are visually paired. No schema change and no seed-data change were needed — this is purely a privilege grant.
- **Rationale:** RLS and GRANTs are two independent, both-required layers (object-level privilege, then row-level filtering). Documenting this explicitly so it isn't re-discovered as a surprise on the next new table added in a future milestone.
- **Status:** Accepted (2026-11-03). Already-provisioned projects (including this one) need the GRANT statements run manually once, since the migration file running again for `CREATE TABLE IF NOT EXISTS` won't re-execute against existing tables' privileges automatically — see the instructions given to the user.

## ADR-009: Scheduled market-data ingestion runs as an isolated offline job, never inside the request-serving app

- **Context:** Milestone 2 needed a way to write shared market data (`price_history`, and the instrument master going forward) on a schedule. ADR-005 established that this application never holds a privileged Supabase credential anywhere reachable from a user request. Ingestion is squarely an admin-style, backend-owned operation on non-user-owned data - the same category ADR-005 already excluded from the live app - so this needed its own resolution rather than quietly reintroducing a service-role key into `backend/app/`.
- **Decision:** All ingestion logic (`backend/app/market_data/`, `backend/app/quantitative/`) has no FastAPI dependency and is never imported by `backend/app/main.py`. The actual privileged write happens only in `backend/scripts/ingest_prices.py`, run by `.github/workflows/ingest-prices.yml` on a schedule (plus manual `workflow_dispatch`), authenticated with `SUPABASE_SERVICE_ROLE_KEY` read directly from the environment in that one script and stored **only** as a GitHub Actions secret - never in `backend/.env`, never loaded by `app/core/config.py`, never reachable from any API route.
- **GitHub Actions safeguards (part of the same decision, implemented in the workflow file itself):**
  - Triggers are `schedule` and `workflow_dispatch` only - never `pull_request`/`pull_request_target`, which would run against a PR's (possibly forked, untrusted) code with repo context.
  - `permissions: contents: read` - the job only checks out the repo and makes outbound HTTPS calls; no write scopes.
  - The secret is referenced in exactly one place, the "Run ingestion" step's `env` block; no other workflow in this repo touches it.
  - The script itself never prints the key (confirmed in `backend/scripts/ingest_prices.py`); GitHub's automatic log-masking is a second layer, not the only one.
- **Rationale:** This preserves ADR-005's actual guarantee - no privileged credential reachable from any user request - while giving a trusted, non-internet-facing batch job the narrow privilege it legitimately needs for shared, non-user-owned data. A dedicated "service" Supabase Auth user on the normal anon+JWT path was considered and rejected: it would need an RLS insert policy scoped to a hardcoded user id, which is more fragile and no safer than a secret a user request can structurally never reach. The key's blast radius if ever leaked is stated honestly, not minimized: `service_role` bypasses RLS on every table, not just `instruments`/`price_history` - the ingestion script's own code only touches those two, but that is a property of the script, not a limit of the key, which is exactly why the safeguards above are treated as required.
- **Status:** Accepted (2026-11-04).

<!-- Add new ADRs below as decisions are made. -->
