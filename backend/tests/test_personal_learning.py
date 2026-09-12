"""Phase 5 - personal learning profile API tests.

The profile aggregates the user's own experiment observations. It never claims
causation, rejected observations never enter it, and everything is user-scoped.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.database.session import SessionLocal
from app.repositories.daily_log import DailyLogRepository

TODAY = date.today()

BANNED_CAUSAL_WORDS = ("causes", "caused", "diagnos", "treatment works", "cures", "risk of")


def _seed_baseline(db, user_id: int, sleep: float = 6.1, energy: int = 5):
    for d in range(1, 15):
        DailyLogRepository().create(
            db, user_id, date=TODAY - timedelta(days=d), sleep_hours=sleep, energy=energy, stress=3, mood="good"
        )


def _start(client, headers):
    return client.post("/api/v1/experiments", json={"experiment_type": "sleep_consistency"}, headers=headers).json()


def _log_day(client, headers, exp_id: int, offset: int):
    resp = client.post(
        f"/api/v1/experiments/{exp_id}/daily-log",
        json={
            "date": str(TODAY + timedelta(days=offset)),
            "target_met": True,
            "metrics": {"sleep_hours": 7.9, "energy": 8, "stress": 2, "mood": "good"},
        },
        headers=headers,
    )
    assert resp.status_code in (200, 201), resp.text


def _run_improving_experiment(client, headers):
    db = SessionLocal()
    user_id = 1
    _seed_baseline(db, user_id)
    db.close()
    exp = _start(client, headers)
    for offset in range(7):
        _log_day(client, headers, exp["id"], offset)
    client.post(f"/api/v1/experiments/{exp['id']}/complete", headers=headers)
    return exp


def _learning_list(client, headers):
    resp = client.get("/api/v1/learnings/personal", headers=headers)
    assert resp.status_code == 200
    return resp.json()["learnings"]


def test_completion_folds_one_observation_in(client, auth_headers):
    headers = auth_headers("pl-1@example.com")
    _run_improving_experiment(client, headers)

    learnings = _learning_list(client, headers)
    assert len(learnings) == 1
    row = learnings[0]
    assert row["pattern_type"] == "sleep_energy"
    assert row["evidence_level"] in {"EARLY_OBSERVATION", "PROMISING_OBSERVATION"}
    assert row["sample_size"] == 1
    assert row["causality_proven"] is False
    assert row["summary"]
    assert not any(w in row["summary"].lower() for w in BANNED_CAUSAL_WORDS)


def test_accept_marks_evidence_source(client, auth_headers):
    headers = auth_headers("pl-2@example.com")
    exp = _run_improving_experiment(client, headers)
    candidate = client.get(
        f"/api/v1/experiments/{exp['id']}/learning-candidate", headers=headers
    ).json()

    resp = client.post(f"/api/v1/learning-candidates/{candidate['id']}/accept", headers=headers)
    assert resp.status_code == 200

    learning = _learning_list(client, headers)[0]
    detail = client.get(f"/api/v1/learnings/personal/{learning['id']}", headers=headers).json()
    assert detail["evidence"], "accepted candidate must keep its evidence snapshot"
    assert detail["evidence"][0]["source"] == "accepted"
    assert detail["evidence"][0]["evidence_level"] == candidate["evidence_level"]


def test_rejected_candidate_downgrades_learning(client, auth_headers):
    headers = auth_headers("pl-3@example.com")
    exp = _run_improving_experiment(client, headers)
    candidate = client.get(
        f"/api/v1/experiments/{exp['id']}/learning-candidate", headers=headers
    ).json()
    client.post(f"/api/v1/learning-candidates/{candidate['id']}/reject", headers=headers)

    client.post("/api/v1/learnings/personal", headers=headers)
    rows = _learning_list(client, headers)
    assert all(r["evidence_level"] == "INSUFFICIENT" for r in rows), "a rejected observation cannot stay in the profile"


def test_two_experiments_merge_into_single_learning(client, auth_headers):
    headers = auth_headers("pl-4@example.com")
    _run_improving_experiment(client, headers)

    exp2 = _start(client, headers)
    for offset in range(7):
        _log_day(client, headers, exp2["id"], offset)
    client.post(f"/api/v1/experiments/{exp2['id']}/complete", headers=headers)

    client.post("/api/v1/learnings/personal", headers=headers)
    learnings = _learning_list(client, headers)
    assert len(learnings) == 1, "both experiments describe the same relationship"
    assert learnings[0]["sample_size"] == 2
    assert learnings[0]["evidence_state"] == "positive"
    assert learnings[0]["consistency_score"] is not None

    detail = client.get(f"/api/v1/learnings/personal/{learnings[0]['id']}", headers=headers).json()
    assert len(detail["evidence"]) == 2


def test_dismiss_and_reopen(client, auth_headers):
    headers = auth_headers("pl-5@example.com")
    _run_improving_experiment(client, headers)
    learning = _learning_list(client, headers)[0]

    resp = client.delete(f"/api/v1/learnings/personal/{learning['id']}", headers=headers)
    assert resp.status_code == 200
    assert _learning_list(client, headers) == []

    resp = client.patch(f"/api/v1/learnings/personal/{learning['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["state"] == "proposed"
    assert _learning_list(client, headers) != []


def test_recalculation_is_idempotent(client, auth_headers):
    headers = auth_headers("pl-6@example.com")
    _run_improving_experiment(client, headers)

    first = client.post("/api/v1/learnings/personal", headers=headers).json()
    second = client.post("/api/v1/learnings/personal", headers=headers).json()
    assert first["count"] == second["count"] == 1
    assert first["learnings"][0]["sample_size"] == second["learnings"][0]["sample_size"] == 1


def test_summary_endpoint_counts_states(client, auth_headers):
    headers = auth_headers("pl-7@example.com")
    _run_improving_experiment(client, headers)
    learning = _learning_list(client, headers)[0]

    summary = client.get("/api/v1/learnings/personal/summary", headers=headers).json()
    assert summary["total"] == 1
    assert summary["proposed"] == 1
    assert summary["dismissed"] == 0
    assert summary["top_learning"]["id"] == learning["id"]

    client.delete(f"/api/v1/learnings/personal/{learning['id']}", headers=headers)
    summary = client.get("/api/v1/learnings/personal/summary", headers=headers).json()
    assert summary["dismissed"] == 1
    assert summary["top_learning"] is None


def test_recommendation_carries_learning_context(client, auth_headers):
    headers = auth_headers("pl-8@example.com")
    _run_improving_experiment(client, headers)
    client.post("/api/v1/learnings/personal", headers=headers)

    from datetime import datetime, timezone

    from sqlalchemy import update

    from app.models.experiment import Experiment

    # Move completion outside the cooldown window so a new recommendation is allowed.
    db = SessionLocal()
    db.execute(
        update(Experiment)
        .where(Experiment.user_id == 1)
        .values(completed_at=datetime.now(timezone.utc) - timedelta(days=20))
    )
    db.commit()
    db.close()

    resp = client.get("/api/v1/experiments/recommended", headers=headers)
    assert resp.status_code == 200
    rec = resp.json()["recommendation"]
    assert rec is not None, "the pattern still exists and a new experiment can be recommended"
    assert rec["learning_context"]["has_learning"] is True
    assert rec["learning_context"]["evidence_level"] in {"EARLY_OBSERVATION", "PROMISING_OBSERVATION"}


def test_learnings_are_user_scoped(client, auth_headers):
    headers_a = auth_headers("pl-9a@example.com")
    headers_b = auth_headers("pl-9b@example.com")
    _run_improving_experiment(client, headers_a)
    learning = _learning_list(client, headers_a)[0]

    assert client.get("/api/v1/learnings/personal", headers=headers_b).json()["learnings"] == []
    assert client.delete(f"/api/v1/learnings/personal/{learning['id']}", headers=headers_b).status_code == 404