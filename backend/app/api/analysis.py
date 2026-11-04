from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_instrument_repository, get_price_repository
from app.core.auth import AuthContext, get_current_user
from app.quantitative import METRICS_VERSION
from app.quantitative.drawdown import max_drawdown
from app.quantitative.momentum import DEFAULT_MOMENTUM_WINDOW_DAYS, momentum
from app.quantitative.moving_averages import simple_moving_average
from app.quantitative.returns import cumulative_return
from app.quantitative.types import MetricValue
from app.quantitative.volatility import annualized_volatility
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.price_repository import PriceRepository
from app.schemas.analysis import InstrumentAnalysis, MetricResponse
from app.schemas.price import PricePoint

router = APIRouter(tags=["analysis"])

# Calendar days of history fetched for analysis - generous enough margin
# over 200 trading days (the largest SMA window) to comfortably cover
# weekends/holidays. If it's still not enough, the affected metric
# correctly reports insufficient_data rather than silently using less.
ANALYSIS_LOOKBACK_DAYS = 400
SMA_WINDOWS = (20, 50, 200)
VOLATILITY_WINDOW_DAYS = 30


def _to_metric_response(metric: MetricValue) -> MetricResponse:
    return MetricResponse(
        value=metric.value,
        insufficient_data=metric.insufficient_data,
        observations_used=metric.observations_used,
    )


@router.get("/api/analysis/{instrument_id}", response_model=InstrumentAnalysis)
def get_instrument_analysis(
    instrument_id: str,
    _auth: AuthContext = Depends(get_current_user),
    instruments: InstrumentRepository = Depends(get_instrument_repository),
    prices: PriceRepository = Depends(get_price_repository),
) -> InstrumentAnalysis:
    instrument = instruments.get(instrument_id)
    if instrument is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown instrument_id")

    bars = prices.history(instrument_id, days=ANALYSIS_LOOKBACK_DAYS)
    latest = bars[-1] if bars else None
    sma_20, sma_50, sma_200 = (simple_moving_average(bars, window) for window in SMA_WINDOWS)

    return InstrumentAnalysis(
        instrument_id=instrument.id,
        symbol=instrument.symbol,
        as_of_date=latest.price_date if latest else None,
        source="yfinance" if bars else None,
        metrics_version=METRICS_VERSION,
        cumulative_return=_to_metric_response(cumulative_return(bars)),
        sma_20=_to_metric_response(sma_20),
        sma_50=_to_metric_response(sma_50),
        sma_200=_to_metric_response(sma_200),
        momentum=_to_metric_response(momentum(bars, DEFAULT_MOMENTUM_WINDOW_DAYS)),
        volatility=_to_metric_response(annualized_volatility(bars, VOLATILITY_WINDOW_DAYS)),
        max_drawdown=_to_metric_response(max_drawdown(bars)),
    )


@router.get("/api/market/{instrument_id}/history", response_model=list[PricePoint])
def get_price_history(
    instrument_id: str,
    days: int = Query(default=90, ge=1, le=ANALYSIS_LOOKBACK_DAYS),
    _auth: AuthContext = Depends(get_current_user),
    instruments: InstrumentRepository = Depends(get_instrument_repository),
    prices: PriceRepository = Depends(get_price_repository),
) -> list[PricePoint]:
    instrument = instruments.get(instrument_id)
    if instrument is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown instrument_id")

    bars = prices.history(instrument_id, days=days)
    return [
        PricePoint(
            price_date=bar.price_date,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            adjusted_close=bar.adjusted_close,
            volume=bar.volume,
        )
        for bar in bars
    ]
