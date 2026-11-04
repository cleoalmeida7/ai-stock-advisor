from datetime import date
from typing import Protocol

from supabase import Client

from app.market_data.provider import PriceBar


class IngestionStore(Protocol):
    def list_instruments(self) -> list[dict]: ...

    def latest_price_date(self, instrument_id: str) -> date | None: ...

    def upsert_price_bars(self, instrument_id: str, bars: list[PriceBar]) -> None: ...


class SupabaseIngestionStore:
    """
    Backed by a service-role Supabase client. Only ever instantiated by
    backend/scripts/ingest_prices.py, an isolated offline job - never by
    the request-serving FastAPI app, which has no service-role client
    anywhere in its own code. See docs/architecture-decisions.md ADR-009.
    """

    def __init__(self, client: Client) -> None:
        self._client = client

    def list_instruments(self) -> list[dict]:
        result = self._client.table("instruments").select("id, exchange, symbol").execute()
        return result.data

    def latest_price_date(self, instrument_id: str) -> date | None:
        result = (
            self._client.table("price_history")
            .select("price_date")
            .eq("instrument_id", instrument_id)
            .order("price_date", desc=True)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        return date.fromisoformat(result.data[0]["price_date"])

    def upsert_price_bars(self, instrument_id: str, bars: list[PriceBar]) -> None:
        if not bars:
            return
        rows = [
            {
                "instrument_id": instrument_id,
                "price_date": bar.price_date.isoformat(),
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "adjusted_close": bar.adjusted_close,
                "volume": bar.volume,
                "source": "yfinance",
            }
            for bar in bars
        ]
        self._client.table("price_history").upsert(rows, on_conflict="instrument_id,price_date").execute()
