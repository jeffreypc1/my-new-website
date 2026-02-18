"""Shared password authentication for all staff tools.

Every dashboard calls require_auth() right after st.set_page_config() and CSS.
If the user isn't authenticated, it renders a login form and calls st.stop()
so no tool UI appears until they log in.

Session tokens are shared across tools via data/config/sessions.json.
Password hash is stored in data/config/auth.json.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"
_AUTH_FILE = _CONFIG_DIR / "auth.json"
_SESSIONS_FILE = _CONFIG_DIR / "sessions.json"

_DEFAULT_SESSION_HOURS = 24


# ── Internal helpers ─────────────────────────────────────────────────────────


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _load_auth() -> dict | None:
    if not _AUTH_FILE.exists():
        return None
    try:
        return json.loads(_AUTH_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _save_auth(data: dict) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _AUTH_FILE.write_text(json.dumps(data, indent=2))


def _load_sessions() -> dict:
    if not _SESSIONS_FILE.exists():
        return {}
    try:
        return json.loads(_SESSIONS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save_sessions(sessions: dict) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _SESSIONS_FILE.write_text(json.dumps(sessions, indent=2))


def _session_is_valid(token: str) -> bool:
    """Check if a session token exists and hasn't expired."""
    sessions = _load_sessions()
    ts = sessions.get(token)
    if not ts:
        return False
    try:
        created = datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return False
    auth = _load_auth() or {}
    max_hours = auth.get("session_hours", _DEFAULT_SESSION_HOURS)
    elapsed = (datetime.now(timezone.utc) - created).total_seconds() / 3600
    return elapsed < max_hours


def _create_session() -> str:
    """Create a new session token and persist it."""
    token = uuid.uuid4().hex
    sessions = _load_sessions()
    sessions[token] = datetime.now(timezone.utc).isoformat()
    _save_sessions(sessions)
    return token


def _destroy_session(token: str) -> None:
    """Remove a session token."""
    sessions = _load_sessions()
    sessions.pop(token, None)
    _save_sessions(sessions)


# ── Login UI CSS ─────────────────────────────────────────────────────────────

_LOGIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
#MainMenu, footer,
div[data-testid="stToolbar"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: linear-gradient(160deg, #f8f9fc 0%, #eef1f8 50%, #e8edf6 100%);
}
.login-card {
    max-width: 400px;
    margin: 8vh auto 0;
    padding: 2.5rem 2rem 2rem;
    background: white;
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    text-align: center;
}
.login-card h2 {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    color: #1a2744;
    margin: 0 0 0.25rem;
    font-size: 1.4rem;
    letter-spacing: -0.02em;
}
.login-card p {
    color: #86868b;
    font-size: 0.9rem;
    margin: 0 0 1.5rem;
}
</style>
"""


# ── Public API ───────────────────────────────────────────────────────────────


def require_auth() -> None:
    """Gate the current page behind password authentication.

    Call right after st.set_page_config() and CSS. If not authenticated,
    renders a login (or initial setup) form and calls st.stop().
    """
    # Already logged in?
    token = st.session_state.get("_auth_token")
    if token and _session_is_valid(token):
        return

    # Token expired or invalid — clear it
    if token:
        st.session_state.pop("_auth_token", None)

    auth = _load_auth()

    if auth is None:
        # First-time setup: no password configured yet
        _render_setup_form()
    else:
        _render_login_form(auth)

    st.stop()


def render_logout() -> None:
    """Render a small right-aligned Log Out button after the nav bar."""
    if not st.session_state.get("_auth_token"):
        return
    cols = st.columns([8, 1])
    with cols[1]:
        if st.button("Log Out", key="_auth_logout", type="tertiary"):
            token = st.session_state.pop("_auth_token", None)
            if token:
                _destroy_session(token)
            st.rerun()


# ── Form renderers ───────────────────────────────────────────────────────────


def _render_login_form(auth: dict) -> None:
    """Render the password login form."""
    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    st.markdown(
        '<div class="login-card">'
        "<h2>O'Brien Immigration Law</h2>"
        "<p>Staff Tools</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    _spacer_l, col, _spacer_r = st.columns([1, 1, 1])
    with col:
        with st.form("_auth_login_form"):
            password = st.text_input(
                "Password", type="password", placeholder="Enter password"
            )
            submitted = st.form_submit_button("Log In", use_container_width=True)

        if submitted:
            if not password:
                st.error("Please enter a password.")
            elif _hash_password(password) == auth.get("password_hash"):
                token = _create_session()
                st.session_state["_auth_token"] = token
                st.rerun()
            else:
                st.error("Incorrect password.")


def _render_setup_form() -> None:
    """Render the initial password setup form (first run)."""
    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    st.markdown(
        '<div class="login-card">'
        "<h2>O'Brien Immigration Law</h2>"
        "<p>Set a password to secure your staff tools</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    _spacer_l, col, _spacer_r = st.columns([1, 1, 1])
    with col:
        with st.form("_auth_setup_form"):
            pw1 = st.text_input(
                "New Password", type="password", placeholder="Choose a password"
            )
            pw2 = st.text_input(
                "Confirm Password", type="password", placeholder="Confirm password"
            )
            submitted = st.form_submit_button(
                "Set Password", use_container_width=True
            )

        if submitted:
            if not pw1:
                st.error("Password cannot be empty.")
            elif pw1 != pw2:
                st.error("Passwords do not match.")
            else:
                _save_auth(
                    {
                        "password_hash": _hash_password(pw1),
                        "session_hours": _DEFAULT_SESSION_HOURS,
                    }
                )
                token = _create_session()
                st.session_state["_auth_token"] = token
                st.rerun()


# ── Admin helpers (used by admin panel) ──────────────────────────────────────


def change_password(current: str, new: str) -> tuple[bool, str]:
    """Validate current password and update to new one.

    Returns (success, message).
    """
    auth = _load_auth()
    if auth is None:
        return False, "No password is configured."
    if _hash_password(current) != auth.get("password_hash"):
        return False, "Current password is incorrect."
    auth["password_hash"] = _hash_password(new)
    _save_auth(auth)
    return True, "Password changed successfully."


def invalidate_all_sessions() -> None:
    """Clear all session tokens, forcing everyone to re-login."""
    _save_sessions({})


def get_session_hours() -> int:
    auth = _load_auth() or {}
    return auth.get("session_hours", _DEFAULT_SESSION_HOURS)


def set_session_hours(hours: int) -> None:
    auth = _load_auth() or {"password_hash": "", "session_hours": _DEFAULT_SESSION_HOURS}
    auth["session_hours"] = hours
    _save_auth(auth)


def is_password_set() -> bool:
    auth = _load_auth()
    return auth is not None and bool(auth.get("password_hash"))


def active_session_count() -> int:
    """Count non-expired sessions."""
    sessions = _load_sessions()
    auth = _load_auth() or {}
    max_hours = auth.get("session_hours", _DEFAULT_SESSION_HOURS)
    now = datetime.now(timezone.utc)
    count = 0
    for ts in sessions.values():
        try:
            created = datetime.fromisoformat(ts)
            if (now - created).total_seconds() / 3600 < max_hours:
                count += 1
        except (ValueError, TypeError):
            pass
    return count
