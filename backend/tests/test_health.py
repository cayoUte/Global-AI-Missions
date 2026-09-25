from fastapi.testclient import TestClient

from app.main import create_app


def test_health_is_public_and_ok():
    client = TestClient(create_app())
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_route_uses_the_error_envelope():
    client = TestClient(create_app())
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert set(response.json()["error"]) == {"code", "message", "details"}
