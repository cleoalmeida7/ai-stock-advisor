from datetime import date, timedelta
from typing import Protocol

from supabase import Client

from app.market_data.provider import PriceBar


class PriceRepository(Protocol):
    def latest(self, instrument_id: str) -> PriceBar | None: ...

    def history(self, instrument_id: str, days: int) -> list[PriceBar]: ...


class SupabasePriceRepository:
    """
    Read-only, through the caller's own RLS-scoped client - same pattern as
    SupabaseInstrumentRepository. price_history grants `select` to
    `authenticated` (migration 0002); there is no write path here at all,
    since writes only ever happen through the offline ingestion job's
    separate, service-role-backed IngestionStore (app/market_data/store.py).
    See docs/architecture-decisions.md ADR-009.
    """

    def __init__(self, client: Client) -> None:
        self._client = client

    def latest(self, instrument_id: str) -> PriceBar | None:
        result = (
            self._client.table("price_history")
            .select("*")
            .eq("instrument_id", instrument_id)
            .order("price_date", desc=True)
            .limit(1)
            .maybe_single()
            .execute()
        )
        if result is None or result.data is None:
            return None
        return self._to_bar(result.data)

    def history(self, instrument_id: str, days: int) -> list[PriceBar]:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        result = (
            self._client.table("price_history")
            .select("*")
            .eq("instrument_id", instrument_id)
            .gte("price_date", cutoff)
            .order("price_date")
            .execute()
        )
        return [self._to_bar(row) for row in result.data]

    @staticmethod
    def _to_bar(row: dict) -> PriceBar:
        return PriceBar(
            price_date=date.fromisoformat(row["price_date"]),
            open=row.get("open"),
            high=row.get("high"),
            low=row.get("low"),
            close=row["close"],
            adjusted_close=row["adjusted_close"],
            volume=row.get("volume"),
        )
