from fastapi import Depends

from app.core.auth import AuthContext, get_current_user
from app.db.supabase_client import get_user_scoped_client
from app.repositories.instrument_repository import InstrumentRepository, SupabaseInstrumentRepository
from app.repositories.portfolio_repository import PortfolioRepository, SupabasePortfolioRepository
from app.repositories.price_repository import PriceRepository, SupabasePriceRepository


def get_portfolio_repository(auth: AuthContext = Depends(get_current_user)) -> PortfolioRepository:
    return SupabasePortfolioRepository(get_user_scoped_client(auth.access_token))


def get_instrument_repository(auth: AuthContext = Depends(get_current_user)) -> InstrumentRepository:
    return SupabaseInstrumentRepository(get_user_scoped_client(auth.access_token))


def get_price_repository(auth: AuthContext = Depends(get_current_user)) -> PriceRepository:
    return SupabasePriceRepository(get_user_scoped_client(auth.access_token))
