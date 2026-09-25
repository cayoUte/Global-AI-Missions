from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import get_settings
from app.core.security import create_session_token
from tests.fakes import PASSWORD


def test_login_sets_an_httponly_lax_cookie_and_returns_the_user(client):
    r = client.post("/api/auth/login", json={"email": " New@GlobalAI.test ", "password": PASSWORD})
    assert r.status_code == 200
    assert r.json()["email"] == "new@globalai.test" and r.json()["role"] == "student"
    cookie = r.headers["set-cookie"]
    assert "gam_session=" in cookie and "HttpOnly" in cookie and "samesite=lax" in cookie.lower()
    assert "Max-Age=3600" in cookie and "token" not in r.json()
    assert client.get("/api/auth/me").json()["display_name"] == "Ana"


def test_unknown_email_and_wrong_password_get_the_same_response(client):
    wrong = client.post("/api/auth/login", json={"email": "new@globalai.test", "password": "x"})
    unknown = client.post("/api/auth/login", json={"email": "ghost@globalai.test", "password": "x"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    assert wrong.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_rejects_extra_fields_and_bad_shapes(client):
    extra = client.post(
        "/api/auth/login",
        json={"email": "new@globalai.test", "password": PASSWORD, "role": "admin"},
    )
    assert extra.status_code == 422 and extra.json()["error"]["code"] == "VALIDATION_ERROR"
    bad = client.post("/api/auth/login", json={"email": "nope", "password": "x"})
    assert bad.status_code == 422


def test_login_rate_limit_is_5_per_minute_per_ip_and_email(client):
    body = {"email": "new@globalai.test", "password": "wrong"}
    for _ in range(5):
        assert client.post("/api/auth/login", json=body).status_code == 401
    r = client.post("/api/auth/login", json=body)
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "RATE_LIMITED"
    assert int(r.headers["Retry-After"]) >= 1
    assert r.json()["error"]["details"]["retry_after_seconds"] >= 1
    # Even the right password is refused inside the window.
    assert client.post("/api/auth/login", json={**body, "password": PASSWORD}).status_code == 429
    other = client.post(
        "/api/auth/login", json={"email": "veteran@globalai.test", "password": PASSWORD}
    )
    assert other.status_code == 200  # another email is another bucket


def test_missing_tampered_forged_or_expired_cookie_is_401(client, store):
    assert client.get("/api/auth/me").json()["error"]["code"] == "UNAUTHENTICATED"
    client.cookies.set("gam_session", "not-a-jwt")
    assert client.get("/api/auth/me").status_code == 401
    past = datetime.now(UTC) - timedelta(hours=2)
    client.cookies.set("gam_session", create_session_token(str(store.ana.id), "student", past))
    r = client.get("/api/auth/me")
    assert r.status_code == 401 and r.json()["error"]["code"] == "UNAUTHENTICATED"
    forged = jwt.encode(
        {"sub": str(store.ana.id), "role": "admin", "iat": 1, "exp": 2**40},
        "another-secret-that-is-long-enough-0123456789",
        algorithm="HS256",
    )
    client.cookies.set("gam_session", forged)
    assert client.get("/api/auth/me").status_code == 401


def test_a_deleted_user_session_is_401(ana, store):
    del store.users[store.ana.id]
    assert ana.get("/api/auth/me").status_code == 401


def test_the_role_comes_from_the_database_not_the_token(ana, store):
    store.ana.role = "teacher"
    assert ana.get("/api/world").status_code == 403


def test_logout_is_204_and_clears_the_cookie(ana):
    r = ana.post("/api/auth/logout")
    assert r.status_code == 204
    assert "gam_session=" in r.headers["set-cookie"] and "Max-Age=0" in r.headers["set-cookie"]
    assert ana.get("/api/auth/me").status_code == 401


def test_config_lists_demo_accounts_only_in_demo_mode(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "demo_mode", True)
    on = client.get("/api/config").json()
    assert on["demo_mode"] is True and on["demo_password"] == "LastTrain2026!"
    assert [a["email"] for a in on["demo_accounts"]] == [
        "new@globalai.test",
        "veteran@globalai.test",
        "teacher@globalai.test",
    ]


def test_config_hides_demo_accounts_when_demo_mode_is_off(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "demo_mode", False)
    assert client.get("/api/config").json() == {
        "demo_mode": False,
        "demo_accounts": None,
        "demo_password": None,
    }


def test_request_id_is_echoed_and_api_responses_are_not_cached(client):
    r = client.get("/api/health", headers={"X-Request-ID": "abc-123"})
    assert r.headers["X-Request-ID"] == "abc-123" and r.headers["Cache-Control"] == "no-store"
    assert len(client.get("/api/health").headers["X-Request-ID"]) == 32
