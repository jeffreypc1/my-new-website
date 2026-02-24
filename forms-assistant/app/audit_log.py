"""Append-only JSONL audit trail for the Forms Assistant.

Stores one JSON object per line in date-partitioned files under data/audit/.
Files are named YYYY-MM-DD.jsonl.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.schema import AuditEntry

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "audit"


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _file_for_date(date_str: str) -> Path:
    """Return the JSONL file path for a given YYYY-MM-DD date string."""
    return DATA_DIR / f"{date_str}.jsonl"


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def log_action(
    action: str,
    form_id: str = "",
    field_id: str = "",
    details: dict | None = None,
) -> AuditEntry:
    """Append an AuditEntry to today's JSONL file and return it."""
    _ensure_dir()

    entry = AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        action=action,
        form_id=form_id,
        field_id=field_id,
        details=details or {},
    )

    path = _file_for_date(_today_str())
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    return entry


def _read_entries_from_file(path: Path) -> list[AuditEntry]:
    """Read all AuditEntry objects from a single JSONL file."""
    entries: list[AuditEntry] = []
    if not path.exists():
        return entries
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            entries.append(AuditEntry.from_dict(data))
    return entries


def _sorted_audit_files(descending: bool = True) -> list[Path]:
    """Return audit JSONL files sorted by filename (date)."""
    _ensure_dir()
    files = sorted(DATA_DIR.glob("*.jsonl"), key=lambda p: p.stem, reverse=descending)
    return files


def get_recent_entries(limit: int = 50) -> list[AuditEntry]:
    """Read the most recent entries across all files, newest first."""
    results: list[AuditEntry] = []
    for path in _sorted_audit_files(descending=True):
        entries = _read_entries_from_file(path)
        # Reverse so newest entries in the file come first
        entries.reverse()
        results.extend(entries)
        if len(results) >= limit:
            break
    return results[:limit]


def get_entries_for_form(form_id: str, limit: int = 100) -> list[AuditEntry]:
    """Return entries matching a specific form_id, newest first."""
    results: list[AuditEntry] = []
    for path in _sorted_audit_files(descending=True):
        entries = _read_entries_from_file(path)
        entries.reverse()
        for entry in entries:
            if entry.form_id == form_id:
                results.append(entry)
                if len(results) >= limit:
                    return results
    return results


def get_entries_for_date(date_str: str) -> list[AuditEntry]:
    """Get all entries for a specific date (YYYY-MM-DD), newest first."""
    path = _file_for_date(date_str)
    entries = _read_entries_from_file(path)
    entries.reverse()
    return entries
