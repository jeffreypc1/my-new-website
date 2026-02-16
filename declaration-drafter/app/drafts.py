"""Draft persistence for declaration drafts.

Drafts are stored as JSON files in data/drafts/.  Each draft captures the
declaration type, declarant info, and all answers so work can be resumed
across sessions.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "drafts"


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def new_draft_id() -> str:
    return str(uuid.uuid4())[:8]


def save_draft(
    draft_id: str,
    declaration_type: str,
    declarant: dict,
    answers: dict[str, str],
) -> dict:
    """Save or update a draft.  Returns the saved draft dict."""
    _ensure_dir()
    path = DATA_DIR / f"{draft_id}.json"

    now = datetime.now().isoformat()
    created_at = now
    if path.exists():
        try:
            existing = json.loads(path.read_text())
            created_at = existing.get("created_at", now)
        except Exception:
            pass

    draft = {
        "id": draft_id,
        "declaration_type": declaration_type,
        "declarant": declarant,
        "answers": {k: v for k, v in answers.items() if v.strip()},
        "created_at": created_at,
        "updated_at": now,
    }
    path.write_text(json.dumps(draft, indent=2))
    return draft


def load_draft(draft_id: str) -> dict | None:
    """Load a draft by ID.  Returns None if not found."""
    path = DATA_DIR / f"{draft_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def list_drafts() -> list[dict]:
    """Return summary info for all saved drafts, newest first."""
    _ensure_dir()
    drafts = []
    for p in DATA_DIR.glob("*.json"):
        try:
            d = json.loads(p.read_text())
            drafts.append(
                {
                    "id": d["id"],
                    "declaration_type": d.get("declaration_type", ""),
                    "declarant_name": d.get("declarant", {}).get("name", "Unnamed"),
                    "updated_at": d.get("updated_at", ""),
                    "created_at": d.get("created_at", ""),
                }
            )
        except Exception:
            continue
    drafts.sort(key=lambda d: d["updated_at"], reverse=True)
    return drafts


def delete_draft(draft_id: str) -> bool:
    """Delete a draft.  Returns True if the file existed."""
    path = DATA_DIR / f"{draft_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False
