"""API tests run the real app (routers, services, engine) over the in-memory FakeStore, so the
whole HTTP flow is exercised without PostgreSQL. Only the repositories are replaced."""

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_session
from app.core.rate_limit import login_limiter
from app.main import create_app
from app.services import content
from tests.fakes import PASSWORD, FakeSession, FakeStore


@pytest.fixture
def store(monkeypatch):
    store = FakeStore()
    store.install(monkeypatch)
    content.clear_cache()
    login_limiter.reset()
    store.ana = store.add_user("new@globalai.test", "Ana")
    store.leo = store.add_user("veteran@globalai.test", "Leo")
    store.teacher = store.add_user("teacher@globalai.test", "Ms. Clarke", "teacher")
    store.other_teacher = store.add_user("other@globalai.test", "Mr. Other", "teacher")
    store.admin = store.add_user("admin@globalai.test", "Admin", "admin")
    store.klass = store.add_class("Evening B1", store.teacher, [store.ana, store.leo])
    store.other_class = store.add_class("Morning A2", store.other_teacher, [])
    yield store
    content.clear_cache()
    login_limiter.reset()


@pytest.fixture
def app(store):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: FakeSession()
    return app


def make_client(app, email=None) -> TestClient:
    client = TestClient(app)
    if email:
        response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
        assert response.status_code == 200, response.text
    return client


@pytest.fixture
def client(app):
    return make_client(app)


@pytest.fixture
def ana(app):
    return make_client(app, "new@globalai.test")


@pytest.fixture
def leo(app):
    return make_client(app, "veteran@globalai.test")


@pytest.fixture
def teacher(app):
    return make_client(app, "teacher@globalai.test")


@pytest.fixture
def admin(app):
    return make_client(app, "admin@globalai.test")
