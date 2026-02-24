"""Draft persistence for the Forms Assistant tool.

Provides save/load/list/delete operations for form drafts stored as JSON
files on disk. Supports both single-form drafts (backward compatible) and
multi-form drafts where a single draft tracks data entry across several
related USCIS forms.

Part of the O'Brien Immigration Law tool suite.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "drafts"


def _ensure_dir() -> None:
    """Create the drafts directory if it does not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def new_draft_id() -> str:
    """Generate a short unique ID for a new draft."""
    return str(uuid.uuid4())[:8]


def save_form_draft(
    draft_id: str,
    form_id: str,
    form_data: dict[str, str],
    current_section: int,
    form_ids: list[str] | None = None,
) -> dict:
    """Save or update a form draft.

    Args:
        draft_id: Unique identifier for the draft.
        form_id: Primary form identifier (e.g. "I-589").
        form_data: Dict mapping field names to their current values.
        current_section: Index of the section the user is currently on.
        form_ids: Optional list of form IDs for multi-form drafts.
            When provided, the draft tracks data entry across multiple
            related forms (e.g. ["I-589", "I-765", "I-131"]).
            Defaults to None for single-form drafts.

    Returns:
        The saved draft dict.
    """
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

    # Derive a display name from form data
    name_field = ""
    for key in ("full_name", "applicant_name", "petitioner_name", "appellant_name"):
        if form_data.get(key, "").strip():
            name_field = form_data[key].strip()
            break

    draft: dict = {
        "id": draft_id,
        "form_id": form_id,
        "form_data": form_data,
        "current_section": current_section,
        "client_name": name_field or "Unnamed",
        "created_at": created_at,
        "updated_at": now,
    }

    if form_ids is not None:
        draft["form_ids"] = form_ids

    path.write_text(json.dumps(draft, indent=2))
    return draft


def load_form_draft(draft_id: str) -> dict | None:
    """Load a draft by ID.

    Args:
        draft_id: The unique draft identifier.

    Returns:
        The full draft dict (including ``form_ids`` if present), or None
        if the draft file does not exist or cannot be read.
    """
    path = DATA_DIR / f"{draft_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def list_form_drafts() -> list[dict]:
    """Return summary info for all saved form drafts, newest first.

    Each summary dict contains: id, form_id, client_name, updated_at,
    created_at, and form_ids (when the draft spans multiple forms).

    Returns:
        List of summary dicts sorted by updated_at descending.
    """
    _ensure_dir()
    drafts: list[dict] = []
    for p in DATA_DIR.glob("*.json"):
        try:
            d = json.loads(p.read_text())
            summary: dict = {
                "id": d["id"],
                "form_id": d.get("form_id", ""),
                "client_name": d.get("client_name", "Unnamed"),
                "updated_at": d.get("updated_at", ""),
                "created_at": d.get("created_at", ""),
            }
            if "form_ids" in d:
                summary["form_ids"] = d["form_ids"]
            drafts.append(summary)
        except Exception:
            continue
    drafts.sort(key=lambda d: d["updated_at"], reverse=True)
    return drafts


def delete_form_draft(draft_id: str) -> bool:
    """Delete a draft.

    Args:
        draft_id: The unique draft identifier.

    Returns:
        True if the file existed and was removed, False otherwise.
    """
    path = DATA_DIR / f"{draft_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False
