from datetime import date

from app.market_data.provider import PriceBar


class FakeMarketDataProvider:
    """
    Returns canned bars, or simulates N transient failures before
    succeeding (or always failing), per symbol. Used so ingestion-logic
    tests never touch real yfinance or the network.
    """

    def __init__(
        self,
        bars_by_symbol: dict[str, list[PriceBar]] | None = None,
        fail_counts: dict[str, int] | None = None,
    ) -> None:
        self._bars_by_symbol = bars_by_symbol or {}
        self._remaining_failures = dict(fail_counts or {})
        self.calls: list[tuple[str, date]] = []

    def fetch_history(self, yfinance_symbol: str, start_date: date) -> list[PriceBar]:
        self.calls.append((yfinance_symbol, start_date))
        remaining = self._remaining_failures.get(yfinance_symbol, 0)
        if remaining > 0:
            self._remaining_failures[yfinance_symbol] = remaining - 1
            raise RuntimeError(f"simulated transient failure for {yfinance_symbol}")
        if remaining < 0:
            raise RuntimeError(f"simulated permanent failure for {yfinance_symbol}")
        return self._bars_by_symbol.get(yfinance_symbol, [])


class FakeIngestionStore:
    def __init__(
        self,
        instruments: list[dict],
        existing_latest_dates: dict[str, date] | None = None,
    ) -> None:
        self._instruments = instruments
        self._latest_dates = dict(existing_latest_dates or {})
        self.upserted: dict[str, list[PriceBar]] = {}

    def list_instruments(self) -> list[dict]:
        return self._instruments

    def latest_price_date(self, instrument_id: str) -> date | None:
        return self._latest_dates.get(instrument_id)

    def upsert_price_bars(self, instrument_id: str, bars: list[PriceBar]) -> None:
        self.upserted[instrument_id] = bars
