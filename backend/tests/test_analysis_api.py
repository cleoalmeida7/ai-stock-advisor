from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.market_data.provider import PriceBar
from tests.conftest import auth_header
from tests.fakes import SEED_INSTRUMENTS, FakePriceRepository

TCS_ID = SEED_INSTRUMENTS[1].id


def make_bars(n: int, start_close: float = 100.0, step: float = 1.0) -> list[PriceBar]:
    today = date.today()
    bars = []
    for i in range(n):
        day = today - timedelta(days=(n - 1 - i))
        close = start_close + step * i
        bars.append(
            PriceBar(price_date=day, open=close, high=close, low=close, close=close, adjusted_close=close, volume=1000)
        )
    return bars


def test_get_analysis_requires_auth(client: TestClient) -> None:
    response = client.get(f"/api/analysis/{TCS_ID}")
    assert response.status_code == 401


def test_get_analysis_unknown_instrument_returns_404(client: TestClient) -> None:
    response = client.get("/api/analysis/does-not-exist", headers=auth_header())
    assert response.status_code == 404


def test_get_analysis_reports_insufficient_data_with_too_little_history(
    client: TestClient, price_repo: FakePriceRepository
) -> None:
    price_repo.set_bars(TCS_ID, make_bars(3))

    response = client.get(f"/api/analysis/{TCS_ID}", headers=auth_header())
    assert response.status_code == 200

    body = response.json()
    assert body["symbol"] == "TCS"
    assert body["sma_20"]["insufficient_data"] is True
    assert body["sma_50"]["insufficient_data"] is True
    assert body["sma_200"]["insufficient_data"] is True
    # cumulative_return and max_drawdown only need 2 bars, so these ARE computable
    assert body["cumulative_return"]["insufficient_data"] is False


def test_get_analysis_computes_full_metrics_with_enough_history(
    client: TestClient, price_repo: FakePriceRepository
) -> None:
    price_repo.set_bars(TCS_ID, make_bars(250))

    response = client.get(f"/api/analysis/{TCS_ID}", headers=auth_header())
    assert response.status_code == 200

    body = response.json()
    assert body["metrics_version"] == "1.0"
    assert body["source"] == "yfinance"
    assert body["sma_20"]["insufficient_data"] is False
    assert body["sma_50"]["insufficient_data"] is False
    assert body["sma_200"]["insufficient_data"] is False
    assert body["momentum"]["insufficient_data"] is False
    assert body["volatility"]["insufficient_data"] is False
    assert body["max_drawdown"]["insufficient_data"] is False


def test_get_analysis_with_no_price_data_returns_all_insufficient(client: TestClient) -> None:
    response = client.get(f"/api/analysis/{TCS_ID}", headers=auth_header())
    assert response.status_code == 200

    body = response.json()
    assert body["as_of_date"] is None
    assert body["source"] is None
    assert body["cumulative_return"]["insufficient_data"] is True
    assert body["sma_20"]["insufficient_data"] is True


def test_get_price_history_requires_auth(client: TestClient) -> None:
    response = client.get(f"/api/market/{TCS_ID}/history")
    assert response.status_code == 401


def test_get_price_history_unknown_instrument_returns_404(client: TestClient) -> None:
    response = client.get("/api/market/does-not-exist/history", headers=auth_header())
    assert response.status_code == 404


def test_get_price_history_returns_points(client: TestClient, price_repo: FakePriceRepository) -> None:
    price_repo.set_bars(TCS_ID, make_bars(10))

    response = client.get(f"/api/market/{TCS_ID}/history", headers=auth_header(), params={"days": 30})
    assert response.status_code == 200

    points = response.json()
    assert len(points) == 10
    assert points[-1]["close"] == 109.0
