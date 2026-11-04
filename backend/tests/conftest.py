"""
Fakes out auth and the two repositories so the suite needs neither network
access nor a live Supabase project. The fake auth dependency still enforces
the same contract as the real one (missing/unknown token -> 401) so the
401 and cross-user-isolation tests exercise real request-handling logic,
not just the fakes. See docs/architecture-decisions.md ADR-007.
"""

import pytest
from fastapi import Header, HTTPException, status
from fastapi.testclient import TestClient

from app.api.deps import get_instrument_repository, get_portfolio_repository, get_price_repository
from app.core.auth import AuthContext, get_current_user
from app.main import app
from tests.fakes import FakeInstrumentRepository, FakePortfolioRepository, FakePriceRepository

FAKE_TOKENS = {
    "user-a-token": "user-a",
    "user-b-token": "user-b",
}


def fake_get_current_user(authorization: str | None = Header(default=None)) -> AuthContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    user_id = FAKE_TOKENS.get(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    return AuthContext(user_id=user_id, access_token=token)


@pytest.fixture
def portfolio_repo() -> FakePortfolioRepository:
    return FakePortfolioRepository()


@pytest.fixture
def instrument_repo() -> FakeInstrumentRepository:
    return FakeInstrumentRepository()


@pytest.fixture
def price_repo() -> FakePriceRepository:
    return FakePriceRepository()


@pytest.fixture
def client(
    portfolio_repo: FakePortfolioRepository,
    instrument_repo: FakeInstrumentRepository,
    price_repo: FakePriceRepository,
) -> TestClient:
    app.dependency_overrides[get_current_user] = fake_get_current_user
    app.dependency_overrides[get_portfolio_repository] = lambda: portfolio_repo
    app.dependency_overrides[get_instrument_repository] = lambda: instrument_repo
    app.dependency_overrides[get_price_repository] = lambda: price_repo
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def auth_header(token: str = "user-a-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
