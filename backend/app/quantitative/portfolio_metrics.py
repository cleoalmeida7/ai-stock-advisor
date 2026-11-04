"""
Portfolio-level valuation and concentration. Pure function - takes
already-fetched holdings and latest prices, no I/O of its own (the API
layer is responsible for calling PortfolioRepository/PriceRepository and
assembling the inputs). See docs/metrics-and-scoring.md.

Uses UNADJUSTED close for valuation, deliberately the opposite of every
other module in this package - see the adjusted-vs-unadjusted usage rule
in docs/metrics-and-scoring.md. adjusted_close is a return-calculation
construct, not a real quoted price; using it here would misstate what a
position is actually worth today.
"""

from dataclasses import dataclass
from datetime import date

from app.market_data.provider import PriceBar
from app.schemas.holding import HoldingRead

STALENESS_THRESHOLD_DAYS = 5


@dataclass(frozen=True)
class UnpricedHolding:
    holding_id: str
    instrument_id: str
    symbol: str
    reason: str  # "no_price_data" | "stale_price"


@dataclass(frozen=True)
class HoldingValuation:
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


@dataclass(frozen=True)
class PortfolioMetrics:
    total_value: float
    total_cost_basis: float
    unrealized_pl: float
    overall_return: float | None
    valuation_complete: bool
    unpriced_holdings: list[UnpricedHolding]
    holdings: list[HoldingValuation]
    sector_concentration: dict[str, float]


def compute_portfolio_metrics(
    holdings: list[HoldingRead],
    latest_prices: dict[str, PriceBar | None],
    as_of: date | None = None,
) -> PortfolioMetrics:
    """
    `total_value`/`total_cost_basis`/`unrealized_pl`/`overall_return` are
    computed ONLY over holdings that actually have a current, non-stale
    price (the "priced" subset) - comparing a value against a cost basis
    that includes holdings excluded from that value would silently
    misstate P/L. Holdings missing a price, or whose latest price is
    older than STALENESS_THRESHOLD_DAYS, are never dropped silently: they
    are listed in `unpriced_holdings` and `valuation_complete` is set to
    False, so the caller always knows the numbers above are partial, not
    just that they're large or small.
    """
    as_of = as_of or date.today()

    priced: list[tuple[HoldingRead, PriceBar]] = []
    unpriced: list[UnpricedHolding] = []

    for holding in holdings:
        instrument = holding.instrument
        bar = latest_prices.get(instrument.id)

        if bar is None:
            unpriced.append(
                UnpricedHolding(
                    holding_id=holding.id,
                    instrument_id=instrument.id,
                    symbol=instrument.symbol,
                    reason="no_price_data",
                )
            )
            continue

        if (as_of - bar.price_date).days > STALENESS_THRESHOLD_DAYS:
            unpriced.append(
                UnpricedHolding(
                    holding_id=holding.id,
                    instrument_id=instrument.id,
                    symbol=instrument.symbol,
                    reason="stale_price",
                )
            )
            continue

        priced.append((holding, bar))

    total_value = sum(float(holding.quantity) * bar.close for holding, bar in priced)
    total_cost_basis = sum(float(holding.total_cost) for holding, _bar in priced)
    unrealized_pl = total_value - total_cost_basis
    overall_return = (unrealized_pl / total_cost_basis) if total_cost_basis > 0 else None

    holding_valuations: list[HoldingValuation] = []
    sector_totals: dict[str, float] = {}

    for holding, bar in priced:
        instrument = holding.instrument
        market_value = float(holding.quantity) * bar.close
        cost_basis = float(holding.total_cost)
        weight = (market_value / total_value) if total_value > 0 else 0.0
        sector_label = instrument.sector or "Unclassified"
        sector_totals[sector_label] = sector_totals.get(sector_label, 0.0) + market_value

        holding_valuations.append(
            HoldingValuation(
                holding_id=holding.id,
                instrument_id=instrument.id,
                symbol=instrument.symbol,
                sector=instrument.sector,
                quantity=float(holding.quantity),
                market_price=bar.close,
                market_value=market_value,
                cost_basis=cost_basis,
                unrealized_pl=market_value - cost_basis,
                weight=weight,
            )
        )

    sector_concentration = {
        sector: (value / total_value if total_value > 0 else 0.0) for sector, value in sector_totals.items()
    }

    return PortfolioMetrics(
        total_value=total_value,
        total_cost_basis=total_cost_basis,
        unrealized_pl=unrealized_pl,
        overall_return=overall_return,
        valuation_complete=len(unpriced) == 0,
        unpriced_holdings=unpriced,
        holdings=holding_valuations,
        sector_concentration=sector_concentration,
    )
