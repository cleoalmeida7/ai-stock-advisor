from fastapi.testclient import TestClient

from tests.conftest import auth_header


def test_search_matches_symbol(client: TestClient) -> None:
    response = client.get("/api/instruments/search", params={"q": "TCS"}, headers=auth_header())
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["symbol"] == "TCS"


def test_search_matches_company_name_case_insensitive(client: TestClient) -> None:
    response = client.get("/api/instruments/search", params={"q": "infosys"}, headers=auth_header())
    assert response.status_code == 200
    results = response.json()
    assert any(r["symbol"] == "INFY" for r in results)


def test_search_requires_auth(client: TestClient) -> None:
    response = client.get("/api/instruments/search", params={"q": "TCS"})
    assert response.status_code == 401
