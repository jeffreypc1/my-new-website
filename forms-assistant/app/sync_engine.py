"""Bidirectional Salesforce sync engine.

Pulls field values from Contact, Contact_Plus__c, and Contact_Plus_1__c
into form data, and pushes form data back to those objects.  All operations
are scoped to approved mappings only and produce an append-only sync log
for auditing.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Allow shared imports from the monorepo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.schema import MappingSet, SyncLogEntry
from app.mapping_store import load_mapping_set
from app.audit_log import log_action

try:
    from shared.salesforce_client import (
        _sf_conn,
        load_active_client,
        update_client,
        get_client,
        get_related_record,
    )
except ImportError:
    # Graceful degradation when shared module is unavailable
    def _sf_conn():  # type: ignore[misc]
        return None

    def load_active_client() -> dict | None:  # type: ignore[misc]
        return None

    def update_client(sf_id: str, updates: dict) -> None:  # type: ignore[misc]
        pass

    def get_client(customer_id: str, fields: list[str] | None = None) -> dict | None:  # type: ignore[misc]
        return None

    def get_related_record(contact_id: str, object_name: str, lookup_field: str = "Contact__c") -> dict | None:  # type: ignore[misc]
        return None


DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "audit"
SYNC_LOG_PATH = DATA_DIR / "sync_log.jsonl"


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _append_sync_log(entry: SyncLogEntry) -> None:
    """Append a SyncLogEntry to the sync log JSONL file."""
    _ensure_dir()
    with SYNC_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")


def get_sync_log(limit: int = 50) -> list[SyncLogEntry]:
    """Read sync log entries from disk, newest first.

    Args:
        limit: Maximum number of entries to return.

    Returns:
        List of SyncLogEntry, most recent first.
    """
    if not SYNC_LOG_PATH.exists():
        return []

    entries: list[SyncLogEntry] = []
    try:
        with SYNC_LOG_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                entries.append(SyncLogEntry.from_dict(data))
    except Exception:
        return []

    # Newest first
    entries.reverse()
    return entries[:limit]


def _resolve_contact_id(contact_id: str | None) -> tuple[str | None, str | None]:
    """Resolve a contact_id (SF record Id) and customer_id from the active client.

    Returns:
        (sf_record_id, customer_id) -- either may be None if unavailable.
    """
    if contact_id:
        return contact_id, None

    client = load_active_client()
    if not client:
        return None, None

    return client.get("Id"), client.get("Customer_ID__c")


def _group_mappings_by_object(approved: list) -> dict[str, list]:
    """Group approved FieldMappings by sf_object."""
    groups: dict[str, list] = defaultdict(list)
    for m in approved:
        groups[m.sf_object].append(m)
    return dict(groups)


def _fetch_related_object_data(
    contact_id: str,
    object_name: str,
    fields: list[str],
) -> dict | None:
    """Fetch field values from a related custom object record."""
    sf = _sf_conn()
    if sf is None:
        return None

    related = get_related_record(contact_id, object_name)
    if not related:
        return None

    record_id = related.get("Id", "")
    if not record_id:
        return None

    # Always include Id
    query_fields = list(set(["Id"] + fields))
    field_list = ", ".join(query_fields)
    query = f"SELECT {field_list} FROM {object_name} WHERE Id = '{record_id}' LIMIT 1"

    try:
        result = sf.query(query)
        records = result.get("records", [])
        if records:
            return {k: v for k, v in records[0].items() if k != "attributes"}
    except Exception:
        pass

    return None


def pull_from_sf(
    form_id: str,
    form_data: dict,
    contact_id: str | None = None,
) -> dict:
    """Pull Salesforce field values into form fields.

    Loads the MappingSet for the given form, filters to approved mappings,
    groups by sf_object, fetches values from Contact + custom objects,
    and returns a dict of {field_id: sf_value} for fields that have data.

    Args:
        form_id:    The form identifier.
        form_data:  Current form field values (not modified, used for diff context).
        contact_id: SF Contact record Id.  Falls back to load_active_client().

    Returns:
        Dict mapping field_id -> value pulled from Salesforce.
    """
    result: dict = {}
    sf_record_id, customer_id = _resolve_contact_id(contact_id)

    if not sf_record_id and not customer_id:
        log_action(
            "sync_executed",
            form_id=form_id,
            details={"direction": "sf_to_form", "error": "No contact ID available"},
        )
        return result

    try:
        mapping_set: MappingSet = load_mapping_set(form_id)
    except Exception as exc:
        log_action(
            "sync_executed",
            form_id=form_id,
            details={"direction": "sf_to_form", "error": f"Failed to load mappings: {exc}"},
        )
        return result

    approved = mapping_set.get_approved_mappings()
    if not approved:
        return result

    # Group mappings by SF object
    groups = _group_mappings_by_object(approved)

    # Track all synced fields for logging
    fields_synced: dict = {}
    resolved_id = sf_record_id or customer_id or ""

    # --- Contact fields ---
    contact_mappings = groups.get("Contact", [])
    if contact_mappings:
        sf_fields_needed = list({m.sf_field for m in contact_mappings if m.sf_field})
        if sf_fields_needed:
            if "Id" not in sf_fields_needed:
                sf_fields_needed.insert(0, "Id")

            try:
                if customer_id:
                    record = get_client(customer_id, fields=sf_fields_needed)
                else:
                    sf = _sf_conn()
                    if sf is None:
                        raise RuntimeError("Salesforce connection unavailable")
                    field_list = ", ".join(sf_fields_needed)
                    query = f"SELECT {field_list} FROM Contact WHERE Id = '{sf_record_id}' LIMIT 1"
                    query_result = sf.query(query)
                    records = query_result.get("records", [])
                    record = {k: v for k, v in records[0].items() if k != "attributes"} if records else None

                if record:
                    resolved_id = record.get("Id") or resolved_id
                    for mapping in contact_mappings:
                        sf_val = record.get(mapping.sf_field)
                        if sf_val is not None and sf_val != "":
                            result[mapping.field_id] = sf_val
                            old_val = form_data.get(mapping.field_id, "")
                            fields_synced[mapping.sf_field] = {"old": old_val, "new": sf_val}
            except Exception as exc:
                entry = SyncLogEntry(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    direction="sf_to_form",
                    form_id=form_id,
                    contact_id=resolved_id,
                    fields_synced={},
                    status="failed",
                    error=f"Contact pull failed: {exc}",
                )
                _append_sync_log(entry)
                log_action(
                    "sync_executed",
                    form_id=form_id,
                    details={"direction": "sf_to_form", "error": str(exc)},
                )
                return result

    # --- Custom object fields (Contact_Plus__c, Contact_Plus_1__c) ---
    # Need the Contact SF Id for related record lookups
    contact_sf_id = resolved_id
    if not contact_sf_id and customer_id:
        try:
            rec = get_client(customer_id, fields=["Id"])
            if rec:
                contact_sf_id = rec.get("Id", "")
        except Exception:
            pass

    for obj_name in ["Contact_Plus__c", "Contact_Plus_1__c"]:
        obj_mappings = groups.get(obj_name, [])
        if not obj_mappings or not contact_sf_id:
            continue

        sf_fields_needed = list({m.sf_field for m in obj_mappings if m.sf_field})
        if not sf_fields_needed:
            continue

        try:
            obj_record = _fetch_related_object_data(
                contact_sf_id, obj_name, sf_fields_needed
            )
            if obj_record:
                for mapping in obj_mappings:
                    sf_val = obj_record.get(mapping.sf_field)
                    if sf_val is not None and sf_val != "":
                        result[mapping.field_id] = sf_val
                        old_val = form_data.get(mapping.field_id, "")
                        fields_synced[f"{obj_name}.{mapping.sf_field}"] = {
                            "old": old_val,
                            "new": sf_val,
                        }
        except Exception as exc:
            log_action(
                "sync_executed",
                form_id=form_id,
                details={
                    "direction": "sf_to_form",
                    "error": f"{obj_name} pull failed: {exc}",
                },
            )

    # Log the sync
    entry = SyncLogEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        direction="sf_to_form",
        form_id=form_id,
        contact_id=resolved_id,
        fields_synced=fields_synced,
        status="success" if fields_synced else "partial",
    )
    _append_sync_log(entry)
    log_action(
        "sync_executed",
        form_id=form_id,
        details={
            "direction": "sf_to_form",
            "fields_count": len(fields_synced),
            "contact_id": resolved_id,
        },
    )

    return result


def push_to_sf(
    form_id: str,
    form_data: dict,
    contact_id: str | None = None,
) -> dict:
    """Push form field values to Salesforce objects.

    Groups form data by target sf_object, pushes Contact fields to Contact,
    and custom object fields to the related records (creates if needed).

    Args:
        form_id:    The form identifier.
        form_data:  Current form field values keyed by field_id.
        contact_id: SF Contact record Id.  Falls back to load_active_client().

    Returns:
        Dict of {sf_field: value} that was pushed to Salesforce.
    """
    all_updates: dict = {}
    sf_record_id, customer_id = _resolve_contact_id(contact_id)

    # We need the SF record Id to update; if we only have customer_id, resolve it
    if not sf_record_id and customer_id:
        try:
            record = get_client(customer_id, fields=["Id"])
            if record:
                sf_record_id = record.get("Id")
        except Exception:
            pass

    if not sf_record_id:
        log_action(
            "sync_executed",
            form_id=form_id,
            details={"direction": "form_to_sf", "error": "No SF record Id available"},
        )
        return all_updates

    try:
        mapping_set: MappingSet = load_mapping_set(form_id)
    except Exception as exc:
        log_action(
            "sync_executed",
            form_id=form_id,
            details={"direction": "form_to_sf", "error": f"Failed to load mappings: {exc}"},
        )
        return all_updates

    approved = mapping_set.get_approved_mappings()
    if not approved:
        return all_updates

    # Group by SF object
    groups = _group_mappings_by_object(approved)

    # --- Push Contact fields ---
    contact_mappings = groups.get("Contact", [])
    if contact_mappings:
        contact_updates: dict = {}
        for mapping in contact_mappings:
            form_val = form_data.get(mapping.field_id)
            if form_val is not None and form_val != "":
                contact_updates[mapping.sf_field] = form_val

        if contact_updates:
            try:
                update_client(sf_record_id, contact_updates)
                all_updates.update(contact_updates)
            except Exception as exc:
                entry = SyncLogEntry(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    direction="form_to_sf",
                    form_id=form_id,
                    contact_id=sf_record_id,
                    fields_synced={k: {"old": None, "new": v} for k, v in contact_updates.items()},
                    status="failed",
                    error=f"Contact push failed: {exc}",
                )
                _append_sync_log(entry)
                log_action(
                    "sync_executed",
                    form_id=form_id,
                    details={"direction": "form_to_sf", "error": str(exc)},
                )
                return {}

    # --- Push custom object fields ---
    for obj_name in ["Contact_Plus__c", "Contact_Plus_1__c"]:
        obj_mappings = groups.get(obj_name, [])
        if not obj_mappings:
            continue

        obj_updates: dict = {}
        for mapping in obj_mappings:
            form_val = form_data.get(mapping.field_id)
            if form_val is not None and form_val != "":
                obj_updates[mapping.sf_field] = form_val

        if not obj_updates:
            continue

        try:
            sf = _sf_conn()
            if sf is None:
                raise RuntimeError("Salesforce connection unavailable")

            related = get_related_record(sf_record_id, obj_name)
            if not related:
                raise RuntimeError(f"Could not find/create {obj_name} record")

            related_id = related.get("Id", "")
            if not related_id:
                raise RuntimeError(f"No Id for {obj_name} record")

            getattr(sf, obj_name).update(related_id, obj_updates)
            # Prefix keys for tracking
            for k, v in obj_updates.items():
                all_updates[f"{obj_name}.{k}"] = v
        except Exception as exc:
            log_action(
                "sync_executed",
                form_id=form_id,
                details={
                    "direction": "form_to_sf",
                    "error": f"{obj_name} push failed: {exc}",
                },
            )

    if not all_updates:
        entry = SyncLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            direction="form_to_sf",
            form_id=form_id,
            contact_id=sf_record_id,
            fields_synced={},
            status="partial",
            error="No non-empty form values to push",
        )
        _append_sync_log(entry)
        return all_updates

    # Log success
    fields_synced = {k: {"old": None, "new": v} for k, v in all_updates.items()}
    entry = SyncLogEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        direction="form_to_sf",
        form_id=form_id,
        contact_id=sf_record_id,
        fields_synced=fields_synced,
        status="success",
    )
    _append_sync_log(entry)
    log_action(
        "sync_executed",
        form_id=form_id,
        details={
            "direction": "form_to_sf",
            "fields_count": len(all_updates),
            "contact_id": sf_record_id,
        },
    )

    return all_updates


def compute_diff(
    form_id: str,
    form_data: dict,
    sf_data: dict,
) -> list[dict]:
    """Compare form values against Salesforce values for approved mappings.

    Args:
        form_id:   The form identifier.
        form_data: Current form field values keyed by field_id.
        sf_data:   Salesforce field values keyed by SF API field name.
                   For custom objects, keys may be prefixed: "Contact_Plus__c.Field__c".

    Returns:
        List of dicts, each containing:
            field_id, sf_field, sf_object, display_label, form_value, sf_value,
            differs (bool).
        Only fields present in approved mappings are included.
    """
    try:
        mapping_set: MappingSet = load_mapping_set(form_id)
    except Exception:
        return []

    approved = mapping_set.get_approved_mappings()
    diffs: list[dict] = []

    for mapping in approved:
        form_val = form_data.get(mapping.field_id, "")

        # Look up SF value: try prefixed key first (for custom objects), then plain
        if mapping.sf_object != "Contact":
            sf_key = f"{mapping.sf_object}.{mapping.sf_field}"
            sf_val = sf_data.get(sf_key, sf_data.get(mapping.sf_field, ""))
        else:
            sf_val = sf_data.get(mapping.sf_field, "")

        # Normalize for comparison: treat None as empty string
        norm_form = str(form_val) if form_val is not None else ""
        norm_sf = str(sf_val) if sf_val is not None else ""

        diffs.append({
            "field_id": mapping.field_id,
            "sf_field": mapping.sf_field,
            "sf_object": mapping.sf_object,
            "display_label": mapping.field_id,  # caller can enrich with schema labels
            "form_value": form_val if form_val is not None else "",
            "sf_value": sf_val if sf_val is not None else "",
            "differs": norm_form != norm_sf,
        })

    return diffs
