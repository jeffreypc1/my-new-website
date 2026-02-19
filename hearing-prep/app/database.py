"""SQLite persistence layer for Hearing Prep sessions.

Three tables: sessions, turns, evaluations.
Uses WAL mode for concurrent read safety.
Database stored at hearing-prep/data/hearing_prep.db.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

_DB_DIR = Path(__file__).resolve().parent.parent / "data"
_DB_PATH = _DB_DIR / "hearing_prep.db"


def _connect() -> sqlite3.Connection:
    """Return a connection with WAL mode and foreign keys enabled."""
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            client_name TEXT NOT NULL DEFAULT '',
            client_id TEXT NOT NULL DEFAULT '',
            case_type TEXT NOT NULL DEFAULT '',
            mode TEXT NOT NULL DEFAULT 'attorney',
            language TEXT NOT NULL DEFAULT 'English',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            notes TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS turns (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            turn_number INTEGER NOT NULL,
            question_id TEXT NOT NULL DEFAULT '',
            question_text TEXT NOT NULL DEFAULT '',
            audio_blob BLOB,
            transcript TEXT NOT NULL DEFAULT '',
            language_code TEXT NOT NULL DEFAULT 'en-US',
            confidence REAL NOT NULL DEFAULT 0.0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS evaluations (
            id TEXT PRIMARY KEY,
            turn_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            evaluation_text TEXT NOT NULL DEFAULT '',
            score INTEGER NOT NULL DEFAULT 0,
            strengths TEXT NOT NULL DEFAULT '[]',
            weaknesses TEXT NOT NULL DEFAULT '[]',
            follow_up_question TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (turn_id) REFERENCES turns(id) ON DELETE CASCADE,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id);
        CREATE INDEX IF NOT EXISTS idx_evaluations_session ON evaluations(session_id);
        CREATE INDEX IF NOT EXISTS idx_evaluations_turn ON evaluations(turn_id);
    """)
    conn.close()


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

def create_session(
    client_name: str,
    client_id: str = "",
    case_type: str = "",
    mode: str = "attorney",
    language: str = "English",
    notes: str = "",
) -> str:
    """Create a new session and return its UUID."""
    sid = str(uuid.uuid4())
    now = datetime.now().isoformat(timespec="seconds")
    conn = _connect()
    conn.execute(
        """INSERT INTO sessions (id, client_name, client_id, case_type, mode,
           language, created_at, updated_at, status, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)""",
        (sid, client_name, client_id, case_type, mode, language, now, now, notes),
    )
    conn.commit()
    conn.close()
    return sid


def get_session(session_id: str) -> dict | None:
    """Return a session dict or None."""
    conn = _connect()
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_sessions(limit: int = 50) -> list[dict]:
    """Return recent sessions, newest first."""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_session(session_id: str, **fields) -> None:
    """Update one or more session fields."""
    allowed = {"client_name", "client_id", "case_type", "mode", "language", "status", "notes"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    updates["updated_at"] = datetime.now().isoformat(timespec="seconds")
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [session_id]
    conn = _connect()
    conn.execute(f"UPDATE sessions SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def delete_session(session_id: str) -> None:
    """Delete a session and its turns/evaluations (cascade)."""
    conn = _connect()
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Turns
# ---------------------------------------------------------------------------

def add_turn(
    session_id: str,
    turn_number: int,
    question_id: str = "",
    question_text: str = "",
    audio_blob: bytes | None = None,
    transcript: str = "",
    language_code: str = "en-US",
    confidence: float = 0.0,
) -> str:
    """Add a turn and return its UUID."""
    tid = str(uuid.uuid4())
    now = datetime.now().isoformat(timespec="seconds")
    conn = _connect()
    conn.execute(
        """INSERT INTO turns (id, session_id, turn_number, question_id,
           question_text, audio_blob, transcript, language_code, confidence, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (tid, session_id, turn_number, question_id, question_text,
         audio_blob, transcript, language_code, confidence, now),
    )
    conn.commit()
    conn.close()
    # Touch session updated_at
    update_session(session_id)
    return tid


def get_turns(session_id: str) -> list[dict]:
    """Return all turns for a session, ordered by turn_number."""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM turns WHERE session_id = ? ORDER BY turn_number",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Evaluations
# ---------------------------------------------------------------------------

def add_evaluation(
    turn_id: str,
    session_id: str,
    evaluation_text: str = "",
    score: int = 0,
    strengths: list[str] | None = None,
    weaknesses: list[str] | None = None,
    follow_up_question: str = "",
) -> str:
    """Add an evaluation and return its UUID."""
    eid = str(uuid.uuid4())
    now = datetime.now().isoformat(timespec="seconds")
    conn = _connect()
    conn.execute(
        """INSERT INTO evaluations (id, turn_id, session_id, evaluation_text,
           score, strengths, weaknesses, follow_up_question, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (eid, turn_id, session_id, evaluation_text, score,
         json.dumps(strengths or []), json.dumps(weaknesses or []),
         follow_up_question, now),
    )
    conn.commit()
    conn.close()
    return eid


def get_evaluations(session_id: str) -> list[dict]:
    """Return all evaluations for a session, ordered by creation time."""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM evaluations WHERE session_id = ? ORDER BY created_at",
        (session_id,),
    ).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        d["strengths"] = json.loads(d["strengths"]) if d["strengths"] else []
        d["weaknesses"] = json.loads(d["weaknesses"]) if d["weaknesses"] else []
        results.append(d)
    return results


def get_session_transcript(session_id: str) -> list[dict]:
    """Return turns joined with their evaluations for a full transcript.

    Each item has: turn fields + 'evaluation' dict (or None).
    """
    conn = _connect()
    turns = conn.execute(
        "SELECT * FROM turns WHERE session_id = ? ORDER BY turn_number",
        (session_id,),
    ).fetchall()
    evals = conn.execute(
        "SELECT * FROM evaluations WHERE session_id = ? ORDER BY created_at",
        (session_id,),
    ).fetchall()
    conn.close()

    eval_by_turn: dict[str, dict] = {}
    for e in evals:
        d = dict(e)
        d["strengths"] = json.loads(d["strengths"]) if d["strengths"] else []
        d["weaknesses"] = json.loads(d["weaknesses"]) if d["weaknesses"] else []
        eval_by_turn[d["turn_id"]] = d

    result = []
    for t in turns:
        td = dict(t)
        td.pop("audio_blob", None)  # Don't include raw audio in transcript
        td["evaluation"] = eval_by_turn.get(td["id"])
        result.append(td)
    return result
