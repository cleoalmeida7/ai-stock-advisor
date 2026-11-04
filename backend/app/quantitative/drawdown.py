"""
Maximum drawdown over adjusted_close: the largest peak-to-trough decline
within the given window. See docs/metrics-and-scoring.md for the
adjusted-vs-unadjusted usage rule.
"""

from app.market_data.provider import PriceBar
from app.quantitative.types import MetricValue


def max_drawdown(bars: list[PriceBar]) -> MetricValue:
    if len(bars) < 2:
        return MetricValue(value=None, insufficient_data=True, observations_used=len(bars))

    peak = bars[0].adjusted_close
    worst = 0.0
    for bar in bars:
        peak = max(peak, bar.adjusted_close)
        drawdown = bar.adjusted_close / peak - 1
        worst = min(worst, drawdown)

    return MetricValue(value=worst, insufficient_data=False, observations_used=len(bars))
