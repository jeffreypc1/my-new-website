"""Checklist templates and case persistence for the Case Checklist tool.

Provides comprehensive, real-world checklist templates for common immigration
case types, along with CRUD functions to create, read, update, and delete
cases persisted as JSON files.

Part of the O'Brien Immigration Law tool suite.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

# ── Storage ──────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "cases"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ── Data models ──────────────────────────────────────────────────────────────


@dataclass
class ChecklistItem:
    """A single actionable item in a case checklist."""

    id: str
    title: str
    category: str  # Filing, Evidence, Preparation, Administrative
    is_completed: bool = False
    completed_date: str | None = None
    deadline: str | None = None  # ISO date string, e.g. "2026-06-15"
    notes: str = ""


@dataclass
class Case:
    """An immigration case with its associated checklist."""

    id: str
    client_name: str
    a_number: str
    case_type: str
    attorney: str
    created_at: str
    updated_at: str
    items: list[dict[str, Any]]
    status: str = "Active"  # Active or Completed


# ── Templates ────────────────────────────────────────────────────────────────

CASE_TYPES: list[str] = [
    "Asylum (I-589)",
    "Family-Based (I-130/I-485)",
    "VAWA (I-360)",
    "U-Visa (I-918)",
    "Cancellation of Removal",
]

_TEMPLATES: dict[str, list[dict[str, str]]] = {
    "Asylum (I-589)": [
        # Filing
        {"title": "I-589 application completed", "category": "Filing"},
        {"title": "Declaration drafted", "category": "Filing"},
        {"title": "Country condition reports gathered", "category": "Filing"},
        {"title": "Supporting evidence compiled", "category": "Filing"},
        {"title": "Brief / legal memo written", "category": "Filing"},
        {"title": "Exhibit bundle compiled and indexed", "category": "Filing"},
        {"title": "Biometrics completed", "category": "Filing"},
        # Preparation
        {"title": "Client interview completed", "category": "Preparation"},
        {"title": "Interpreter arranged (if needed)", "category": "Preparation"},
        {"title": "Psychological evaluation scheduled", "category": "Preparation"},
        {"title": "Expert declaration requested", "category": "Preparation"},
        {"title": "Witness declarations gathered", "category": "Preparation"},
        # Deadlines / Administrative
        {"title": "One-year filing deadline tracked", "category": "Administrative"},
        {"title": "Hearing date calendared", "category": "Administrative"},
        {"title": "Filing deadline for brief tracked", "category": "Administrative"},
    ],
    "Family-Based (I-130/I-485)": [
        # Filing
        {"title": "I-130 petition filed", "category": "Filing"},
        {"title": "I-485 adjustment application filed", "category": "Filing"},
        {"title": "I-765 (EAD) application filed", "category": "Filing"},
        {"title": "I-131 (Advance Parole) filed", "category": "Filing"},
        {"title": "I-864 Affidavit of Support completed", "category": "Filing"},
        # Evidence
        {"title": "Civil documents gathered (birth/marriage certificates)", "category": "Evidence"},
        {"title": "Translations certified", "category": "Evidence"},
        {"title": "Passport-style photos taken", "category": "Evidence"},
        {"title": "Financial documents for I-864 gathered", "category": "Evidence"},
        {"title": "Evidence of bona fide relationship compiled", "category": "Evidence"},
        # Administrative
        {"title": "Biometrics appointment completed", "category": "Administrative"},
        {"title": "Interview preparation completed", "category": "Administrative"},
        {"title": "Medical exam (I-693) completed", "category": "Administrative"},
    ],
    "VAWA (I-360)": [
        # Filing
        {"title": "I-360 self-petition filed", "category": "Filing"},
        {"title": "Personal declaration drafted", "category": "Filing"},
        # Evidence
        {"title": "Evidence of qualifying relationship", "category": "Evidence"},
        {"title": "Evidence of abuse documented", "category": "Evidence"},
        {"title": "Evidence of good faith marriage", "category": "Evidence"},
        {"title": "Evidence of good moral character", "category": "Evidence"},
        {"title": "Evidence of residence in the U.S.", "category": "Evidence"},
        # Preparation
        {"title": "Client safety plan reviewed", "category": "Preparation"},
        {"title": "Psychological evaluation scheduled", "category": "Preparation"},
    ],
    "U-Visa (I-918)": [
        # Filing
        {"title": "I-918 petition filed", "category": "Filing"},
        {"title": "I-918 Supplement B (law enforcement certification) obtained", "category": "Filing"},
        # Evidence
        {"title": "Personal declaration drafted", "category": "Evidence"},
        {"title": "Evidence of qualifying crime documented", "category": "Evidence"},
        {"title": "Evidence of substantial physical/mental harm", "category": "Evidence"},
        {"title": "Evidence of helpfulness to law enforcement", "category": "Evidence"},
        # Preparation
        {"title": "Client interview completed", "category": "Preparation"},
        {"title": "Law enforcement agency contacted for certification", "category": "Preparation"},
        # Administrative
        {"title": "Biometrics completed", "category": "Administrative"},
        {"title": "Waiver of inadmissibility filed (if needed)", "category": "Administrative"},
    ],
    "Cancellation of Removal": [
        # Filing
        {"title": "EOIR-42B application filed", "category": "Filing"},
        {"title": "Declaration drafted", "category": "Filing"},
        {"title": "Legal brief written", "category": "Filing"},
        # Evidence
        {"title": "10 years continuous physical presence documented", "category": "Evidence"},
        {"title": "Good moral character evidence compiled", "category": "Evidence"},
        {"title": "Exceptional and extremely unusual hardship evidence", "category": "Evidence"},
        {"title": "Country condition evidence (if applicable)", "category": "Evidence"},
        # Preparation
        {"title": "Client testimony preparation", "category": "Preparation"},
        {"title": "Witness testimony prepared", "category": "Preparation"},
        # Administrative
        {"title": "Hearing date calendared", "category": "Administrative"},
        {"title": "Filing deadlines tracked", "category": "Administrative"},
    ],
}


def _make_item_id() -> str:
    """Generate a short unique item ID."""
    return uuid.uuid4().hex[:12]


def _new_case_id() -> str:
    """Generate a unique case ID."""
    return uuid.uuid4().hex[:16]


def _items_from_template(case_type: str) -> list[dict[str, Any]]:
    """Build checklist item dicts from a case-type template."""
    template = _TEMPLATES.get(case_type, [])
    items: list[dict[str, Any]] = []
    for entry in template:
        item = ChecklistItem(
            id=_make_item_id(),
            title=entry["title"],
            category=entry["category"],
        )
        items.append(asdict(item))
    return items


# ── Persistence helpers ──────────────────────────────────────────────────────


def _case_path(case_id: str) -> Path:
    """Return the JSON file path for a given case ID."""
    # Sanitize to prevent path traversal
    safe_id = "".join(c for c in case_id if c.isalnum() or c in "-_")
    return DATA_DIR / f"{safe_id}.json"


# ── CRUD functions ───────────────────────────────────────────────────────────


def create_case(
    client_name: str,
    case_type: str,
    a_number: str = "",
    attorney: str = "",
) -> dict[str, Any]:
    """Create a new case auto-populated from a case-type template.

    Args:
        client_name: Full legal name of the client.
        case_type: One of the keys in CASE_TYPES.
        a_number: Alien registration number (optional).
        attorney: Name of the assigned attorney.

    Returns:
        The newly-created case dict, already saved to disk.
    """
    now = datetime.now().isoformat(timespec="seconds")
    case_id = _new_case_id()

    case_data: dict[str, Any] = {
        "id": case_id,
        "client_name": client_name,
        "a_number": a_number,
        "case_type": case_type,
        "attorney": attorney,
        "created_at": now,
        "updated_at": now,
        "status": "Active",
        "items": _items_from_template(case_type),
    }

    save_case(case_data)
    return case_data


def save_case(case_data: dict[str, Any]) -> None:
    """Persist a case dict to disk as JSON.

    Args:
        case_data: Must contain an ``id`` key.
    """
    case_id = case_data.get("id", "")
    if not case_id:
        raise ValueError("case_data must include an 'id' key.")
    case_data["updated_at"] = datetime.now().isoformat(timespec="seconds")
    path = _case_path(case_id)
    path.write_text(json.dumps(case_data, indent=2, default=str))


def load_case(case_id: str) -> dict[str, Any] | None:
    """Load a single case by its ID.

    Returns:
        The case dict, or ``None`` if not found or unreadable.
    """
    path = _case_path(case_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def list_cases() -> list[dict[str, Any]]:
    """Return all saved cases, sorted by most-recently updated first."""
    cases: list[dict[str, Any]] = []
    if not DATA_DIR.exists():
        return cases
    for path in DATA_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text())
            cases.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    # Sort by updated_at descending
    cases.sort(key=lambda c: c.get("updated_at", ""), reverse=True)
    return cases


def delete_case(case_id: str) -> bool:
    """Delete a case from disk.

    Returns:
        ``True`` if the file was deleted, ``False`` if it didn't exist.
    """
    path = _case_path(case_id)
    if path.exists():
        path.unlink()
        return True
    return False


def update_item(case_id: str, item_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    """Update a single checklist item within a case.

    Args:
        case_id: The case identifier.
        item_id: The unique item ID within the case's checklist.
        updates: Dict of fields to update, e.g.
            ``{"is_completed": True, "deadline": "2026-06-01", "notes": "..."}``.

    Returns:
        The updated case dict, or ``None`` if the case or item wasn't found.
    """
    case_data = load_case(case_id)
    if case_data is None:
        return None

    items = case_data.get("items", [])
    target = None
    for item in items:
        if item.get("id") == item_id:
            target = item
            break

    if target is None:
        return None

    # Apply updates
    for key, value in updates.items():
        if key in ("is_completed", "deadline", "notes"):
            target[key] = value

    # Auto-set completed_date when completing an item
    if updates.get("is_completed") is True:
        target["completed_date"] = date.today().isoformat()
    elif updates.get("is_completed") is False:
        target["completed_date"] = None

    save_case(case_data)
    return case_data


def add_custom_item(
    case_id: str,
    title: str,
    category: str,
    deadline: str | None = None,
) -> dict[str, Any] | None:
    """Add a custom checklist item to an existing case.

    Args:
        case_id: The case identifier.
        title: Label for the new item.
        category: One of Filing, Evidence, Preparation, Administrative.
        deadline: Optional ISO date string for the deadline.

    Returns:
        The updated case dict, or ``None`` if the case wasn't found.
    """
    case_data = load_case(case_id)
    if case_data is None:
        return None

    new_item = ChecklistItem(
        id=_make_item_id(),
        title=title,
        category=category,
        deadline=deadline,
    )
    case_data["items"].append(asdict(new_item))
    save_case(case_data)
    return case_data


def get_case_progress(case_data: dict[str, Any]) -> dict[str, Any]:
    """Compute completion progress for a case.

    Returns a dict with ``total``, ``completed``, and ``pct`` keys,
    plus a ``by_category`` breakdown.
    """
    items = case_data.get("items", [])
    total = len(items)
    completed = sum(1 for item in items if item.get("is_completed"))
    pct = round((completed / total) * 100) if total > 0 else 0

    by_category: dict[str, dict[str, int]] = {}
    for item in items:
        cat = item.get("category", "General")
        if cat not in by_category:
            by_category[cat] = {"total": 0, "completed": 0}
        by_category[cat]["total"] += 1
        if item.get("is_completed"):
            by_category[cat]["completed"] += 1

    return {
        "total": total,
        "completed": completed,
        "pct": pct,
        "by_category": by_category,
    }


def get_deadline_status(deadline_str: str | None) -> dict[str, Any]:
    """Evaluate a deadline relative to today.

    Returns:
        A dict with ``days_remaining``, ``label``, and ``urgency``
        (one of ``overdue``, ``due_soon``, ``on_track``, or ``none``).
    """
    if not deadline_str:
        return {"days_remaining": None, "label": "", "urgency": "none"}

    try:
        dl = datetime.strptime(deadline_str, "%Y-%m-%d").date()
    except ValueError:
        return {"days_remaining": None, "label": "", "urgency": "none"}

    today = date.today()
    days_remaining = (dl - today).days

    if days_remaining < 0:
        return {
            "days_remaining": days_remaining,
            "label": f"OVERDUE by {abs(days_remaining)} day{'s' if abs(days_remaining) != 1 else ''}",
            "urgency": "overdue",
        }
    elif days_remaining <= 7:
        return {
            "days_remaining": days_remaining,
            "label": f"Due in {days_remaining} day{'s' if days_remaining != 1 else ''}",
            "urgency": "due_soon",
        }
    else:
        return {
            "days_remaining": days_remaining,
            "label": f"Due in {days_remaining} days",
            "urgency": "on_track",
        }
