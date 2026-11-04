"""
Daily and cumulative returns, computed from adjusted_close only - never
raw close. See docs/metrics-and-scoring.md for the adjusted-vs-unadjusted
usage rule that this whole package follows.
"""

from app.market_data.provider import PriceBar
from app.quantitative.types import MetricValue


def daily_returns(bars: list[PriceBar]) -> list[float]:
    """
    r_t = adjusted_close_t / adjusted_close_{t-1} - 1. `bars` must already
    be sorted ascending by price_date. Returns one value per consecutive
    pair; empty if fewer than 2 bars are available - a series is its own
    insufficient-data signal, no extra flag needed.
    """
    if len(bars) < 2:
        return []
    return [bars[i].adjusted_close / bars[i - 1].adjusted_close - 1 for i in range(1, len(bars))]


def cumulative_return(bars: list[PriceBar]) -> MetricValue:
    """Total adjusted-close return from the first to the last bar given."""
    if len(bars) < 2:
        return MetricValue(value=None, insufficient_data=True, observations_used=len(bars))
    value = bars[-1].adjusted_close / bars[0].adjusted_close - 1
    return MetricValue(value=value, insufficient_data=False, observations_used=len(bars))
