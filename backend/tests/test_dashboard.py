"""Dashboard API tests (today + baseline tracking)."""

from __future__ import annotations


def test_dashboard_empty(client, auth_headers):
    headers = auth_headers("dash-empty@example.com")
    resp = client.get("/api/v1/dashboard/today", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["has_data"] is False
    assert body["baseline"]["status"] == "getting_started"
    assert body["baseline"]["days_recorded"] == 0


def test_baseline_getting_started(client, auth_headers):
    headers = auth_headers("bl-gs@example.com")
    client.post("/api/v1/daily-logs", json={"energy": 6, "stress": 3}, headers=headers)
    resp = client.get("/api/v1/dashboard/baseline", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "getting_started"
    assert resp.json()["days_recorded"] == 1
    assert "Keep checking in" in resp.json()["message"]


def test_baseline_building(client, auth_headers):
    headers = auth_headers("bl-build@example.com")
    from datetime import date, timedelta

    today = date.today()
    for i in range(4):
        d = (today - timedelta(days=3 - i)).isoformat()
        client.post(
            "/api/v1/daily-logs",
            json={"energy": 5, "stress": 3, "date": d},
            headers=headers,
        )
    resp = client.get("/api/v1/dashboard/baseline", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "building"
    assert resp.json()["days_recorded"] == 4


def test_baseline_ready(client, auth_headers):
    headers = auth_headers("bl-ready@example.com")
    from datetime import date, timedelta

    today = date.today()
    for i in range(7):
        d = (today - timedelta(days=6 - i)).isoformat()
        client.post(
            "/api/v1/daily-logs",
            json={"energy": 6, "stress": 2, "date": d},
            headers=headers,
        )
    resp = client.get("/api/v1/dashboard/baseline", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"
    assert resp.json()["days_recorded"] == 7
    assert "baseline is ready" in resp.json()["message"]


def test_today_has_data(client, auth_headers):
    headers = auth_headers("today-data@example.com")
    client.post("/api/v1/daily-logs", json={"sleep_hours": 7, "energy": 8, "stress": 2}, headers=headers)
    resp = client.get("/api/v1/dashboard/today", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["has_data"] is True
    assert body["summary"]["sleep_hours"] == 7


def test_today_other_date(client, auth_headers):
    """Dashboard /today shows today's data only - past dates appear in history."""
    headers = auth_headers("today-past@example.com")
    from datetime import date, timedelta

    d = (date.today() - timedelta(days=5)).isoformat()
    client.post("/api/v1/daily-logs", json={"energy": 4, "stress": 4, "date": d}, headers=headers)
    resp = client.get("/api/v1/dashboard/today", headers=headers)
    assert resp.json()["has_data"] is False