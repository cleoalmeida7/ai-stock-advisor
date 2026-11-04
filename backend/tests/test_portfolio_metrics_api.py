from datetime import date

from fastapi.testclient import TestClient

from app.market_data.provider import PriceBar
from tests.conftest import auth_header
from tests.fakes import SEED_INSTRUMENTS, FakePriceRepository

RELIANCE_ID = SEED_INSTRUMENTS[0].id
TCS_ID = SEED_INSTRUMENTS[1].id


def price_bar(close: float) -> PriceBar:
    return PriceBar(price_date=date.today(), open=close, high=close, low=close, close=close, adjusted_close=close, volume=1000)


def test_metrics_requires_auth(client: TestClient) -> None:
    response = client.get("/api/portfolio/metrics")
    assert response.status_code == 401


def test_metrics_for_empty_portfolio(client: TestClient) -> None:
    response = client.get("/api/portfolio/metrics", headers=auth_header())
    assert response.status_code == 200

    body = response.json()
    assert body["total_value"] == 0
    assert body["valuation_complete"] is True
    assert body["holdings"] == []
    assert body["unpriced_holdings"] == []
    assert body["overall_return"] is None


def test_metrics_for_fully_priced_portfolio(client: TestClient, price_repo: FakePriceRepository) -> None:
    client.post(
        "/api/portfolio/holdings",
        json={"instrument_id": RELIANCE_ID, "quantity": "10", "average_buy_price": "2500"},
        headers=auth_header("user-a-token"),
    )
    price_repo.set_bars(RELIANCE_ID, [price_bar(2600)])

    response = client.get("/api/portfolio/metrics", headers=auth_header("user-a-token"))
    assert response.status_code == 200

    body = response.json()
    assert body["valuation_complete"] is True
    assert body["total_value"] == 26000
    assert body["total_cost_basis"] == 25000
    assert body["unrealized_pl"] == 1000
    assert len(body["holdings"]) == 1
    assert body["holdings"][0]["weight"] == 1.0


def test_metrics_flags_holding_with_no_price_data(client: TestClient, price_repo: FakePriceRepository) -> None:
    client.post(
        "/api/portfolio/holdings",
        json={"instrument_id": TCS_ID, "quantity": "5", "average_buy_price": "3000"},
        headers=auth_header("user-a-token"),
    )
    # deliberately no price_repo.set_bars for TCS_ID

    response = client.get("/api/portfolio/metrics", headers=auth_header("user-a-token"))
    assert response.status_code == 200

    body = response.json()
    assert body["valuation_complete"] is False
    assert len(body["unpriced_holdings"]) == 1
    assert body["unpriced_holdings"][0]["symbol"] == "TCS"
    assert body["unpriced_holdings"][0]["reason"] == "no_price_data"
    assert body["total_value"] == 0


def test_metrics_only_reflect_the_caller_own_holdings(client: TestClient, price_repo: FakePriceRepository) -> None:
    client.post(
        "/api/portfolio/holdings",
        json={"instrument_id": RELIANCE_ID, "quantity": "10", "average_buy_price": "2500"},
        headers=auth_header("user-a-token"),
    )
    price_repo.set_bars(RELIANCE_ID, [price_bar(2600)])

    response = client.get("/api/portfolio/metrics", headers=auth_header("user-b-token"))
    assert response.status_code == 200

    body = response.json()
    assert body["total_value"] == 0
    assert body["holdings"] == []
