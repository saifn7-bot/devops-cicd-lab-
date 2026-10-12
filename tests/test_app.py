import pytest

from app.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_index_returns_message(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "message" in r.get_json()


def test_health_is_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_metrics_exposes_counter(client):
    client.get("/")
    r = client.get("/metrics")
    assert r.status_code == 200
    assert b"app_requests_total" in r.data
