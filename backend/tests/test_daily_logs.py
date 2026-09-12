"""Daily check-in API tests."""

from __future__ import annotations


def test_create_daily_log(client, auth_headers):
    headers = auth_headers("checkin@example.com")
    payload = {
        "sleep_hours": 7.2,
        "sleep_quality": "good",
        "steps": 8412,
        "active_minutes": 35,
        "exercise_level": "moderate",
        "water_liters": 2.1,
        "meal_quality": "healthy",
        "mood": "good",
        "energy": 7,
        "stress": 2,
        "caffeine": "low",
    }
    resp = client.post("/api/v1/daily-logs", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["sleep_hours"] == 7.2
    assert body["steps"] == 8412
    assert body["source"] == "manual"


def test_duplicate_checkin_rejected(client, auth_headers):
    headers = auth_headers("dup-checkin@example.com")
    payload = {"sleep_hours": 6.5, "energy": 5, "stress": 3}
    r1 = client.post("/api/v1/daily-logs", json=payload, headers=headers)
    assert r1.status_code == 201
    r2 = client.post("/api/v1/daily-logs", json=payload, headers=headers)
    assert r2.status_code == 409
    assert r2.json()["error"]["code"] == "conflict"


def test_get_specific_daily_log(client, auth_headers):
    headers = auth_headers("get-log@example.com")
    client.post(
        "/api/v1/daily-logs",
        json={"date": "2025-09-11", "sleep_hours": 8, "energy": 9, "stress": 1},
        headers=headers,
    )
    resp = client.get("/api/v1/daily-logs/2025-09-11", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["sleep_hours"] == 8


def test_get_nonexistent_log(client, auth_headers):
    headers = auth_headers("missing-log@example.com")
    resp = client.get("/api/v1/daily-logs/2000-01-01", headers=headers)
    assert resp.status_code == 404


def test_update_daily_log(client, auth_headers):
    headers = auth_headers("update-log@example.com")
    client.post(
        "/api/v1/daily-logs",
        json={"date": "2025-09-11", "sleep_hours": 6, "energy": 4, "stress": 4},
        headers=headers,
    )
    resp = client.put(
        "/api/v1/daily-logs/2025-09-11",
        json={"sleep_hours": 7.5, "energy": 8},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["sleep_hours"] == 7.5
    assert resp.json()["energy"] == 8


def test_partial_fields_allow_nulls(client, auth_headers):
    """Phase 1 rule: unspecified fields are stored as NULL, never 0."""
    headers = auth_headers("partial@example.com")
    resp = client.post(
        "/api/v1/daily-logs",
        json={"energy": 6, "stress": 3},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["sleep_hours"] is None
    assert body["steps"] is None
    assert body["water_liters"] is None


def test_enum_validators_reject_invalid(client, auth_headers):
    headers = auth_headers("bad-enum@example.com")
    resp = client.post(
        "/api/v1/daily-logs",
        json={"mood": "ecstatic", "meal_quality": "gourmet"},
        headers=headers,
    )
    assert resp.status_code == 422


def test_list_daily_logs(client, auth_headers):
    headers = auth_headers("list-logs@example.com")
    for i in range(3):
        client.post("/api/v1/daily-logs", json={"energy": 5 + i, "stress": 3 - i}, headers=headers)
    resp = client.get("/api/v1/daily-logs", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)