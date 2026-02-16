"""Timeline event data model, approximate date parser, and JSON persistence.

Handles the full lifecycle of timeline events: creation, parsing of
approximate dates that asylum attorneys commonly use, chronological sorting,
and persistent storage as JSON files.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "timelines"

import sys as _sys
_sys.path.insert(0, str(BASE_DIR.parent))
from shared.config_store import get_config_value

# ── Category definitions ─────────────────────────────────────────────────────

_DEFAULT_EVENT_CATEGORIES: dict[str, str] = {
    "Persecution": "#dc3545",   # red — incidents of harm, threats, discrimination
    "Travel": "#0d6efd",        # blue — departure, transit countries, arrival in US
    "Legal": "#198754",         # green — applications filed, RFEs, hearings, decisions
    "Personal": "#6c757d",      # gray — marriage, children, employment, education
    "Medical": "#6f42c1",       # purple — injuries, treatment, psychological evaluations
}

_DEFAULT_CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "Persecution": "Incidents of harm, threats, discrimination",
    "Travel": "Departure, transit countries, arrival in US",
    "Legal": "Applications filed, RFEs, hearings, decisions",
    "Personal": "Marriage, children, employment, education",
    "Medical": "Injuries, treatment, psychological evaluations",
}

# ── Config-aware loading (JSON override with hardcoded fallback) ─────────────
EVENT_CATEGORIES: dict[str, str] = get_config_value("timeline-builder", "event_categories", _DEFAULT_EVENT_CATEGORIES)
CATEGORY_DESCRIPTIONS: dict[str, str] = get_config_value("timeline-builder", "category_descriptions", _DEFAULT_CATEGORY_DESCRIPTIONS)

# ── Data model ───────────────────────────────────────────────────────────────


@dataclass
class TimelineEvent:
    """A single event on a case timeline."""

    id: str
    title: str
    date_text: str                  # user's original input like "March 2019"
    parsed_date: str                # sortable ISO-ish key like "2019-03-00"
    category: str                   # key in EVENT_CATEGORIES
    description: str = ""
    end_date_text: str = ""         # optional, for date ranges

    @classmethod
    def create(
        cls,
        title: str,
        date_text: str,
        category: str,
        description: str = "",
        end_date_text: str = "",
    ) -> TimelineEvent:
        """Factory method that auto-generates id and parses the date."""
        return cls(
            id=uuid.uuid4().hex[:12],
            title=title,
            date_text=date_text,
            parsed_date=parse_approximate_date(date_text),
            category=category,
            description=description,
            end_date_text=end_date_text,
        )


# ── Approximate date parser ─────────────────────────────────────────────────

_MONTH_NAMES: dict[str, str] = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}

_SEASON_MAP: dict[str, str] = {
    "winter": "01",
    "spring": "04",
    "summer": "07",
    "fall": "10",
    "autumn": "10",
}

_QUALIFIER_MAP: dict[str, str] = {
    "early": "02",
    "beginning of": "01",
    "mid": "06",
    "middle of": "06",
    "late": "11",
    "end of": "12",
}


def parse_approximate_date(text: str) -> str:
    """Convert a human-friendly date string into a sortable key.

    Returns a string in the format ``YYYY-MM-DD`` where unknown month or day
    components are ``00``.  This keeps the value sortable while preserving
    the fact that precision is limited.

    Supported formats
    -----------------
    - ISO:       ``2019-03-15``           -> ``2019-03-15``
    - US:        ``03/15/2019``           -> ``2019-03-15``
    - Long:      ``March 15, 2019``       -> ``2019-03-15``
    - Month-Year:``March 2019``           -> ``2019-03-00``
    - Year only: ``2019``                 -> ``2019-00-00``
    - Season:    ``Summer 2017``          -> ``2017-07-00``
    - Qualifier: ``Early 2018``           -> ``2018-02-00``
    - Qualifier: ``Late 2019``            -> ``2019-11-00``
    - Range:     ``Between 2016 and 2018``-> ``2016-00-00`` (start date)
    - Approx:    ``Around March 2019``    -> ``2019-03-00``
    - Approx:    ``Approximately 2015``   -> ``2015-00-00``
    """
    cleaned = text.strip()
    if not cleaned:
        return "9999-99-99"  # sort unknowns to the end

    # Strip leading approximation qualifiers that don't affect the date
    cleaned = re.sub(
        r"^(around|approximately|approx\.?|circa|about|roughly)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # ── ISO date: YYYY-MM-DD ─────────────────────────────────────────────
    iso_match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", cleaned)
    if iso_match:
        y, m, d = iso_match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    # ── US date: MM/DD/YYYY ──────────────────────────────────────────────
    us_match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", cleaned)
    if us_match:
        m, d, y = us_match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"

    # ── "Month Day, Year" — e.g. "January 5, 2022" ──────────────────────
    long_match = re.match(
        r"^([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})$", cleaned
    )
    if long_match:
        month_str, day_str, year_str = long_match.groups()
        mm = _MONTH_NAMES.get(month_str.lower(), "00")
        return f"{year_str}-{mm}-{int(day_str):02d}"

    # ── "Day Month Year" — e.g. "5 January 2022" ────────────────────────
    dmy_match = re.match(
        r"^(\d{1,2})\s+([A-Za-z]+)\.?\s+(\d{4})$", cleaned
    )
    if dmy_match:
        day_str, month_str, year_str = dmy_match.groups()
        mm = _MONTH_NAMES.get(month_str.lower(), "00")
        return f"{year_str}-{mm}-{int(day_str):02d}"

    # ── "Between YEAR and YEAR" — use start date ─────────────────────────
    between_match = re.match(
        r"^between\s+(\d{4})\s+and\s+(\d{4})$", cleaned, re.IGNORECASE
    )
    if between_match:
        start_year = between_match.group(1)
        return f"{start_year}-00-00"

    # ── "Between Month YEAR and Month YEAR" ──────────────────────────────
    between_month_match = re.match(
        r"^between\s+([A-Za-z]+)\s+(\d{4})\s+and\s+([A-Za-z]+)\s+(\d{4})$",
        cleaned,
        re.IGNORECASE,
    )
    if between_month_match:
        month_str, year_str = between_month_match.group(1), between_month_match.group(2)
        mm = _MONTH_NAMES.get(month_str.lower(), "00")
        return f"{year_str}-{mm}-00"

    # ── Season + Year — e.g. "Summer 2020" ───────────────────────────────
    season_match = re.match(r"^([A-Za-z]+)\s+(\d{4})$", cleaned)
    if season_match:
        qualifier, year_str = season_match.groups()
        q_lower = qualifier.lower()
        # Check season first
        if q_lower in _SEASON_MAP:
            return f"{year_str}-{_SEASON_MAP[q_lower]}-00"
        # Then qualifier (Early, Mid, Late)
        if q_lower in _QUALIFIER_MAP:
            return f"{year_str}-{_QUALIFIER_MAP[q_lower]}-00"
        # Then month name (March 2019)
        if q_lower in _MONTH_NAMES:
            return f"{year_str}-{_MONTH_NAMES[q_lower]}-00"

    # ── Multi-word qualifier + Year — e.g. "Beginning of 2018" ───────────
    multi_qual_match = re.match(
        r"^(beginning of|middle of|end of)\s+(\d{4})$", cleaned, re.IGNORECASE
    )
    if multi_qual_match:
        qualifier, year_str = multi_qual_match.groups()
        mm = _QUALIFIER_MAP.get(qualifier.lower(), "00")
        return f"{year_str}-{mm}-00"

    # ── Bare year: "2018" ────────────────────────────────────────────────
    year_only = re.match(r"^(\d{4})$", cleaned)
    if year_only:
        return f"{cleaned}-00-00"

    # ── Fallback: return a key that sorts at the end, preserving data ────
    return "9999-99-99"


def parsed_date_to_display(parsed: str) -> str:
    """Convert a parsed date key back to a human-readable form for sorting display.

    Used only when we need a secondary display string; the original date_text
    is always preferred for display.
    """
    if parsed == "9999-99-99":
        return "Unknown date"
    parts = parsed.split("-")
    if len(parts) != 3:
        return parsed
    y, m, d = parts
    if m == "00":
        return y
    month_names = [
        "", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    mi = int(m)
    month_label = month_names[mi] if 1 <= mi <= 12 else m
    if d == "00":
        return f"{month_label} {y}"
    return f"{month_label} {int(d)}, {y}"


# ── Timeline persistence ────────────────────────────────────────────────────


def _ensure_data_dir() -> None:
    """Create the data directory if it does not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def new_timeline_id() -> str:
    """Generate a fresh unique timeline identifier."""
    return uuid.uuid4().hex[:12]


def _timeline_path(timeline_id: str) -> Path:
    """Return the JSON file path for a given timeline."""
    return DATA_DIR / f"{timeline_id}.json"


def save_timeline(timeline: dict) -> None:
    """Persist a timeline dict to its JSON file.

    Sets ``updated_at`` to the current timestamp automatically.
    """
    _ensure_data_dir()
    timeline["updated_at"] = datetime.now().isoformat()
    if "created_at" not in timeline:
        timeline["created_at"] = timeline["updated_at"]
    path = _timeline_path(timeline["id"])
    with open(path, "w") as f:
        json.dump(timeline, f, indent=2, default=str)


def load_timeline(timeline_id: str) -> dict | None:
    """Load a timeline dict from disk, or return None if not found."""
    path = _timeline_path(timeline_id)
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return None


def list_timelines() -> list[dict]:
    """Return summary info for every saved timeline.

    Each item contains: id, case_name, client_name, event_count, updated_at.
    Sorted by most recently updated first.
    """
    _ensure_data_dir()
    summaries: list[dict] = []
    for p in DATA_DIR.glob("*.json"):
        try:
            with open(p) as f:
                data = json.load(f)
            summaries.append({
                "id": data.get("id", p.stem),
                "case_name": data.get("case_name", ""),
                "client_name": data.get("client_name", ""),
                "event_count": len(data.get("events", [])),
                "updated_at": data.get("updated_at", ""),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    summaries.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
    return summaries


def delete_timeline(timeline_id: str) -> bool:
    """Delete a timeline JSON file. Returns True if the file existed."""
    path = _timeline_path(timeline_id)
    if path.exists():
        path.unlink()
        return True
    return False


def new_timeline(case_name: str = "", client_name: str = "") -> dict:
    """Create a fresh timeline dict (not yet saved to disk)."""
    now = datetime.now().isoformat()
    return {
        "id": new_timeline_id(),
        "case_name": case_name,
        "client_name": client_name,
        "events": [],
        "created_at": now,
        "updated_at": now,
    }


def add_event(timeline: dict, event: TimelineEvent) -> dict:
    """Append an event to a timeline, re-sort, and save. Returns updated timeline."""
    timeline["events"].append(asdict(event))
    _sort_events(timeline)
    save_timeline(timeline)
    return timeline


def update_event(timeline: dict, event_id: str, updates: dict) -> dict:
    """Update fields on an existing event, re-sort, and save."""
    for ev in timeline["events"]:
        if ev.get("id") == event_id:
            for k, v in updates.items():
                ev[k] = v
            # Re-parse date if date_text changed
            if "date_text" in updates:
                ev["parsed_date"] = parse_approximate_date(updates["date_text"])
            break
    _sort_events(timeline)
    save_timeline(timeline)
    return timeline


def delete_event(timeline: dict, event_id: str) -> dict:
    """Remove an event by id, and save. Returns updated timeline."""
    timeline["events"] = [e for e in timeline["events"] if e.get("id") != event_id]
    save_timeline(timeline)
    return timeline


def _sort_events(timeline: dict) -> None:
    """Sort the events list in-place by parsed_date."""
    timeline["events"].sort(key=lambda e: e.get("parsed_date", "9999-99-99"))
