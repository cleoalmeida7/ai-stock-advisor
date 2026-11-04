"""
Simplified price momentum over adjusted_close: the cumulative return
across the trailing `window` trading-day bars (default 90). This is NOT
the academic 12-1 momentum factor used in quant research - it's a
simpler, explicitly documented definition appropriate for an educational
tool, not a trading signal. See docs/metrics-and-scoring.md.
"""

from app.market_data.provider import PriceBar
from app.quantitative.types import MetricValue

DEFAULT_MOMENTUM_WINDOW_DAYS = 90


def momentum(bars: list[PriceBar], window: int = DEFAULT_MOMENTUM_WINDOW_DAYS) -> MetricValue:
    if len(bars) < window:
        return MetricValue(value=None, insufficient_data=True, observations_used=len(bars))
    recent = bars[-window:]
    value = recent[-1].adjusted_close / recent[0].adjusted_close - 1
    return MetricValue(value=value, insufficient_data=False, observations_used=window)
