"""Phase 3 (experiment engine) + Phase 4 (evaluation/evidence) API tests.

Covered scenarios
-----------------
- predefined templates are seeded
- recommendation is computed from real phase-2 patterns (or is None)
- experiment lifecycle: start, daily logs, cancel, complete, history
- actionable restrictions: one active experiment, log window, ownership
- evaluation pipeline: metrics, evidence, learning candidates
- the non-medical/non-causal invariant everywhere (causality_proven=False)
"""

from __future__ import annotations

import random
from datetime import date, timedelta

from app.database.session import SessionLocal
from app.repositories.daily_log import DailyLogRepository

TODAY = date.today()

BANNED_CAUSAL_WORDS = ("causes", "caused", "crime", "diagnos", "treatment works", "cures", "risk of")


def _days_ago(n: int) -> date:
    return TODAY - timedelta(days=n)


def _seed_log(db, user_id: int, *dates, **fields):
    for d in dates:
        DailyLogRepository().create(db, user_id, date=d, **fields)


def _seed_baseline(db, user_id: int, window_days: int = 14, sleep: float = 6.1, energy: int = 5):
    dates = [_days_ago(d) for d in range(1, window_days + 1)]
    _seed_log(db, user_id, *dates, sleep_hours=sleep, energy=energy, stress=3, mood="good", steps=6000)
    return dates


def _log_experiment_day(client, headers, exp_id: int, offset: int, sleep: float, energy: int, met: bool):
    resp = client.post(
        f"/api/v1/experiments/{exp_id}/daily-log",
        json={
            "date": str(TODAY + timedelta(days=offset)),
            "day_number": offset + 1,
            "target_met": met,
            "notes": "kept to routine",
            "metrics": {"sleep_hours": sleep, "energy": energy, "stress": 2, "mood": "good"},
        },
        headers=headers,
    )
    assert resp.status_code in (200, 201), resp.text
    return resp


def _start_experiment(client, headers, experiment_type: str = "sleep_consistency"):
    return client.post("/api/v1/experiments", json={"experiment_type": experiment_type}, headers=headers)


# --- Phase 3: templates & recommendation ------------------------------------


def test_templates_are_seeded(client, auth_headers):
    headers = auth_headers("t-str-1@example.com")
    resp = client.get("/api/v1/experiment-templates", headers=headers)
    assert resp.status_code == 200
    types = {t["experiment_type"] for t in resp.json()}
    assert types == {"sleep_consistency", "night_screen_reduction", "daily_activity"}


def test_recommendation_is_none_for_new_user(client, auth_headers):
    headers = auth_headers("t-rec-none@example.com")
    resp = client.get("/api/v1/experiments/recommended", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["recommendation"] is None
    assert body["has_active_experiment"] is False


def test_recommendation_from_real_pattern(client, auth_headers):
    headers = auth_headers("t-rec-pattern@example.com")
    db = SessionLocal()
    user_id = 1
    rng = random.Random(42)
    prev_sleep = rng.uniform(4.5, 8.5)
    for i in range(34):
        d = _days_ago(34 - i)
        sleep = round(min(8.5, max(4.5, rng.uniform(4.5, 8.5))), 1)
        energy = int(round(max(1, min(10, 4.5 + (prev_sleep - 6.0) * 2.0 + rng.gauss(0, 0.5)))))
        _seed_log(db, user_id, d, sleep_hours=sleep, energy=energy, stress=3, mood="good", steps=6000)
        prev_sleep = sleep
    db.close()

    resp = client.get("/api/v1/experiments/recommended", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    rec = body["recommendation"]
    assert rec is not None, "strong sleep->energy pattern should yield a recommendation"
    assert rec["experiment_type"] == "sleep_consistency"
    assert rec["pattern"] is not None
    assert rec["pattern"]["pattern_id"] == "sleep_energy"
    assert rec["why"]


# --- Phase 3: lifecycle ------------------------------------------------------


def test_unknown_experiment_type_rejected(client, auth_headers):
    headers = auth_headers("t-unknown@example.com")
    resp = _start_experiment(client, headers, "definitely_not_a_template")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_start_and_single_active_experiment(client, auth_headers):
    headers = auth_headers("t-active@example.com")
    r1 = _start_experiment(client, headers)
    assert r1.status_code == 201, r1.text
    body = r1.json()
    assert body["status"] == "active"
    assert body["start_date"] == str(TODAY)
    assert body["end_date"] == str(TODAY + timedelta(days=6))
    assert body["duration_days"] == 7

    r2 = _start_experiment(client, headers, "daily_activity")
    assert r2.status_code == 409
    assert r2.json()["error"]["code"] == "conflict"

    active = client.get("/api/v1/experiments/active", headers=headers).json()
    assert active["experiment"]["experiment_type"] == "sleep_consistency"


def test_daily_log_must_be_within_experiment_window(client, auth_headers):
    headers = auth_headers("t-window@example.com")
    exp = _start_experiment(client, headers).json()
    resp = client.post(
        f"/api/v1/experiments/{exp['id']}/daily-log",
        json={
            "date": str(TODAY + timedelta(days=20)),
            "day_number": 1,
            "target_met": True,
            "metrics": {"sleep_hours": 7.5, "energy": 7},
        },
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "bad_request"


def test_daily_log_writes_metrics_into_user_daily_log(client, auth_headers):
    headers = auth_headers("t-writes@example.com")
    exp = _start_experiment(client, headers).json()
    resp = _log_experiment_day(client, headers, exp["id"], 0, 7.6, 8, True)
    body = resp.json()
    assert body["day_number"] == 1
    assert body["target_met"] is True

    log = client.get(f"/api/v1/daily-logs/{TODAY}", headers=headers)
    assert log.status_code == 200
    assert log.json()["sleep_hours"] == 7.6
    assert log.json()["energy"] == 8


def test_experiment_is_owned_by_user(client, auth_headers):
    headers_a = auth_headers("t-owner-a@example.com")
    headers_b = auth_headers("t-owner-b@example.com")
    exp = _start_experiment(client, headers_a).json()

    for path in (
        f"/api/v1/experiments/{exp['id']}",
        f"/api/v1/experiments/{exp['id']}/result",
        f"/api/v1/experiments/{exp['id']}/evidence",
    ):
        assert client.get(path, headers=headers_b).status_code == 404
    assert client.get("/api/v1/experiments/active", headers=headers_b).json()["experiment"] is None


def test_complete_with_no_data_is_insufficient(client, auth_headers):
    headers = auth_headers("t-empty@example.com")
    exp = _start_experiment(client, headers).json()
    resp = client.post(f"/api/v1/experiments/{exp['id']}/complete", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["evidence_level"] == "INSUFFICIENT"
    assert body["causality_proven"] is False
    assert body["metrics"], "tracked metrics are still listed"
    for metric in body["metrics"]:
        assert metric["baseline_mean"] is None, "no data was measured; means must stay NULL"
        assert metric["experiment_mean"] is None
        assert metric["direction"] == "no_change"
    assert not any(w in body["summary"].lower() for w in BANNED_CAUSAL_WORDS)


def test_complete_with_improvement_produces_evidence(client, auth_headers):
    headers = auth_headers("t-improv@example.com")
    db = SessionLocal()
    _seed_baseline(db, 1, sleep=6.1, energy=5)
    db.close()

    exp = _start_experiment(client, headers).json()
    for offset in range(7):
        resp = _log_experiment_day(client, headers, exp["id"], offset, 7.9, 8, True)

    resp = client.post(f"/api/v1/experiments/{exp['id']}/complete", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["evidence_level"] in {"EARLY_OBSERVATION", "PROMISING_OBSERVATION"}
    assert body["causality_proven"] is False
    assert body["metrics"], "improved energy should produce metric comparisons"
    energy = next(m for m in body["metrics"] if m["metric"] == "energy")
    assert energy["experiment_mean"] > energy["baseline_mean"]
    assert energy["direction"] in {"improved", "no_change"}
    assert not any(w in body["summary"].lower() for w in BANNED_CAUSAL_WORDS)
    assert body["limitations"]


def test_skipped_days_are_allowed_and_not_fabricated(client, auth_headers):
    headers = auth_headers("t-skip@example.com")
    db = SessionLocal()
    _seed_baseline(db, 1, sleep=6.1, energy=5)
    db.close()

    exp = _start_experiment(client, headers).json()
    for offset in (0, 2, 3, 6):
        resp = _log_experiment_day(client, headers, exp["id"], offset, 8.0, 8, True)

    body = client.post(f"/api/v1/experiments/{exp['id']}/complete", headers=headers).json()
    assert body["evidence_level"] in {"EARLY_OBSERVATION", "PROMISING_OBSERVATION"}
    assert 0.0 < body["data_completeness"] < 1.0


def test_completed_experiment_cannot_be_logged_and_no_double_complete(client, auth_headers):
    headers = auth_headers("t-Double@example.com")
    exp = _start_experiment(client, headers).json()
    client.post(f"/api/v1/experiments/{exp['id']}/complete", headers=headers)

    resp = client.post(
        f"/api/v1/experiments/{exp['id']}/daily-log",
        json={"date": str(TODAY + timedelta(days=1)), "day_number": 1, "target_met": True, "metrics": {"sleep_hours": 7, "energy": 6}},
        headers=headers,
    )
    assert resp.status_code == 409

    resp2 = client.post(f"/api/v1/experiments/{exp['id']}/complete", headers=headers)
    assert resp2.status_code == 409


def test_cancel_reopens_template_for_new_experiment(client, auth_headers):
    headers = auth_headers("t-cancel@example.com")
    exp = _start_experiment(client, headers).json()
    resp = client.post(f"/api/v1/experiments/{exp['id']}/cancel", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"

    r2 = _start_experiment(client, headers)
    assert r2.status_code == 201, "a cancelled experiment must not block a new one"
    assert r2.json()["id"] != exp["id"]


def test_recommendation_respects_cooldown_after_completion(client, auth_headers):
    headers = auth_headers("t-cooldown@example.com")
    db = SessionLocal()
    rng = random.Random(7)
    prev_sleep = rng.uniform(4.5, 8.5)
    for i in range(34):
        d = _days_ago(34 - i)
        sleep = round(min(8.5, max(4.5, rng.uniform(4.5, 8.5))), 1)
        energy = int(round(max(1, min(10, 4.5 + (prev_sleep - 6.0) * 2.0 + rng.gauss(0, 0.5)))))
        _seed_log(db, 1, d, sleep_hours=sleep, energy=energy, stress=3, mood="good", steps=6000)
        prev_sleep = sleep
    db.close()

    rec = client.get("/api/v1/experiments/recommended", headers=headers).json()
    assert rec["recommendation"] is not None

    exp = _start_experiment(client, headers).json()
    client.post(f"/api/v1/experiments/{exp['id']}/complete", headers=headers)

    rec2 = client.get("/api/v1/experiments/recommended", headers=headers).json()
    assert rec2["recommendation"] is None, "cooldown should suppress a just-completed experiment"


def test_history_reflects_cancelled_and_completed(client, auth_headers):
    headers = auth_headers("t-history@example.com")
    exp = _start_experiment(client, headers).json()
    client.post(f"/api/v1/experiments/{exp['id']}/cancel", headers=headers)
    exp2 = _start_experiment(client, headers).json()
    client.post(f"/api/v1/experiments/{exp2['id']}/complete", headers=headers)

    resp = client.get("/api/v1/experiments/history", headers=headers)
    assert resp.status_code == 200
    items = resp.json()
    by_id = {item["experiment"]["id"]: item for item in items}
    assert by_id[exp["id"]]["experiment"]["status"] == "cancelled"
    assert by_id[exp2["id"]]["experiment"]["status"] == "completed"
    assert by_id[exp2["id"]]["result"] is not None


# --- Phase 4: evaluation endpoints -------------------------------------------


def _build_evaluated_experiment(client, headers):
    db = SessionLocal()
    _seed_baseline(db, 1, sleep=6.1, energy=5)
    db.close()
    exp = _start_experiment(client, headers).json()
    for offset in range(7):
        _log_experiment_day(client, headers, exp["id"], offset, 7.9, 8, True)
    return exp


def test_evaluate_requires_completed_experiment(client, auth_headers):
    headers = auth_headers("t-lazy@example.com")
    exp = _start_experiment(client, headers).json()
    resp = client.post(f"/api/v1/experiments/{exp['id']}/evaluate", headers=headers)
    assert resp.status_code == 409


def test_evaluation_endpoints_after_completion(client, auth_headers):
    headers = auth_headers("t-eval@example.com")
    exp = _build_evaluated_experiment(client, headers)
    client.post(f"/api/v1/experiments/{exp['id']}/complete", headers=headers)

    ev = client.get(f"/api/v1/experiments/{exp['id']}/evaluation", headers=headers)
    assert ev.status_code == 200
    assert ev.json()["causality_proven"] is False

    metrics = client.get(f"/api/v1/experiments/{exp['id']}/metrics", headers=headers)
    assert metrics.status_code == 200
    names = {m["metric"] for m in metrics.json()}
    assert {"energy", "stress"}.issubset(names)

    evidence = client.get(f"/api/v1/experiments/{exp['id']}/evidence", headers=headers)
    assert evidence.status_code == 200
    assert evidence.json()["evidence_level"] in {"EARLY_OBSERVATION", "PROMISING_OBSERVATION"}
    assert evidence.json()["causality_proven"] is False

    candidate = client.get(
        f"/api/v1/experiments/{exp['id']}/learning-candidate", headers=headers
    ).json()
    assert candidate is not None
    assert candidate["causality_proven"] is False
    assert candidate["evidence_level"] in {"EARLY_OBSERVATION", "PROMISING_OBSERVATION"}
    import json

    assert not any(w in json.dumps(candidate).lower() for w in BANNED_CAUSAL_WORDS)


def test_learning_candidate_accept_and_reject(client, auth_headers):
    headers = auth_headers("t-cand@example.com")
    exp = _build_evaluated_experiment(client, headers)
    client.post(f"/api/v1/experiments/{exp['id']}/complete", headers=headers)
    candidate = client.get(
        f"/api/v1/experiments/{exp['id']}/learning-candidate", headers=headers
    ).json()

    resp = client.post(
        f"/api/v1/learning-candidates/{candidate['id']}/accept", headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"

    resp = client.post(
        f"/api/v1/learning-candidates/{candidate['id']}/reject", headers=headers
    )
    assert resp.status_code in (409, 400), "an accepted candidate is finalised"


def test_learning_candidates_are_user_scoped(client, auth_headers):
    headers_a = auth_headers("t-sa@example.com")
    headers_b = auth_headers("t-sb@example.com")
    exp = _build_evaluated_experiment(client, headers_a)
    client.post(f"/api/v1/experiments/{exp['id']}/complete", headers=headers_a)
    candidate = client.get(
        f"/api/v1/experiments/{exp['id']}/learning-candidate", headers=headers_a
    ).json()

    assert client.post(
        f"/api/v1/learning-candidates/{candidate['id']}/accept", headers=headers_b
    ).status_code == 404
    listed = client.get("/api/v1/learning-candidates", headers=headers_b).json()
    assert listed["candidates"] == []
    own = client.get("/api/v1/learning-candidates", headers=headers_a).json()
    assert len(own["candidates"]) == 1


def test_metric_results_never_invent_values(client, auth_headers):
    """The response only ever contains metrics this template actually tracks."""
    headers = auth_headers("t-null@example.com")
    db = SessionLocal()
    _seed_baseline(db, 1, sleep=6.1, energy=5)
    db.close()
    exp = _start_experiment(client, headers).json()
    for offset in range(7):
        _log_experiment_day(client, headers, exp["id"], offset, 7.9, 8, True)
    client.post(f"/api/v1/experiments/{exp['id']}/complete", headers=headers)

    metrics = client.get(f"/api/v1/experiments/{exp['id']}/metrics", headers=headers).json()
    tracked = {"sleep_hours", "energy", "stress", "mood"}
    assert metrics, "the experiment tracked at least one metric"
    assert {m["metric"] for m in metrics} <= tracked, "no untracked metric may be invented"
    energy = next(m for m in metrics if m["metric"] == "energy")
    assert energy["baseline_mean"] == 5.0
    assert energy["experiment_mean"] > 7.0