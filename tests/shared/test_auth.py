"""Tests for shared/auth.py — authentication helpers.

Covers password hashing, session lifecycle, session validation,
password management, and admin helpers. All file I/O is redirected
to tmp_path to avoid touching real config.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

# We need to patch module-level path constants before the code uses them.
import shared.auth as auth_mod


@pytest.fixture(autouse=True)
def _isolate_auth_files(tmp_path):
    """Redirect auth file paths to tmp_path for every test."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    with patch.object(auth_mod, "_CONFIG_DIR", config_dir), \
         patch.object(auth_mod, "_AUTH_FILE", config_dir / "auth.json"), \
         patch.object(auth_mod, "_SESSIONS_FILE", config_dir / "sessions.json"):
        yield


# ── Password hashing ─────────────────────────────────────────────────────


class TestHashPassword:
    def test_deterministic(self):
        assert auth_mod._hash_password("secret") == auth_mod._hash_password("secret")

    def test_different_passwords_differ(self):
        assert auth_mod._hash_password("a") != auth_mod._hash_password("b")

    def test_returns_hex_string(self):
        h = auth_mod._hash_password("test")
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex digest


# ── Auth file load/save ──────────────────────────────────────────────────


class TestLoadSaveAuth:
    def test_load_returns_none_when_missing(self):
        assert auth_mod._load_auth() is None

    def test_round_trip(self):
        data = {"password_hash": "abc", "session_hours": 12, "enabled": True}
        auth_mod._save_auth(data)
        loaded = auth_mod._load_auth()
        assert loaded == data

    def test_load_returns_none_on_corrupt_json(self):
        auth_mod._AUTH_FILE.write_text("NOT JSON{{{")
        assert auth_mod._load_auth() is None


# ── Session management ───────────────────────────────────────────────────


class TestSessions:
    def test_load_empty_when_missing(self):
        assert auth_mod._load_sessions() == {}

    def test_create_session_returns_hex_token(self):
        token = auth_mod._create_session()
        assert isinstance(token, str)
        assert len(token) == 32  # uuid4().hex

    def test_create_session_persists(self):
        token = auth_mod._create_session()
        sessions = auth_mod._load_sessions()
        assert token in sessions

    def test_destroy_session(self):
        token = auth_mod._create_session()
        auth_mod._destroy_session(token)
        sessions = auth_mod._load_sessions()
        assert token not in sessions

    def test_destroy_nonexistent_session_is_safe(self):
        auth_mod._destroy_session("nonexistent")  # should not raise

    def test_load_sessions_on_corrupt_json(self):
        auth_mod._SESSIONS_FILE.write_text("corrupt!!!")
        assert auth_mod._load_sessions() == {}


# ── Session validation ───────────────────────────────────────────────────


class TestSessionIsValid:
    def test_valid_session(self):
        # Set up auth with 24-hour sessions
        auth_mod._save_auth({"session_hours": 24, "enabled": True})
        token = auth_mod._create_session()
        assert auth_mod._session_is_valid(token) is True

    def test_expired_session(self):
        auth_mod._save_auth({"session_hours": 1, "enabled": True})
        # Manually create a session 2 hours ago
        sessions = auth_mod._load_sessions()
        old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        sessions["old-token"] = old_time
        auth_mod._save_sessions(sessions)
        assert auth_mod._session_is_valid("old-token") is False

    def test_nonexistent_token(self):
        assert auth_mod._session_is_valid("does-not-exist") is False

    def test_malformed_timestamp(self):
        sessions = {"bad-token": "not-a-date"}
        auth_mod._save_sessions(sessions)
        assert auth_mod._session_is_valid("bad-token") is False

    def test_uses_default_session_hours_when_not_set(self):
        # No auth file → default 24 hours
        token = auth_mod._create_session()
        assert auth_mod._session_is_valid(token) is True


# ── Admin helpers ─────────────────────────────────────────────────────────


class TestChangePassword:
    def test_success(self):
        auth_mod._save_auth({
            "password_hash": auth_mod._hash_password("old"),
            "session_hours": 24,
            "enabled": True,
        })
        ok, msg = auth_mod.change_password("old", "new")
        assert ok is True
        assert "success" in msg.lower()
        # Verify new password hash is stored
        auth = auth_mod._load_auth()
        assert auth["password_hash"] == auth_mod._hash_password("new")

    def test_wrong_current_password(self):
        auth_mod._save_auth({
            "password_hash": auth_mod._hash_password("correct"),
            "session_hours": 24,
            "enabled": True,
        })
        ok, msg = auth_mod.change_password("wrong", "new")
        assert ok is False
        assert "incorrect" in msg.lower()

    def test_no_password_configured(self):
        ok, msg = auth_mod.change_password("any", "new")
        assert ok is False


class TestInvalidateAllSessions:
    def test_clears_all(self):
        auth_mod._create_session()
        auth_mod._create_session()
        assert len(auth_mod._load_sessions()) == 2
        auth_mod.invalidate_all_sessions()
        assert auth_mod._load_sessions() == {}


class TestSessionHours:
    def test_get_default(self):
        assert auth_mod.get_session_hours() == 24

    def test_set_and_get(self):
        auth_mod.set_session_hours(8)
        assert auth_mod.get_session_hours() == 8


class TestAuthEnabled:
    def test_default_not_enabled(self):
        assert auth_mod.is_auth_enabled() is False

    def test_set_enabled(self):
        auth_mod._save_auth({"password_hash": "x", "enabled": False, "session_hours": 24})
        auth_mod.set_auth_enabled(True)
        assert auth_mod.is_auth_enabled() is True

    def test_set_disabled(self):
        auth_mod._save_auth({"password_hash": "x", "enabled": True, "session_hours": 24})
        auth_mod.set_auth_enabled(False)
        assert auth_mod.is_auth_enabled() is False


class TestIsPasswordSet:
    def test_no_file(self):
        assert auth_mod.is_password_set() is False

    def test_with_password(self):
        auth_mod._save_auth({"password_hash": "abc123"})
        assert auth_mod.is_password_set() is True

    def test_empty_hash(self):
        auth_mod._save_auth({"password_hash": ""})
        assert auth_mod.is_password_set() is False


class TestResetPassword:
    def test_creates_auth_if_missing(self):
        auth_mod.reset_password("newpass")
        auth = auth_mod._load_auth()
        assert auth["password_hash"] == auth_mod._hash_password("newpass")

    def test_overwrites_existing(self):
        auth_mod._save_auth({"password_hash": "old", "enabled": True, "session_hours": 12})
        auth_mod.reset_password("newpass")
        auth = auth_mod._load_auth()
        assert auth["password_hash"] == auth_mod._hash_password("newpass")
        assert auth["enabled"] is True  # preserved


class TestActiveSessionCount:
    def test_zero_when_empty(self):
        assert auth_mod.active_session_count() == 0

    def test_counts_valid_sessions(self):
        auth_mod._save_auth({"session_hours": 24})
        auth_mod._create_session()
        auth_mod._create_session()
        assert auth_mod.active_session_count() == 2

    def test_excludes_expired(self):
        auth_mod._save_auth({"session_hours": 1})
        # One valid
        auth_mod._create_session()
        # One expired (2 hours ago)
        sessions = auth_mod._load_sessions()
        old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        sessions["expired-token"] = old_time
        auth_mod._save_sessions(sessions)
        assert auth_mod.active_session_count() == 1
