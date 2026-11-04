from datetime import date

import pandas as pd

from app.market_data import provider as provider_module
from app.market_data.provider import YFinanceProvider


def test_fetch_history_requests_auto_adjust_false_and_maps_columns_correctly(monkeypatch) -> None:
    """
    The critical regression test for the adjusted-vs-unadjusted rule:
    asserts auto_adjust=False was actually requested, and that close /
    adjusted_close map to the distinct 'Close' / 'Adj Close' source
    columns without being swapped or collapsed into one value. The fixture
    deliberately makes them different so a bug here would fail loudly.
    """
    captured: dict = {}

    class FakeTicker:
        def __init__(self, symbol: str) -> None:
            captured["symbol"] = symbol

        def history(self, start: str, auto_adjust: bool) -> pd.DataFrame:
            captured["start"] = start
            captured["auto_adjust"] = auto_adjust
            index = pd.to_datetime(["2024-01-02", "2024-01-03"])
            return pd.DataFrame(
                {
                    "Open": [100.0, 101.0],
                    "High": [102.0, 103.0],
                    "Low": [99.0, 100.0],
                    "Close": [101.0, 102.0],
                    "Adj Close": [95.0, 96.0],
                    "Volume": [1000, 1100],
                },
                index=index,
            )

    monkeypatch.setattr(provider_module.yf, "Ticker", FakeTicker)

    bars = YFinanceProvider().fetch_history("RELIANCE.NS", date(2024, 1, 1))

    assert captured["symbol"] == "RELIANCE.NS"
    assert captured["auto_adjust"] is False

    assert len(bars) == 2
    assert bars[0].price_date == date(2024, 1, 2)
    assert bars[0].close == 101.0
    assert bars[0].adjusted_close == 95.0
    assert bars[0].close != bars[0].adjusted_close
    assert bars[1].close == 102.0
    assert bars[1].adjusted_close == 96.0


def test_fetch_history_omits_rows_with_nan_close(monkeypatch) -> None:
    """
    Reproduces what the live yfinance API actually returned when fetched
    mid-session: the most recent day's Close/Adj Close come back as NaN
    before the trading day finalizes. Must be omitted, never stored as a
    fabricated 0 or passed through as NaN (which isn't even valid JSON).
    """

    class PartiallyNanTicker:
        def __init__(self, symbol: str) -> None:
            pass

        def history(self, start: str, auto_adjust: bool) -> pd.DataFrame:
            index = pd.to_datetime(["2026-11-02", "2026-11-03"])
            return pd.DataFrame(
                {
                    "Open": [100.0, 103.0],
                    "High": [102.0, float("nan")],
                    "Low": [99.0, float("nan")],
                    "Close": [101.0, float("nan")],
                    "Adj Close": [95.0, float("nan")],
                    "Volume": [1000, 500],
                },
                index=index,
            )

    monkeypatch.setattr(provider_module.yf, "Ticker", PartiallyNanTicker)

    bars = YFinanceProvider().fetch_history("RELIANCE.NS", date(2026, 11, 1))

    assert len(bars) == 1
    assert bars[0].price_date == date(2026, 11, 2)
    assert bars[0].close == 101.0


def test_fetch_history_returns_empty_list_for_empty_response(monkeypatch) -> None:
    class EmptyTicker:
        def __init__(self, symbol: str) -> None:
            pass

        def history(self, start: str, auto_adjust: bool) -> pd.DataFrame:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Adj Close", "Volume"])

    monkeypatch.setattr(provider_module.yf, "Ticker", EmptyTicker)

    bars = YFinanceProvider().fetch_history("UNKNOWN.NS", date(2024, 1, 1))

    assert bars == []
