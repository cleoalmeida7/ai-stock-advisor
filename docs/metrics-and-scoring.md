# Metrics and Scoring (Planning Stage)

Status: placeholder. This document will be filled in with formal definitions as each metric module is implemented and tested in Weeks 3-4 and the scoring engine is built in Weeks 5-6. It must never describe a metric or scoring weight that hasn't actually been implemented and tested.

Each entry, once added, must specify: formula, required inputs, observation window, missing-data behaviour, known limitations, and the module's test file.

## Future: weighted-average cost basis from the transaction ledger (not yet implemented)

Documented now, ahead of implementation, so it isn't invented ad hoc when the `transactions` table is actually built (see `docs/architecture-decisions.md` ADR-006). Today (Milestone 1), `holdings.quantity` and `holdings.average_buy_price` are directly user-entered (`source = 'manual'`); `total_cost` is a Postgres generated column (`quantity * average_buy_price`), never stored independently.

Once a `transactions` ledger exists, a `source = 'computed'` holding will be derived as follows:

- **On a buy** of `buy_qty` at `buy_price`: `new_average_buy_price = (old_qty * old_average_buy_price + buy_qty * buy_price) / (old_qty + buy_qty)`; `new_qty = old_qty + buy_qty`.
- **On a sell** of `sell_qty`: `new_qty = old_qty - sell_qty`; `average_buy_price` is unchanged (standard weighted-average cost basis — a sell realises P/L against the existing average cost, it does not change the average cost of what remains).
- `total_cost` continues to be `quantity * average_buy_price`, still generated, never separately stored.
- Direct editing of `quantity`/`average_buy_price` via the API will be restricted for `source = 'computed'` holdings at that point, since they become derived from the transaction history rather than user-entered.

