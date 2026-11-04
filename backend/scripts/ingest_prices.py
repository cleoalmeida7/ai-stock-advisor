"""
Offline ingestion job - run on a schedule by .github/workflows/ingest-prices.yml,
never imported by the request-serving app. Reads SUPABASE_SERVICE_ROLE_KEY
directly from the environment here, and nowhere else in this codebase. See
docs/architecture-decisions.md ADR-009.

Usage: SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... python scripts/ingest_prices.py
"""

import os
import sys
import time
from datetime import date, timedelta

from supabase import create_client

from app.market_data.provider import MarketDataProvider, YFinanceProvider, to_yfinance_symbol
from app.market_data.store import IngestionStore, SupabaseIngestionStore

REFRESH_WINDOW_DAYS = 10
BACKFILL_DAYS = 730
MAX_ATTEMPTS = 2


def determine_start_date(store: IngestionStore, instrument_id: str) -> date:
    latest = store.latest_price_date(instrument_id)
    if latest is None:
        return date.today() - timedelta(days=BACKFILL_DAYS)
    # Re-fetch a trailing window, not just strictly-new dates: corporate
    # actions are sometimes applied retroactively by the data provider,
    # revising past adjusted_close values after the fact.
    return latest - timedelta(days=REFRESH_WINDOW_DAYS)


def ingest_one(store: IngestionStore, provider: MarketDataProvider, instrument: dict) -> int:
    yfinance_symbol = to_yfinance_symbol(instrument["exchange"], instrument["symbol"])
    start_date = determine_start_date(store, instrument["id"])

    attempts = 0
    while True:
        try:
            bars = provider.fetch_history(yfinance_symbol, start_date)
            break
        except Exception:
            attempts += 1
            if attempts >= MAX_ATTEMPTS:
                raise
            time.sleep(2)

    store.upsert_price_bars(instrument["id"], bars)
    return len(bars)


def run(store: IngestionStore, provider: MarketDataProvider) -> dict:
    """
    Orchestration kept separate from main() so tests can call this
    directly with fakes - no real env vars, network, or Supabase project
    needed. main() is the only place real credentials/network are touched.
    """
    total_rows = 0
    failed_symbols: list[str] = []

    for instrument in store.list_instruments():
        try:
            count = ingest_one(store, provider, instrument)
            total_rows += count
            print(f"{instrument['symbol']}: {count} rows upserted")
        except Exception as exc:
            failed_symbols.append(instrument["symbol"])
            print(f"{instrument['symbol']}: FAILED - {exc}", file=sys.stderr)

    return {"total_rows": total_rows, "failed_symbols": failed_symbols}


def main() -> None:
    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    store = SupabaseIngestionStore(client)
    provider = YFinanceProvider()

    results = run(store, provider)
    print(f"Done. {results['total_rows']} rows upserted.")
    if results["failed_symbols"]:
        print(f"Failed: {', '.join(results['failed_symbols'])}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
