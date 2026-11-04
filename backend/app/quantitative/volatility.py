"""
Annualized volatility: standard deviation of daily adjusted_close returns
over a trailing window, scaled by sqrt(252) trading days/year and
labeled as such - a raw daily figure is never presented unannotated. See
docs/metrics-and-scoring.md for the adjusted-vs-unadjusted usage rule.
"""

import statistics

from app.market_data.provider import PriceBar
from app.quantitative.returns import daily_returns
from app.quantitative.types import MetricValue

TRADING_DAYS_PER_YEAR = 252


def annualized_volatility(bars: list[PriceBar], window: int) -> MetricValue:
    if len(bars) < window + 1:
        return MetricValue(value=None, insufficient_data=True, observations_used=len(bars))

    recent_returns = daily_returns(bars[-(window + 1) :])
    if len(recent_returns) < 2:
        return MetricValue(value=None, insufficient_data=True, observations_used=len(bars))

    value = statistics.stdev(recent_returns) * (TRADING_DAYS_PER_YEAR**0.5)
    return MetricValue(value=value, insufficient_data=False, observations_used=len(recent_returns))
