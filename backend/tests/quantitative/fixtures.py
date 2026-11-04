from datetime import date, timedelta

from app.market_data.provider import PriceBar


def make_bar(day_offset: int, close: float, adjusted_close: float | None = None, volume: int = 1000) -> PriceBar:
    if adjusted_close is None:
        adjusted_close = close
    base = date(2024, 1, 1)
    return PriceBar(
        price_date=base + timedelta(days=day_offset),
        open=close,
        high=close,
        low=close,
        close=close,
        adjusted_close=adjusted_close,
        volume=volume,
    )


def make_series(closes: list[float], adjusted_closes: list[float] | None = None) -> list[PriceBar]:
    if adjusted_closes is None:
        adjusted_closes = closes
    assert len(closes) == len(adjusted_closes)
    return [make_bar(i, c, a) for i, (c, a) in enumerate(zip(closes, adjusted_closes))]


def flat_series(n: int, close: float = 100.0) -> list[PriceBar]:
    return make_series([close] * n)


def divergent_series() -> list[PriceBar]:
    """
    close is completely flat (no price movement at all); adjusted_close
    has a single -5% step on day 2 and is flat afterward. Any metric
    computed correctly from adjusted_close must come out non-zero /
    distinct from flat; a metric that was accidentally computed from
    `close` instead (the exact bug this guards against) would come out
    zero/flat instead. Shared across every quantitative module's
    adjusted-vs-unadjusted regression test (docs/metrics-and-scoring.md).
    """
    closes = [100.0, 100.0, 100.0, 100.0, 100.0]
    adjusted = [100.0, 95.0, 95.0, 95.0, 95.0]
    return make_series(closes, adjusted)
