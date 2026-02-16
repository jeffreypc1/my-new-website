"""Office attorney management — JSON-backed CRUD.

Stores attorney info at data/config/attorneys.json. Used by the
Forms Assistant to auto-fill attorney fields on uploaded PDF forms.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"
ATTORNEYS_FILE = CONFIG_DIR / "attorneys.json"


def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_attorneys() -> list[dict]:
    """Load all attorneys from JSON. Returns empty list if file missing."""
    if not ATTORNEYS_FILE.exists():
        return []
    try:
        data = json.loads(ATTORNEYS_FILE.read_text())
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_attorneys(attorneys: list[dict]) -> None:
    """Save the full attorney list to JSON."""
    _ensure_dir()
    ATTORNEYS_FILE.write_text(json.dumps(attorneys, indent=2, ensure_ascii=False))


def get_attorney_by_id(attorney_id: str) -> dict | None:
    """Look up a single attorney by ID. Returns None if not found."""
    for a in load_attorneys():
        if a.get("id") == attorney_id:
            return a
    return None


def new_attorney_id() -> str:
    """Generate a short unique ID for a new attorney."""
    return str(uuid.uuid4())[:8]
