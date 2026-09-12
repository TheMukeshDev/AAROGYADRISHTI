"""Security helper unit tests (no DB required)."""

from __future__ import annotations

import pytest

from app.core.security import (
    hash_password,
    password_problems,
    verify_password,
)


def test_hash_and_verify():
    h = hash_password("MyP@ss123")
    assert verify_password("MyP@ss123", h) is True
    assert verify_password("WrongPass", h) is False


def test_hash_is_deterministic_different():
    h1 = hash_password("samepass")
    h2 = hash_password("samepass")
    # bcrypt salts are random so hashes should differ each time.
    assert h1 != h2
    # But both verify correctly.
    assert verify_password("samepass", h1) is True
    assert verify_password("samepass", h2) is True


def test_verify_empty_hash():
    assert verify_password("anything", None) is False
    assert verify_password("anything", "") is False
    assert verify_password("anything", "garbage") is False


def test_password_policy_too_short():
    problems = password_problems("Ab1!", min_length=8)
    assert any("8 characters" in p for p in problems)


def test_password_policy_no_mixed():
    problems = password_problems("12345678901235", min_length=6)
    assert any("mix" in p for p in problems)


def test_password_policy_only_alpha():
    problems = password_problems("onlyletters", min_length=6)
    assert any("mix" in p for p in problems)


def test_password_valid():
    assert password_problems("Str0ng!Pass") == []