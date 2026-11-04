from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_instrument_repository, get_portfolio_repository, get_price_repository
from app.core.auth import AuthContext, get_current_user
from app.quantitative.portfolio_metrics import compute_portfolio_metrics
from app.repositories.exceptions import DuplicateHoldingError
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.repositories.price_repository import PriceRepository
from app.schemas.analysis import HoldingValuationResponse, PortfolioMetricsResponse, UnpricedHoldingResponse
from app.schemas.holding import HoldingCreate, HoldingRead

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("/holdings", response_model=list[HoldingRead])
def list_holdings(
    auth: AuthContext = Depends(get_current_user),
    repo: PortfolioRepository = Depends(get_portfolio_repository),
) -> list[HoldingRead]:
    return repo.list_holdings(auth.user_id)


@router.post("/holdings", response_model=HoldingRead, status_code=status.HTTP_201_CREATED)
def create_holding(
    data: HoldingCreate,
    auth: AuthContext = Depends(get_current_user),
    repo: PortfolioRepository = Depends(get_portfolio_repository),
    instruments: InstrumentRepository = Depends(get_instrument_repository),
) -> HoldingRead:
    instrument = instruments.get(data.instrument_id)
    if instrument is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown instrument_id")

    try:
        return repo.create_holding(auth.user_id, data, instrument)
    except DuplicateHoldingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holding(
    holding_id: str,
    auth: AuthContext = Depends(get_current_user),
    repo: PortfolioRepository = Depends(get_portfolio_repository),
) -> None:
    deleted = repo.delete_holding(auth.user_id, holding_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")


@router.get("/metrics", response_model=PortfolioMetricsResponse)
def get_portfolio_metrics(
    auth: AuthContext = Depends(get_current_user),
    repo: PortfolioRepository = Depends(get_portfolio_repository),
    prices: PriceRepository = Depends(get_price_repository),
) -> PortfolioMetricsResponse:
    holdings = repo.list_holdings(auth.user_id)
    latest_prices = {holding.instrument.id: prices.latest(holding.instrument.id) for holding in holdings}

    metrics = compute_portfolio_metrics(holdings, latest_prices)

    return PortfolioMetricsResponse(
        total_value=metrics.total_value,
        total_cost_basis=metrics.total_cost_basis,
        unrealized_pl=metrics.unrealized_pl,
        overall_return=metrics.overall_return,
        valuation_complete=metrics.valuation_complete,
        unpriced_holdings=[
            UnpricedHoldingResponse(
                holding_id=u.holding_id, instrument_id=u.instrument_id, symbol=u.symbol, reason=u.reason
            )
            for u in metrics.unpriced_holdings
        ],
        holdings=[
            HoldingValuationResponse(
                holding_id=h.holding_id,
                instrument_id=h.instrument_id,
                symbol=h.symbol,
                sector=h.sector,
                quantity=h.quantity,
                market_price=h.market_price,
                market_value=h.market_value,
                cost_basis=h.cost_basis,
                unrealized_pl=h.unrealized_pl,
                weight=h.weight,
            )
            for h in metrics.holdings
        ],
        sector_concentration=metrics.sector_concentration,
    )
