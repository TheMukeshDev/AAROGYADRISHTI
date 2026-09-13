"""Health connection and sync API tests."""

from __future__ import annotations


def test_liveness_healthcheck(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_liveness_healthcheck_api_alias(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_db_healthcheck(client):
    resp = client.get("/health/db")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_db_healthcheck_api_alias(client):
    resp = client.get("/api/v1/health/db")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_db_healthcheck_database_down(client, monkeypatch):
    import app.main as main_module

    monkeypatch.setattr(main_module, "db_is_reachable", lambda db: False)
    resp = client.get("/health/db")
    assert resp.status_code == 503
    body = resp.json()
    assert body["error"]["code"] == "service_unavailable"
    assert "detail" not in body  # no driver/connection internals leak


def test_health_initially_unconnected(client, auth_headers):
    headers = auth_headers("hc-empty@example.com")
    resp = client.get("/api/v1/health/status", headers=headers)
    assert resp.status_code == 200
    # No connection yet - body is either empty/None or connection object.


def test_connect_health(client, auth_headers):
    headers = auth_headers("hc-connect@example.com")
    resp = client.post(
        "/api/v1/health/connect",
        json={"provider": "health_connect", "steps_enabled": True, "sleep_enabled": True, "activity_enabled": True},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["steps_enabled"] is True
    assert body["provider"] == "health_connect"


def test_sync_health_steps(client, auth_headers):
    headers = auth_headers("hc-steps@example.com")
    client.post("/api/v1/health/connect", json={"provider": "health_connect"}, headers=headers)
    resp = client.post(
        "/api/v1/health/sync",
        json={"steps": 7421, "active_minutes": 28, "sleep_minutes": 420},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["synced"] is True
    assert body["steps"] == 7421
    assert body["sleep_minutes"] == 420


def test_sync_health_partial(client, auth_headers):
    headers = auth_headers("hc-partial@example.com")
    resp = client.post(
        "/api/v1/health/sync",
        json={"steps": 5210},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["steps"] == 5210
    assert body["sleep_minutes"] is None
    assert body["active_minutes"] is None


def test_sync_empty_rejected(client, auth_headers):
    headers = auth_headers("hc-empty-sync@example.com")
    resp = client.post(
        "/api/v1/health/sync",
        json={},
        headers=headers,
    )
    assert resp.status_code == 400


def test_health_upsert_replaces(client, auth_headers):
    headers = auth_headers("hc-upsert@example.com")
    client.post("/api/v1/health/sync", json={"steps": 100}, headers=headers)
    client.post("/api/v1/health/sync", json={"steps": 200}, headers=headers)
    # DailyHealthData: same (user_id, date, source) => upsert
    # The last sync wins; source is always "health_connect"


def test_health_status_after_connect(client, auth_headers):
    headers = auth_headers("hc-status@example.com")
    client.post(
        "/api/v1/health/connect",
        json={"provider": "health_connect", "steps_enabled": True},
        headers=headers,
    )
    resp = client.get("/api/v1/health/status", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["steps_enabled"] is True