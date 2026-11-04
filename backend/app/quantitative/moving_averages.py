"""
Simple moving averages over adjusted_close. See
docs/metrics-and-scoring.md for the adjusted-vs-unadjusted usage rule.
"""

from app.market_data.provider import PriceBar
from app.quantitative.types import MetricValue


def simple_moving_average(bars: list[PriceBar], window: int) -> MetricValue:
    """
    The most recent `window`-bar average of adjusted_close. Returns
    insufficient_data (never a partial average over fewer rows) when
    fewer than `window` bars are available. `bars` must be sorted
    ascending by price_date.
    """
    if len(bars) < window:
        return MetricValue(value=None, insufficient_data=True, observations_used=len(bars))
    recent = bars[-window:]
    value = sum(bar.adjusted_close for bar in recent) / window
    return MetricValue(value=value, insufficient_data=False, observations_used=window)
