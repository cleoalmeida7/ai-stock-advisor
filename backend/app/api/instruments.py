from fastapi import APIRouter, Depends, Query

from app.api.deps import get_instrument_repository
from app.core.auth import AuthContext, get_current_user
from app.repositories.instrument_repository import InstrumentRepository
from app.schemas.instrument import InstrumentRead

router = APIRouter(prefix="/api/instruments", tags=["instruments"])


@router.get("/search", response_model=list[InstrumentRead])
def search_instruments(
    q: str = Query(default="", max_length=50),
    # Declared directly (not just pulled in transitively via the repository
    # factory's own dependency) so auth is enforced on this route even if
    # the repository dependency is ever overridden or swapped - as the test
    # suite's DI overrides demonstrated it otherwise would not be.
    _auth: AuthContext = Depends(get_current_user),
    repo: InstrumentRepository = Depends(get_instrument_repository),
) -> list[InstrumentRead]:
    return repo.search(q)
