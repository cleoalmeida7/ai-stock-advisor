# Metrics and Scoring

Status: Milestone 2's quantitative engine (`backend/app/quantitative/`) is implemented and tested, documented below. The scoring engine (Weeks 5-6) is not yet built. This file must never describe a metric or scoring weight that hasn't actually been implemented and tested.

## Adjusted vs. unadjusted price - the rule every metric below follows

`price_history` stores both `close` (raw/unadjusted) and `adjusted_close` (split/dividend-adjusted) explicitly, never conflated. **Every metric in this document uses `adjusted_close` exclusively** - using raw `close` would produce a fake jump or drop on every split/dividend ex-date, since the price series wouldn't reflect the actual economic return. `close` (unadjusted) is used in exactly one place in this codebase: **current market value / portfolio valuation** (`app/quantitative/portfolio_metrics.py`), because `adjusted_close` is a backward-looking return-calculation construct, not a real quoted/tradable price - using it there would misstate what a position is actually worth today. This distinction is verified by a dedicated regression test in every metric module below (`tests/quantitative/fixtures.py::divergent_series`), not just asserted in prose.

## Shared conventions

- Every function takes `bars: list[PriceBar]` sorted ascending by `price_date` (see `app/market_data/provider.py`).
- Every scalar metric returns a `MetricValue(value, insufficient_data, observations_used)` (`app/quantitative/types.py`) - `insufficient_data=True` is an explicit, first-class outcome whenever there isn't enough history for the requested window. A metric **never** returns a partial or guessed value instead.
- `METRICS_VERSION` (`app/quantitative/__init__.py`, currently `"1.0"`) is recorded alongside any computed result so the formula version in use is always traceable, even though Milestone 2 does not yet persist analysis runs (that's a later milestone - see `docs/architecture-decisions.md`).

## Daily and cumulative returns - `app/quantitative/returns.py`

- **Daily return:** `r_t = adjusted_close_t / adjusted_close_{t-1} - 1`. Returns a plain `list[float]`, one shorter than the input; empty if fewer than 2 bars (a series is its own insufficient-data signal).
- **Cumulative return:** `adjusted_close_last / adjusted_close_first - 1` over whatever window of bars is passed in. `insufficient_data` if fewer than 2 bars.
- **Inputs:** `bars`. **Window:** whatever's passed in by the caller. **Missing data:** gaps in `price_history` simply mean fewer bars are passed in - never forward-filled or zero-filled.
- **Tests:** `tests/quantitative/test_returns.py`.

## Moving averages - `app/quantitative/moving_averages.py`

- **Formula:** `simple_moving_average(bars, window)` = mean of `adjusted_close` over the most recent `window` bars.
- **Windows used by the API:** 20, 50, 200 days (`/api/analysis/{instrument_id}` calls this three times).
- **Missing data:** `insufficient_data=True` (not a partial average over fewer rows) when fewer than `window` bars exist.
- **Limitation:** "day" here means an available trading-day row in `price_history`, not a calendar day - holidays and gaps are already absent from the input, not specially handled.
- **Tests:** `tests/quantitative/test_moving_averages.py`.

## Momentum - `app/quantitative/momentum.py`

- **Formula:** cumulative `adjusted_close` return over the trailing `window` trading-day bars, default `window=90` (`DEFAULT_MOMENTUM_WINDOW_DAYS`).
- **Known limitation - explicitly simplified:** this is **not** the academic 12-1 momentum factor used in quantitative finance research (which typically excludes the most recent month). It's a simpler, directly-interpretable "how much has this moved over the trailing N trading days" figure, appropriate for an educational tool - not a trading signal, and never presented as one.
- **Missing data:** `insufficient_data=True` when fewer than `window` bars exist.
- **Tests:** `tests/quantitative/test_momentum.py`.

## Volatility - `app/quantitative/volatility.py`

- **Formula:** `annualized_volatility(bars, window)` = `stdev(daily_returns over the trailing window) * sqrt(252)`. Always annualized and always labeled as such - a raw daily figure is never presented unannotated.
- **Missing data:** needs `window + 1` bars (to produce `window` daily returns); `insufficient_data=True` otherwise.
- **Edge case:** a perfectly flat price series correctly produces `0.0`, not `insufficient_data` - zero real volatility is a valid, distinct outcome from "not enough data to know."
- **Tests:** `tests/quantitative/test_volatility.py`.

## Maximum drawdown - `app/quantitative/drawdown.py`

- **Formula:** `drawdown_t = adjusted_close_t / running_peak_t - 1`; result = `min(drawdown_t)` over the given window. `running_peak_t` is the highest `adjusted_close` seen up to and including bar `t`.
- **Missing data:** `insufficient_data=True` with fewer than 2 bars.
- **Tests:** `tests/quantitative/test_drawdown.py`.

## Portfolio-level metrics - `app/quantitative/portfolio_metrics.py`

Uses **unadjusted** `close` (not `adjusted_close`) for valuation - the one deliberate exception to the rule above, since `adjusted_close` would misstate what a position is worth today.

- **Per-holding market value:** `quantity * latest_close`.
- **Total value / cost basis / unrealized P/L / overall return:** computed **only over holdings with a current, non-stale price** (the "priced" subset) - cost basis for excluded holdings is never mixed into a total that excludes their value, which would silently distort P/L. `overall_return = unrealized_pl / total_cost_basis`, `None` if cost basis is `0` (e.g. no priced holdings at all).
- **Missing/stale price handling - never silent:** a holding with no `price_history` row at all, or whose latest row is older than `STALENESS_THRESHOLD_DAYS` (5 calendar days), is excluded from every total above but recorded in `unpriced_holdings` (`reason`: `"no_price_data"` or `"stale_price"`); `valuation_complete` is `False` whenever `unpriced_holdings` is non-empty. The frontend must surface this, not just show a number.
- **Per-holding weight / sector concentration:** `market_value / total_value`, grouped by `instrument.sector` (or `"Unclassified"` if `null`) for concentration. Only computed over the priced subset, for the same reason as above.
- **Known limitation:** `overall_return` is a simple (not time-weighted or money-weighted) return - computing either of those needs cash-flow timing from a transaction ledger that doesn't exist yet (see ADR-006 / the weighted-average-cost-basis section above).
- **Tests:** `tests/quantitative/test_portfolio_metrics.py`.

## Future: weighted-average cost basis from the transaction ledger (not yet implemented)

Documented now, ahead of implementation, so it isn't invented ad hoc when the `transactions` table is actually built (see `docs/architecture-decisions.md` ADR-006). Today (Milestone 1), `holdings.quantity` and `holdings.average_buy_price` are directly user-entered (`source = 'manual'`); `total_cost` is a Postgres generated column (`quantity * average_buy_price`), never stored independently.

Once a `transactions` ledger exists, a `source = 'computed'` holding will be derived as follows:

- **On a buy** of `buy_qty` at `buy_price`: `new_average_buy_price = (old_qty * old_average_buy_price + buy_qty * buy_price) / (old_qty + buy_qty)`; `new_qty = old_qty + buy_qty`.
- **On a sell** of `sell_qty`: `new_qty = old_qty - sell_qty`; `average_buy_price` is unchanged (standard weighted-average cost basis — a sell realises P/L against the existing average cost, it does not change the average cost of what remains).
- `total_cost` continues to be `quantity * average_buy_price`, still generated, never separately stored.
- Direct editing of `quantity`/`average_buy_price` via the API will be restricted for `source = 'computed'` holdings at that point, since they become derived from the transaction history rather than user-entered.

