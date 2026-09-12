"""Phase 6 - AI preventive lifestyle coach tests.

The coach falls back to a fully deterministic provider, so every reply is
reproducible. Assertions focus on the non-medical invariant, ownership, and the
deterministic rule-based services (next action, weekly summary).
"""

from __future__ import annotations

import random
from datetime import date, timedelta

from app.database.session import SessionLocal
from app.repositories.daily_log import DailyLogRepository

TODAY = date.today()


def _seed_logs(db, user_id: int, days: int = 4, sleep: float = 7.0, energy: int = 7):
    for d in range(1, days + 1):
        DailyLogRepository().create(
            db, user_id, date=TODAY - timedelta(days=d), sleep_hours=sleep, energy=energy, stress=2, mood="good", steps=8000
        )


def _new_conversation(client, headers):
    resp = client.post(
        "/api/v1/coach/conversations", json={"title": "My check-in"}, headers=headers
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_and_empty_state_reply(client, auth_headers):
    headers = auth_headers("coach-empty@example.com")
    conv = _new_conversation(client, headers)

    resp = client.post(
        f"/api/v1/coach/conversations/{conv['id']}/messages",
        json={"content": "How am I doing?"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["provider"] == "deterministic"
    reply = body["reply"]["content"]
    assert "not a doctor" in reply.lower()  # disclaimer always present

    msgs = client.get(
        f"/api/v1/coach/conversations/{conv['id']}/messages", headers=headers
    ).json()
    roles = [m["role"] for m in msgs["messages"]]
    assert roles == ["user", "coach"]
    assert msgs["messages"][1]["provider"] == "deterministic"
    assert msgs["messages"][1]["safety_applied"] is True


def test_reply_after_data_mentions_patterns(client, auth_headers):
    headers = auth_headers("coach-data@example.com")
    db = SessionLocal()
    rng = random.Random(3)
    prev_sleep = rng.uniform(4.5, 8.5)
    for i in range(20):
        d = TODAY - timedelta(days=20 - i)
        sleep = round(min(8.5, max(4.5, rng.uniform(4.5, 8.5))), 1)
        energy = int(round(max(1, min(10, 4.5 + (prev_sleep - 6.0) * 2.0 + rng.gauss(0, 0.5)))))
        DailyLogRepository().create(
            db, 1, date=d, sleep_hours=sleep, energy=energy, stress=3, mood="good", steps=7000
        )
        prev_sleep = sleep
    db.close()

    conv = _new_conversation(client, headers)
    resp = client.post(
        f"/api/v1/coach/conversations/{conv['id']}/messages",
        json={"content": "Tell me about my sleep"},
        headers=headers,
    )
    reply = resp.json()["reply"]["content"]
    assert "I hear you" in reply
    assert "patterns" in reply.lower() or "your own" in reply.lower()
    assert "not a doctor" in reply.lower()
    # no phone-like digit runs, no dosage text
    import re

    assert not re.search(r"(?<!\d)\d{7,}(?!\d)", reply)


def test_prohibited_topic_gets_scope_note(client, auth_headers):
    headers = auth_headers("coach-scope@example.com")
    conv = _new_conversation(client, headers)
    resp = client.post(
        f"/api/v1/coach/conversations/{conv['id']}/messages",
        json={"content": "What medicine should I take for my headache?"},
        headers=headers,
    )
    reply = resp.json()["reply"]["content"]
    assert "outside what I can help with" in reply
    assert "clinician" in reply.lower()


def test_conversation_and_messages_are_owned(client, auth_headers):
    headers_a = auth_headers("coach-own-a@example.com")
    headers_b = auth_headers("coach-own-b@example.com")
    conv = _new_conversation(client, headers_a)
    conv_b = _new_conversation(client, headers_b)

    assert client.get(
        f"/api/v1/coach/conversations/{conv['id']}/messages", headers=headers_b
    ).status_code == 404
    assert client.post(
        f"/api/v1/coach/conversations/{conv['id']}/messages",
        json={"content": "hi"},
        headers=headers_b,
    ).status_code == 404
    assert client.get(
        f"/api/v1/coach/conversations/{conv_b['id']}/messages", headers=headers_a
    ).status_code == 404

    mine = client.get("/api/v1/coach/conversations", headers=headers_a).json()
    assert mine["count"] == 1
    assert mine["conversations"][0]["id"] == conv["id"]


def test_next_action_collect_more_data_for_new_user(client, auth_headers):
    headers = auth_headers("next-1@example.com")
    resp = client.get("/api/v1/coach/next-action", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["action_type"] == "collect_more_data"


def test_next_action_continues_active_experiment(client, auth_headers):
    headers = auth_headers("next-2@example.com")
    client.post("/api/v1/experiments", json={"experiment_type": "sleep_consistency"}, headers=headers)
    resp = client.get("/api/v1/coach/next-action", headers=headers)
    assert resp.json()["action_type"] == "continue_routine"


def test_weekly_summary_with_and_without_data(client, auth_headers):
    headers_empty = auth_headers("week-0@example.com")
    empty = client.get("/api/v1/coach/weekly-summary", headers=headers_empty).json()
    assert empty["days_tracked"] == 0
    assert "check-ins from you yet" in empty["narrative"]

    headers = auth_headers("week-1@example.com")
    db = SessionLocal()
    _seed_logs(db, 2, days=3, sleep=8.0, energy=9)
    db.close()
    summary = client.get("/api/v1/coach/weekly-summary", headers=headers).json()
    assert summary["days_tracked"] == 3
    assert summary["completion_rate"] == round(3 / 7, 2)
    assert summary["averages"]["sleep_hours"]["value"] == 8.0
    assert summary["averages"]["energy"]["count"] == 3


def test_safety_guard_unit_rules():
    from app.ai.safety_guard import is_prohibited_user_question, sanitize_coach_reply

    assert is_prohibited_user_question("What medicine should I take?") is True
    assert is_prohibited_user_question("How was my sleep this week?") is False

    clean = sanitize_coach_reply("Take 500 mg of paracetamol.", role="coach")
    assert "500 mg" not in clean
    assert "dose prescribed" in clean
    assert "not a doctor" in clean.lower()

    clean2 = sanitize_coach_reply("Call me at 9876543210", role="coach")
    assert "9876543210" not in clean2
    assert "not a doctor" in clean2.lower()


def test_deterministic_provider_unit():
    from app.ai.base_provider import CoachContext
    from app.ai.deterministic_provider import generate_deterministic_reply

    context = CoachContext(
        user_name="Alex",
        days_tracked=5,
        has_daily_data=True,
        patterns=[{"pattern_id": "sleep_energy", "feature_label": "sleep", "target_label": "energy", "strength_label": "early", "correlation": 0.4}],
        next_action={"action_type": "continue_routine", "heading": "Keep going", "reason": "Stick with the routine."},
    )
    reply = generate_deterministic_reply(context, "How am I doing?")
    assert "Alex" in reply or "Thanks for checking in" in reply
    assert "sleep" in reply.lower()
    assert "not a doctor" in reply.lower()
    assert "0.40" in reply  # only real correlation, no invented ones


def test_send_message_persists_and_returns_reply(client, auth_headers):
    headers = auth_headers("coach-persist@example.com")
    conv = _new_conversation(client, headers)
    for i in range(2):
        resp = client.post(
            f"/api/v1/coach/conversations/{conv['id']}/messages",
            json={"content": f"message {i}"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text

    msgs = client.get(
        f"/api/v1/coach/conversations/{conv['id']}/messages", headers=headers
    ).json()
    assert len(msgs["messages"]) == 4  # 2 user + 2 coach
    assert [m["role"] for m in msgs["messages"]] == ["user", "coach", "user", "coach"]