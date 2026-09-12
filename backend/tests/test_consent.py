"""Consent API tests."""

from __future__ import annotations


def test_initial_consent_all_false(client, auth_headers):
    headers = auth_headers("consent-empty@example.com")
    resp = client.get("/api/v1/consent", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["steps"] is False
    assert body["sleep"] is False
    assert body["activity"] is False
    assert body["screen_time"] is False
    assert body["demographic_optional"] is False


def test_record_consent(client, auth_headers):
    headers = auth_headers("consent-grant@example.com")
    resp = client.post(
        "/api/v1/consent",
        json={"data_type": "steps", "consent_given": True},
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["data_type"] == "steps"
    assert body["consent_given"] is True
    assert body["revoked"] is False

    status = client.get("/api/v1/consent", headers=headers)
    assert status.json()["steps"] is True


def test_revoke_consent(client, auth_headers):
    headers = auth_headers("consent-revoke@example.com")
    client.post("/api/v1/consent", json={"data_type": "steps", "consent_given": True}, headers=headers)
    client.post("/api/v1/consent", json={"data_type": "steps", "consent_given": False}, headers=headers)

    status = client.get("/api/v1/consent", headers=headers)
    assert status.json()["steps"] is False


def test_multiple_data_types(client, auth_headers):
    headers = auth_headers("consent-multi@example.com")
    for dt in ("steps", "sleep", "activity"):
        client.post("/api/v1/consent", json={"data_type": dt, "consent_given": True}, headers=headers)
    status = client.get("/api/v1/consent", headers=headers)
    assert status.json()["steps"] is True
    assert status.json()["sleep"] is True
    assert status.json()["activity"] is True