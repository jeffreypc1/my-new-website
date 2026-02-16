"""Draft persistence for document translations.

Drafts are stored as JSON files in data/drafts/.  Each draft captures the
client name, source/target language, original paragraphs, translated
paragraphs, and staff edits so work can be resumed across sessions.
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
    client_name: str,
    source_filename: str,
    source_lang: str,
    target_lang: str,
    paragraphs: list[dict],
    notes: str = "",
    include_original: bool = True,
    export_format: str = "Translation only",
    certificate_type: str = "None",
    translator_info: dict | None = None,
    client_pronoun: str = "they",
    show_disclaimer: bool = True,
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
        "client_name": client_name,
        "source_filename": source_filename,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "paragraphs": paragraphs,
        "notes": notes,
        "include_original": include_original,
        "export_format": export_format,
        "certificate_type": certificate_type,
        "translator_info": translator_info or {"name": "", "address": "", "phone": ""},
        "client_pronoun": client_pronoun,
        "show_disclaimer": show_disclaimer,
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
                    "client_name": d.get("client_name", "Unnamed"),
                    "source_filename": d.get("source_filename", ""),
                    "source_lang": d.get("source_lang", ""),
                    "target_lang": d.get("target_lang", ""),
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
