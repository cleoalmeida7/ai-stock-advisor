from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_instrument_repository, get_portfolio_repository
from app.core.auth import AuthContext, get_current_user
from app.repositories.exceptions import DuplicateHoldingError
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.portfolio_repository import PortfolioRepository
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
