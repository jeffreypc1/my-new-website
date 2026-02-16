"""Event management and storage for Timeline Builder."""

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "timelines"

# ---------------------------------------------------------------------------
# Category definitions with display colors
# ---------------------------------------------------------------------------

EVENT_CATEGORIES: dict[str, str] = {
    "Persecution": "#e74c3c",   # red
    "Travel": "#3498db",        # blue
    "Legal Filing": "#2ecc71",  # green
    "Personal": "#95a5a6",      # gray
    "Medical": "#9b59b6",       # purple
}

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class TimelineEvent:
    """A single event on a case timeline."""

    date_text: str                          # original human-entered date ("March 2019")
    date_sortable: str                      # ISO-ish sortable key ("2019-03-00")
    description: str
    category: str                           # key in EVENT_CATEGORIES
    location: str = ""
    evidence_ref: str = ""                  # e.g. "Exhibit A-3"
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])


# ---------------------------------------------------------------------------
# Approximate-date parser
# ---------------------------------------------------------------------------

_SEASON_MAP: dict[str, str] = {
    "winter": "01",
    "spring": "04",
    "summer": "07",
    "fall": "10",
    "autumn": "10",
    "early": "02",
    "mid": "06",
    "late": "11",
}

_MONTH_NAMES: dict[str, str] = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}


def parse_approximate_date(text: str) -> str:
    """Convert a human-friendly date string into a sortable key.

    Supported formats:
      - "2018"            -> "2018-00-00"
      - "March 2019"      -> "2019-03-00"
      - "Summer 2020"     -> "2020-07-00"
      - "Early 2020"      -> "2020-02-00"
      - "03/15/2021"      -> "2021-03-15"
      - "2021-03-15"      -> "2021-03-15"
      - "January 5, 2022" -> "2022-01-05"
    """
    cleaned = text.strip()

    # Try ISO date first (YYYY-MM-DD)
    iso_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", cleaned)
    if iso_match:
        return cleaned

    # US date format MM/DD/YYYY
    us_match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", cleaned)
    if us_match:
        m, d, y = us_match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    # "Month Day, Year" — e.g. "January 5, 2022"
    long_match = re.match(
        r"^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})$", cleaned
    )
    if long_match:
        month_str, day_str, year_str = long_match.groups()
        mm = _MONTH_NAMES.get(month_str.lower(), "00")
        return f"{year_str}-{mm}-{int(day_str):02d}"

    # "Month Year" — e.g. "March 2019"
    month_year = re.match(r"^([A-Za-z]+)\s+(\d{4})$", cleaned)
    if month_year:
        month_str, year_str = month_year.groups()
        mm = _MONTH_NAMES.get(month_str.lower())
        if mm:
            return f"{year_str}-{mm}-00"

    # Season / qualifier + year — e.g. "Summer 2020", "Early 2020"
    season_match = re.match(r"^([A-Za-z]+)\s+(\d{4})$", cleaned)
    if season_match:
        qualifier, year_str = season_match.groups()
        mm = _SEASON_MAP.get(qualifier.lower())
        if mm:
            return f"{year_str}-{mm}-00"

    # Bare year — e.g. "2018"
    year_only = re.match(r"^(\d{4})$", cleaned)
    if year_only:
        return f"{cleaned}-00-00"

    # Fallback: return as-is so we don't lose data
    return cleaned


# ---------------------------------------------------------------------------
# Timeline persistence (JSON files in data/timelines/)
# ---------------------------------------------------------------------------


def _timeline_path(timeline_id: str) -> Path:
    """Return the JSON file path for a given timeline."""
    return DATA_DIR / f"{timeline_id}.json"


def load_timeline(timeline_id: str) -> dict:
    """Load a timeline dict from disk.

    Returns a dict with keys: id, name, client, events (list of event dicts).
    """
    path = _timeline_path(timeline_id)
    if not path.exists():
        return {"id": timeline_id, "name": "", "client": "", "events": []}
    with open(path) as f:
        return json.load(f)


def save_timeline(timeline: dict) -> None:
    """Persist a timeline dict to its JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = _timeline_path(timeline["id"])
    with open(path, "w") as f:
        json.dump(timeline, f, indent=2, default=str)


def list_timelines() -> list[dict]:
    """Return summary info for every saved timeline.

    Each item contains: id, name, client, event_count.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    summaries: list[dict] = []
    for p in sorted(DATA_DIR.glob("*.json")):
        try:
            with open(p) as f:
                data = json.load(f)
            summaries.append({
                "id": data.get("id", p.stem),
                "name": data.get("name", ""),
                "client": data.get("client", ""),
                "event_count": len(data.get("events", [])),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return summaries


def add_event(timeline_id: str, event: TimelineEvent) -> dict:
    """Append an event to a timeline and save.  Returns updated timeline."""
    timeline = load_timeline(timeline_id)
    timeline["events"].append(asdict(event))
    sort_events(timeline)
    save_timeline(timeline)
    return timeline


def sort_events(timeline: dict) -> None:
    """Sort the events list in-place by date_sortable."""
    timeline["events"].sort(key=lambda e: e.get("date_sortable", ""))
