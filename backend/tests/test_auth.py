from fastapi.testclient import TestClient

from tests.conftest import auth_header


def test_missing_authorization_header_is_rejected(client: TestClient) -> None:
    response = client.get("/api/portfolio/holdings")
    assert response.status_code == 401


def test_unknown_token_is_rejected(client: TestClient) -> None:
    response = client.get("/api/portfolio/holdings", headers=auth_header("not-a-real-token"))
    assert response.status_code == 401


def test_malformed_header_is_rejected(client: TestClient) -> None:
    response = client.get("/api/portfolio/holdings", headers={"Authorization": "user-a-token"})
    assert response.status_code == 401


def test_valid_token_is_accepted(client: TestClient) -> None:
    response = client.get("/api/portfolio/holdings", headers=auth_header("user-a-token"))
    assert response.status_code == 200
