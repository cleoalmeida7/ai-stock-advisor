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

<!-- Add new ADRs below as decisions are made. -->
