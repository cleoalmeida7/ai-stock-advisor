from datetime import date

from pydantic import BaseModel


class MetricResponse(BaseModel):
    value: float | None
    insufficient_data: bool
    observations_used: int


class InstrumentAnalysis(BaseModel):
    instrument_id: str
    symbol: str
    as_of_date: date | None
    source: str | None
    metrics_version: str
    cumulative_return: MetricResponse
    sma_20: MetricResponse
    sma_50: MetricResponse
    sma_200: MetricResponse
    momentum: MetricResponse
    volatility: MetricResponse
    max_drawdown: MetricResponse


class UnpricedHoldingResponse(BaseModel):
    holding_id: str
    instrument_id: str
    symbol: str
    reason: str


class HoldingValuationResponse(BaseModel):
    holding_id: str
    instrument_id: str
    symbol: str
    sector: str | None
    quantity: float
    market_price: float
    market_value: float
    cost_basis: float
    unrealized_pl: float
    weight: float


class PortfolioMetricsResponse(BaseModel):
    total_value: float
    total_cost_basis: float
    unrealized_pl: float
    overall_return: float | None
    valuation_complete: bool
    unpriced_holdings: list[UnpricedHoldingResponse]
    holdings: list[HoldingValuationResponse]
    sector_concentration: dict[str, float]
