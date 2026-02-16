"""Checklist definitions and case persistence for the Case Checklist tool.

Provides pre-built checklists for common immigration case types, along with
functions to load and save case data as JSON files.

Part of the O'Brien Immigration Law tool suite.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path

# Storage directory for case JSON files
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "cases"
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ChecklistItem:
    """A single item in a case checklist."""

    label: str
    required: bool = True
    deadline_days: int | None = None  # Days from case creation until deadline
    category: str = "General"  # Filing, Evidence, Preparation, Administrative
    completed: bool = False
    completed_date: str | None = None
    notes: str = ""


# ---------------------------------------------------------------------------
# Pre-built checklists by case type
# ---------------------------------------------------------------------------

CASE_TYPE_CHECKLISTS: dict[str, list[ChecklistItem]] = {
    "Asylum": [
        ChecklistItem(
            label="I-589 filed",
            required=True,
            deadline_days=365,  # One-year filing deadline
            category="Filing",
        ),
        ChecklistItem(
            label="Declaration drafted",
            required=True,
            deadline_days=None,
            category="Evidence",
        ),
        ChecklistItem(
            label="Country conditions gathered",
            required=True,
            deadline_days=None,
            category="Evidence",
        ),
        ChecklistItem(
            label="Brief written",
            required=True,
            deadline_days=None,
            category="Preparation",
        ),
        ChecklistItem(
            label="Evidence indexed",
            required=True,
            deadline_days=None,
            category="Evidence",
        ),
        ChecklistItem(
            label="Biometrics completed",
            required=True,
            deadline_days=None,
            category="Administrative",
        ),
        ChecklistItem(
            label="Interview/hearing prep",
            required=True,
            deadline_days=None,
            category="Preparation",
        ),
    ],
    "Family-Based": [
        ChecklistItem(
            label="I-130 filed",
            required=True,
            deadline_days=None,
            category="Filing",
        ),
        ChecklistItem(
            label="I-485 filed",
            required=True,
            deadline_days=None,
            category="Filing",
        ),
        ChecklistItem(
            label="I-765 filed",
            required=True,
            deadline_days=None,
            category="Filing",
        ),
        ChecklistItem(
            label="I-131 filed",
            required=False,
            deadline_days=None,
            category="Filing",
        ),
        ChecklistItem(
            label="Civil documents gathered",
            required=True,
            deadline_days=None,
            category="Evidence",
        ),
        ChecklistItem(
            label="Translations certified",
            required=True,
            deadline_days=None,
            category="Evidence",
        ),
        ChecklistItem(
            label="Biometrics completed",
            required=True,
            deadline_days=None,
            category="Administrative",
        ),
    ],
    "VAWA": [
        ChecklistItem(
            label="I-360 filed",
            required=True,
            deadline_days=None,
            category="Filing",
        ),
        ChecklistItem(
            label="Personal declaration",
            required=True,
            deadline_days=None,
            category="Evidence",
        ),
        ChecklistItem(
            label="Evidence of abuse gathered",
            required=True,
            deadline_days=None,
            category="Evidence",
        ),
        ChecklistItem(
            label="Evidence of good faith marriage",
            required=True,
            deadline_days=None,
            category="Evidence",
        ),
    ],
}


# ---------------------------------------------------------------------------
# Case persistence stubs
# ---------------------------------------------------------------------------

def _case_path(case_id: str) -> Path:
    """Return the JSON file path for a given case ID."""
    return DATA_DIR / f"{case_id}.json"


def load_cases() -> list[dict]:
    """Load all saved cases from the data directory.

    Returns:
        List of case dicts, each containing case metadata and checklist items.

    TODO: Add pagination for large numbers of cases.
    TODO: Add sorting by deadline urgency.
    TODO: Add caching to avoid re-reading files on every request.
    """
    cases: list[dict] = []
    if not DATA_DIR.exists():
        return cases

    for path in sorted(DATA_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text())
            cases.append(data)
        except (json.JSONDecodeError, OSError):
            continue

    return cases


def load_case(case_id: str) -> dict | None:
    """Load a single case by ID.

    Args:
        case_id: The unique case identifier.

    Returns:
        The case dict, or None if not found.
    """
    path = _case_path(case_id)
    if not path.exists():
        return None

    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def save_case(case_data: dict) -> None:
    """Save a case to the data directory as a JSON file.

    Args:
        case_data: Dict containing case metadata and checklist items.
            Must include a "case_id" key.

    TODO: Add validation of case_data structure.
    TODO: Add backup/versioning of case files.
    """
    case_id = case_data.get("case_id", "")
    if not case_id:
        raise ValueError("case_data must include a 'case_id' key.")

    path = _case_path(case_id)
    path.write_text(json.dumps(case_data, indent=2, default=str))


def create_case(
    case_id: str,
    client_name: str,
    case_type: str,
    a_number: str = "",
) -> dict:
    """Create a new case with an auto-populated checklist.

    Args:
        case_id: Unique identifier for the case.
        client_name: Client's full name.
        case_type: One of the keys in CASE_TYPE_CHECKLISTS.
        a_number: Alien Registration Number, if available.

    Returns:
        The newly created case dict.

    TODO: Validate case_type against CASE_TYPE_CHECKLISTS.
    TODO: Generate case_id automatically if not provided.
    """
    template_items = CASE_TYPE_CHECKLISTS.get(case_type, [])
    today = date.today().isoformat()

    checklist = [asdict(item) for item in template_items]

    # Compute absolute deadlines from relative deadline_days
    for item in checklist:
        if item.get("deadline_days") is not None:
            deadline = date.today()
            deadline = deadline.replace(
                year=deadline.year + (item["deadline_days"] // 365),
            )
            remaining_days = item["deadline_days"] % 365
            # Simple offset — production code should use timedelta
            item["deadline_date"] = (
                datetime.strptime(today, "%Y-%m-%d").date().__add__(
                    __import__("datetime").timedelta(days=item["deadline_days"])
                )
            ).isoformat()

    case_data = {
        "case_id": case_id,
        "client_name": client_name,
        "case_type": case_type,
        "a_number": a_number,
        "status": "Active",
        "created_date": today,
        "updated_date": today,
        "checklist": checklist,
    }

    save_case(case_data)
    return case_data


def update_item(case_id: str, item_index: int, updates: dict) -> dict | None:
    """Update a specific checklist item within a case.

    Args:
        case_id: The case identifier.
        item_index: Zero-based index of the checklist item.
        updates: Dict of fields to update (e.g. {"completed": True}).

    Returns:
        The updated case dict, or None if case/item not found.

    TODO: Add validation of update fields.
    TODO: Auto-set completed_date when marking an item as completed.
    """
    case_data = load_case(case_id)
    if case_data is None:
        return None

    checklist = case_data.get("checklist", [])
    if item_index < 0 or item_index >= len(checklist):
        return None

    checklist[item_index].update(updates)

    # Auto-set completed_date
    if updates.get("completed") and not checklist[item_index].get("completed_date"):
        checklist[item_index]["completed_date"] = date.today().isoformat()

    case_data["updated_date"] = date.today().isoformat()
    save_case(case_data)
    return case_data
