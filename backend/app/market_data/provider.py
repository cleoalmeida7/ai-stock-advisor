import math
from dataclasses import dataclass
from datetime import date
from typing import Protocol

import yfinance as yf


@dataclass(frozen=True)
class PriceBar:
    price_date: date
    open: float | None
    high: float | None
    low: float | None
    close: float
    adjusted_close: float
    volume: int | None


class MarketDataProvider(Protocol):
    def fetch_history(self, yfinance_symbol: str, start_date: date) -> list[PriceBar]: ...


_EXCHANGE_SUFFIXES = {"NSE": ".NS", "BSE": ".BO"}


def to_yfinance_symbol(exchange: str, symbol: str) -> str:
    """
    Derived at request time rather than stored on the instrument - a
    deterministic mapping, not data. If a future symbol doesn't follow the
    pattern, that's a known limitation to revisit, not a reason to add a
    column now. See docs/known-limitations.md.
    """
    suffix = _EXCHANGE_SUFFIXES.get(exchange)
    if suffix is None:
        raise ValueError(f"Unknown exchange '{exchange}' - no yfinance suffix mapping")
    return f"{symbol}{suffix}"


class YFinanceProvider:
    """
    auto_adjust=False is required, not optional. yfinance defaults to
    auto_adjust=True, which overwrites Close with the adjusted value and
    drops the separate Adj Close column entirely - collapsing exactly the
    raw-vs-adjusted distinction this application depends on throughout
    (see docs/metrics-and-scoring.md). This is asserted directly in
    tests/market_data/test_yfinance_provider.py against a mocked response,
    not just assumed from the parameter name.
    """

    def fetch_history(self, yfinance_symbol: str, start_date: date) -> list[PriceBar]:
        ticker = yf.Ticker(yfinance_symbol)
        history = ticker.history(start=start_date.isoformat(), auto_adjust=False)

        bars = []
        for index, row in history.iterrows():
            close, adjusted_close = row["Close"], row["Adj Close"]
            if _is_nan(close) or _is_nan(adjusted_close):
                # The most recent trading day can come back with no close yet
                # if fetched before the session finalizes (observed live:
                # today's bar returned NaN mid-day). Never store a fabricated
                # or placeholder price for it - just omit the bar entirely;
                # the next scheduled run picks it up once it's real.
                continue
            bars.append(
                PriceBar(
                    price_date=index.date(),
                    open=_as_float_or_none(row.get("Open")),
                    high=_as_float_or_none(row.get("High")),
                    low=_as_float_or_none(row.get("Low")),
                    close=float(close),
                    adjusted_close=float(adjusted_close),
                    volume=_as_int_or_none(row.get("Volume")),
                )
            )
        return bars


def _is_nan(value) -> bool:
    return isinstance(value, float) and math.isnan(value)


def _as_float_or_none(value) -> float | None:
    if value is None or _is_nan(value):
        return None
    return float(value)


def _as_int_or_none(value) -> int | None:
    if value is None or _is_nan(value):
        return None
    return int(value)
