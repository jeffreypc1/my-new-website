"""Office preparer management — JSON-backed CRUD.

Stores preparer info at data/config/preparers.json. Used by the
Forms Assistant to auto-fill preparer fields on uploaded PDF forms.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "data" / "config"
PREPARERS_FILE = CONFIG_DIR / "preparers.json"


def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_preparers() -> list[dict]:
    """Load all preparers from JSON. Returns empty list if file missing."""
    if not PREPARERS_FILE.exists():
        return []
    try:
        data = json.loads(PREPARERS_FILE.read_text())
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_preparers(preparers: list[dict]) -> None:
    """Save the full preparer list to JSON."""
    _ensure_dir()
    PREPARERS_FILE.write_text(json.dumps(preparers, indent=2, ensure_ascii=False))


def get_preparer_by_id(preparer_id: str) -> dict | None:
    """Look up a single preparer by ID. Returns None if not found."""
    for p in load_preparers():
        if p.get("id") == preparer_id:
            return p
    return None


def new_preparer_id() -> str:
    """Generate a short unique ID for a new preparer."""
    return str(uuid.uuid4())[:8]
