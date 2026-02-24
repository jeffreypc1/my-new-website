"""Mapping persistence, approval, rejection, and override operations.

Stores one JSON file per form in ``data/mappings/{form_id}.json``.
All mutating functions log to the audit trail via ``app.audit_log.log_action``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.audit_log import log_action
from app.schema import FieldMapping, MappingSet

MAPPINGS_DIR = Path(__file__).resolve().parent.parent / "data" / "mappings"


def _ensure_dir() -> None:
    """Create the mappings directory if it doesn't exist."""
    MAPPINGS_DIR.mkdir(parents=True, exist_ok=True)


def _path_for(form_id: str) -> Path:
    """Return the JSON file path for a given form_id."""
    return MAPPINGS_DIR / f"{form_id}.json"


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def save_mapping_set(ms: MappingSet) -> Path:
    """Persist a MappingSet to disk as ``{form_id}.json``.

    Args:
        ms: The mapping set to save.

    Returns:
        Path to the written JSON file.
    """
    _ensure_dir()
    path = _path_for(ms.form_id)
    path.write_text(
        json.dumps(ms.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def load_mapping_set(form_id: str) -> MappingSet | None:
    """Load a MappingSet from disk.

    Args:
        form_id: The form identifier.

    Returns:
        The deserialized ``MappingSet``, or ``None`` if the file doesn't exist.
    """
    path = _path_for(form_id)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return MappingSet.from_dict(data)


def list_mapping_sets() -> list[MappingSet]:
    """Load and return all saved MappingSets.

    Returns:
        List of ``MappingSet`` objects found in the mappings directory,
        sorted by form_id.
    """
    _ensure_dir()
    results: list[MappingSet] = []
    for path in sorted(MAPPINGS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            results.append(MappingSet.from_dict(data))
        except Exception:
            continue
    return results


# ---------------------------------------------------------------------------
# Approve / Reject / Override
# ---------------------------------------------------------------------------

def _find_mapping(ms: MappingSet, field_id: str) -> FieldMapping | None:
    """Locate a FieldMapping within a MappingSet by field_id."""
    for m in ms.mappings:
        if m.field_id == field_id:
            return m
    return None


def approve_mapping(
    form_id: str,
    field_id: str,
    approved_by: str = "user",
) -> bool:
    """Mark a single mapping as approved.

    Args:
        form_id: The form identifier.
        field_id: The field within the form to approve.
        approved_by: Who approved the mapping (default ``"user"``).

    Returns:
        ``True`` if the mapping was found and approved, ``False`` otherwise.
    """
    ms = load_mapping_set(form_id)
    if ms is None:
        return False

    mapping = _find_mapping(ms, field_id)
    if mapping is None:
        return False

    mapping.approved = True
    mapping.approved_by = approved_by
    mapping.approved_at = datetime.now(timezone.utc).isoformat()

    save_mapping_set(ms)

    log_action(
        action="mapping_approved",
        form_id=form_id,
        field_id=field_id,
        details={
            "sf_field": mapping.sf_field,
            "method": mapping.match_method,
            "confidence": mapping.confidence,
            "approved_by": approved_by,
        },
    )
    return True


def reject_mapping(form_id: str, field_id: str) -> bool:
    """Reject a mapping by clearing its SF field suggestion.

    Sets ``sf_field`` to ``""`` and ``confidence`` to ``0``, effectively
    removing the auto-mapped suggestion.

    Args:
        form_id: The form identifier.
        field_id: The field within the form to reject.

    Returns:
        ``True`` if the mapping was found and rejected, ``False`` otherwise.
    """
    ms = load_mapping_set(form_id)
    if ms is None:
        return False

    mapping = _find_mapping(ms, field_id)
    if mapping is None:
        return False

    old_sf = mapping.sf_field
    mapping.sf_field = ""
    mapping.confidence = 0.0
    mapping.match_method = ""
    mapping.approved = False
    mapping.approved_by = ""
    mapping.approved_at = ""

    save_mapping_set(ms)

    log_action(
        action="mapping_rejected",
        form_id=form_id,
        field_id=field_id,
        details={"previous_sf_field": old_sf},
    )
    return True


def override_mapping(
    form_id: str,
    field_id: str,
    sf_field: str,
    sf_object: str = "Contact",
    approved_by: str = "user",
) -> bool:
    """Manually override a mapping with a specific SF field and approve it.

    Args:
        form_id: The form identifier.
        field_id: The field within the form to override.
        sf_field: The Salesforce API field name to map to.
        sf_object: The target SF object (default ``"Contact"``).
        approved_by: Who performed the override (default ``"user"``).

    Returns:
        ``True`` if the mapping was found and overridden, ``False`` otherwise.
    """
    ms = load_mapping_set(form_id)
    if ms is None:
        return False

    mapping = _find_mapping(ms, field_id)
    if mapping is None:
        return False

    old_sf = mapping.sf_field
    old_obj = mapping.sf_object
    mapping.sf_field = sf_field
    mapping.sf_object = sf_object
    mapping.match_method = "manual"
    mapping.confidence = 1.0
    mapping.approved = True
    mapping.approved_by = approved_by
    mapping.approved_at = datetime.now(timezone.utc).isoformat()

    save_mapping_set(ms)

    log_action(
        action="mapping_overridden",
        form_id=form_id,
        field_id=field_id,
        details={
            "previous_sf_field": old_sf,
            "previous_sf_object": old_obj,
            "new_sf_field": sf_field,
            "new_sf_object": sf_object,
            "approved_by": approved_by,
        },
    )
    return True


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_unmatched_fields(form_id: str) -> list[str]:
    """Return field_ids that have no SF mapping.

    Args:
        form_id: The form identifier.

    Returns:
        List of ``field_id`` strings where ``sf_field`` is empty.
    """
    ms = load_mapping_set(form_id)
    if ms is None:
        return []
    return [m.field_id for m in ms.mappings if not m.sf_field]


def bulk_approve_high_confidence(
    form_id: str,
    threshold: float = 0.9,
    approved_by: str = "user",
) -> int:
    """Approve all pending mappings whose confidence meets or exceeds a threshold.

    Only mappings that have a non-empty ``sf_field`` and are not yet approved
    are considered.

    Args:
        form_id: The form identifier.
        threshold: Minimum confidence required (default ``0.9``).
        approved_by: Who approved the mappings (default ``"user"``).

    Returns:
        Number of mappings approved.
    """
    ms = load_mapping_set(form_id)
    if ms is None:
        return 0

    now = datetime.now(timezone.utc).isoformat()
    count = 0

    for mapping in ms.mappings:
        if mapping.sf_field and not mapping.approved and mapping.confidence >= threshold:
            mapping.approved = True
            mapping.approved_by = approved_by
            mapping.approved_at = now
            count += 1

    if count > 0:
        save_mapping_set(ms)

        log_action(
            action="bulk_mapping_approved",
            form_id=form_id,
            details={
                "threshold": threshold,
                "count": count,
                "approved_by": approved_by,
            },
        )

    return count
