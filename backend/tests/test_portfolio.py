from fastapi.testclient import TestClient

from tests.conftest import auth_header
from tests.fakes import SEED_INSTRUMENTS

RELIANCE_ID = SEED_INSTRUMENTS[0].id
TCS_ID = SEED_INSTRUMENTS[1].id


def test_create_holding_succeeds_and_total_cost_is_derived(client: TestClient) -> None:
    response = client.post(
        "/api/portfolio/holdings",
        json={"instrument_id": RELIANCE_ID, "quantity": "10", "average_buy_price": "2500.50"},
        headers=auth_header("user-a-token"),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["instrument"]["symbol"] == "RELIANCE"
    assert body["quantity"] == "10"
    assert body["average_buy_price"] == "2500.50"
    assert body["total_cost"] == "25005.00"


def test_create_holding_rejects_unknown_instrument(client: TestClient) -> None:
    response = client.post(
        "/api/portfolio/holdings",
        json={"instrument_id": "does-not-exist", "quantity": "1", "average_buy_price": "100"},
        headers=auth_header("user-a-token"),
    )
    assert response.status_code == 400


def test_create_holding_rejects_zero_quantity(client: TestClient) -> None:
    response = client.post(
        "/api/portfolio/holdings",
        json={"instrument_id": RELIANCE_ID, "quantity": "0", "average_buy_price": "100"},
        headers=auth_header("user-a-token"),
    )
    assert response.status_code == 422


def test_create_holding_rejects_negative_price(client: TestClient) -> None:
    response = client.post(
        "/api/portfolio/holdings",
        json={"instrument_id": RELIANCE_ID, "quantity": "1", "average_buy_price": "-5"},
        headers=auth_header("user-a-token"),
    )
    assert response.status_code == 422


def test_duplicate_holding_for_same_instrument_is_rejected(client: TestClient) -> None:
    payload = {"instrument_id": RELIANCE_ID, "quantity": "1", "average_buy_price": "100"}
    first = client.post("/api/portfolio/holdings", json=payload, headers=auth_header("user-a-token"))
    second = client.post("/api/portfolio/holdings", json=payload, headers=auth_header("user-a-token"))
    assert first.status_code == 201
    assert second.status_code == 409


def test_list_holdings_returns_created_holding(client: TestClient) -> None:
    client.post(
        "/api/portfolio/holdings",
        json={"instrument_id": TCS_ID, "quantity": "5", "average_buy_price": "3400"},
        headers=auth_header("user-a-token"),
    )
    response = client.get("/api/portfolio/holdings", headers=auth_header("user-a-token"))
    assert response.status_code == 200
    holdings = response.json()
    assert len(holdings) == 1
    assert holdings[0]["instrument"]["symbol"] == "TCS"


def test_delete_holding_removes_it(client: TestClient) -> None:
    create = client.post(
        "/api/portfolio/holdings",
        json={"instrument_id": TCS_ID, "quantity": "5", "average_buy_price": "3400"},
        headers=auth_header("user-a-token"),
    )
    holding_id = create.json()["id"]

    delete = client.delete(f"/api/portfolio/holdings/{holding_id}", headers=auth_header("user-a-token"))
    assert delete.status_code == 204

    listing = client.get("/api/portfolio/holdings", headers=auth_header("user-a-token"))
    assert listing.json() == []


def test_delete_nonexistent_holding_returns_404(client: TestClient) -> None:
    response = client.delete("/api/portfolio/holdings/does-not-exist", headers=auth_header("user-a-token"))
    assert response.status_code == 404


def test_cross_user_isolation_on_list(client: TestClient) -> None:
    client.post(
        "/api/portfolio/holdings",
        json={"instrument_id": RELIANCE_ID, "quantity": "1", "average_buy_price": "100"},
        headers=auth_header("user-a-token"),
    )

    user_b_listing = client.get("/api/portfolio/holdings", headers=auth_header("user-b-token"))
    assert user_b_listing.status_code == 200
    assert user_b_listing.json() == []

    user_a_listing = client.get("/api/portfolio/holdings", headers=auth_header("user-a-token"))
    assert len(user_a_listing.json()) == 1


def test_cross_user_isolation_on_delete(client: TestClient) -> None:
    create = client.post(
        "/api/portfolio/holdings",
        json={"instrument_id": RELIANCE_ID, "quantity": "1", "average_buy_price": "100"},
        headers=auth_header("user-a-token"),
    )
    holding_id = create.json()["id"]

    forbidden_delete = client.delete(f"/api/portfolio/holdings/{holding_id}", headers=auth_header("user-b-token"))
    assert forbidden_delete.status_code == 404

    still_there = client.get("/api/portfolio/holdings", headers=auth_header("user-a-token"))
    assert len(still_there.json()) == 1
