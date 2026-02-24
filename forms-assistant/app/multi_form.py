"""Schema merging across multiple forms for unified data entry.

When a user fills out several related USCIS forms at once (e.g. I-589 +
I-765 + I-131), many fields map to the same Salesforce object/field --
applicant name, A-number, date of birth, etc.  This module identifies
those shared fields so the UI can present a single input widget instead
of asking for the same value three times.

Functions:
    merge_form_schemas  -- find shared vs unique fields across forms
    split_form_data     -- fan unified answers back to per-form dicts
    get_shared_field_key -- canonical session-state key for shared fields
"""

from __future__ import annotations

from app.mapping_store import load_mapping_set
from app.schema import FormFieldSchema, FormSchema


def merge_form_schemas(schemas: list[FormSchema]) -> dict:
    """Identify shared and unique fields across multiple FormSchemas.

    Two fields are considered "shared" when they have the same approved
    Salesforce mapping (sf_object + sf_field) in their MappingSet.

    Args:
        schemas: List of FormSchema objects to merge.

    Returns:
        A dict with four keys:

        - ``shared_fields``: list[FormFieldSchema] -- deduplicated shared
          fields (uses the first form's definition for display/type info).
        - ``form_specific``: dict[str, list[FormFieldSchema]] -- fields
          unique to each form, keyed by form_id.
        - ``field_to_forms``: dict[str, list[str]] -- for every shared
          field_id (from the first form's definition), the list of
          form_ids that contain it.
        - ``sf_to_field_ids``: dict[str, list[tuple[str, str]]] -- maps
          each SF field name to a list of (form_id, field_id) tuples
          across all forms.
    """
    # Build a lookup: sf_field -> list of (form_id, field_id, FormFieldSchema)
    sf_to_entries: dict[str, list[tuple[str, str, FormFieldSchema]]] = {}

    for schema in schemas:
        mapping_set = load_mapping_set(schema.form_id)
        approved = {}
        if mapping_set:
            approved = {
                m.field_id: m.sf_field
                for m in mapping_set.get_approved_mappings()
            }

        for fld in schema.fields:
            sf_field = approved.get(fld.field_id, "")
            if sf_field:
                sf_to_entries.setdefault(sf_field, []).append(
                    (schema.form_id, fld.field_id, fld)
                )

    # Partition into shared (sf_field appears in 2+ forms) vs per-form
    shared_fields: list[FormFieldSchema] = []
    field_to_forms: dict[str, list[str]] = {}
    sf_to_field_ids: dict[str, list[tuple[str, str]]] = {}
    seen_shared_sf: set[str] = set()

    # Track which field_ids are shared so we can build form_specific later
    shared_field_ids_per_form: dict[str, set[str]] = {
        s.form_id: set() for s in schemas
    }

    for sf_field, entries in sf_to_entries.items():
        # Collect distinct form_ids that map to this SF field
        form_ids_for_sf = list(dict.fromkeys(e[0] for e in entries))

        # Always populate sf_to_field_ids regardless of shared/unique
        sf_to_field_ids[sf_field] = [(fid, field_id) for fid, field_id, _ in entries]

        if len(form_ids_for_sf) >= 2:
            # Shared field -- use the first form's definition as canonical
            first_entry = entries[0]
            canonical_field = first_entry[2]

            if sf_field not in seen_shared_sf:
                shared_fields.append(canonical_field)
                seen_shared_sf.add(sf_field)
                field_to_forms[canonical_field.field_id] = form_ids_for_sf

            for form_id, field_id, _ in entries:
                shared_field_ids_per_form[form_id].add(field_id)

    # Build form_specific: fields that are NOT shared
    form_specific: dict[str, list[FormFieldSchema]] = {}
    for schema in schemas:
        unique = [
            fld
            for fld in schema.fields
            if fld.field_id not in shared_field_ids_per_form[schema.form_id]
        ]
        if unique:
            form_specific[schema.form_id] = unique

    return {
        "shared_fields": shared_fields,
        "form_specific": form_specific,
        "field_to_forms": field_to_forms,
        "sf_to_field_ids": sf_to_field_ids,
    }


def split_form_data(merged_info: dict, form_data: dict) -> dict[str, dict]:
    """Split unified form data back into per-form dicts.

    After the user fills in a merged form, this function distributes
    values to each constituent form.  Shared fields are copied to every
    form that uses them; form-specific fields go only to their form.

    Args:
        merged_info: The dict returned by ``merge_form_schemas``.
        form_data: A flat dict of {field_id_or_shared_key: value} as
            collected from the unified UI.

    Returns:
        Dict of {form_id: {field_id: value}} ready for per-form
        processing, PDF filling, or Salesforce sync.
    """
    sf_to_field_ids: dict[str, list[tuple[str, str]]] = merged_info["sf_to_field_ids"]
    form_specific: dict[str, list[FormFieldSchema]] = merged_info.get("form_specific", {})
    shared_fields: list[FormFieldSchema] = merged_info.get("shared_fields", [])

    result: dict[str, dict] = {}

    # Collect all form_ids from form_specific and shared mappings
    all_form_ids: set[str] = set(form_specific.keys())
    for entries in sf_to_field_ids.values():
        for form_id, _ in entries:
            all_form_ids.add(form_id)

    for form_id in all_form_ids:
        result[form_id] = {}

    # Distribute shared field values: look up by shared key, then copy to
    # every (form_id, field_id) tuple that maps to the same SF field.
    for fld in shared_fields:
        shared_key = get_shared_field_key(fld.sf_field)

        # Also try the canonical field_id as a fallback
        value = form_data.get(shared_key, form_data.get(fld.field_id))
        if value is None:
            continue

        # Find the SF field for this shared field by checking sf_to_field_ids
        for sf_field, entries in sf_to_field_ids.items():
            field_ids_in_entries = {fid for _, fid in entries}
            if fld.field_id in field_ids_in_entries:
                for form_id, field_id in entries:
                    result.setdefault(form_id, {})[field_id] = value
                break

    # Distribute form-specific field values
    for form_id, fields in form_specific.items():
        for fld in fields:
            value = form_data.get(fld.field_id)
            if value is not None:
                result.setdefault(form_id, {})[fld.field_id] = value

    return result


def get_shared_field_key(sf_field: str) -> str:
    """Generate a canonical session-state key for a shared field.

    In multi-form mode, shared fields (those mapping to the same SF
    field across forms) need a single widget key.  This function
    produces that key from the Salesforce field API name.

    Args:
        sf_field: The Salesforce field API name (e.g. ``"FirstName"``).

    Returns:
        A string like ``"shared_FirstName"`` suitable for use as a
        Streamlit session state key.
    """
    return f"shared_{sf_field}"
