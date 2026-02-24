"""Bridge between config store and form definitions for uploaded PDF forms.

Merges hardcoded SUPPORTED_FORMS with uploaded forms from config,
provides unified field access, and manages PDF template files.

Also bridges to the new FormSchema system (``app.ingestion``) so that
forms ingested through the new pipeline appear seamlessly alongside
hardcoded and legacy-uploaded forms.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.config_store import get_config_value, load_config
from app.form_definitions import (
    FIELD_DEFINITIONS,
    SUPPORTED_FORMS,
    _DEFAULT_SUPPORTED_FORMS,
    FormField,
)
from app.ingestion import load_form_schema, list_form_schemas

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "data" / "form_templates"


def _ensure_template_dir() -> None:
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)


def get_all_forms() -> dict[str, dict]:
    """Return all available forms: hardcoded + uploaded, minus deleted.

    Returns:
        Dict mapping form_id -> metadata dict (title, agency, etc.).
        Uploaded forms include an extra "_uploaded": True key.
    """
    deleted = get_config_value("forms-assistant", "deleted_forms", [])

    # Start with hardcoded forms (merge config-loaded + defaults for new forms)
    result: dict[str, dict] = {}
    for fid, meta in SUPPORTED_FORMS.items():
        if fid not in deleted:
            result[fid] = dict(meta)
    # Also include any forms in _DEFAULT_SUPPORTED_FORMS not yet in config
    for fid, meta in _DEFAULT_SUPPORTED_FORMS.items():
        if fid not in deleted and fid not in result:
            result[fid] = dict(meta)

    # Add uploaded forms from config
    cfg = load_config("forms-assistant") or {}
    uploaded = cfg.get("uploaded_forms", {})
    for fid, meta in uploaded.items():
        if fid not in deleted:
            entry = dict(meta)
            entry["_uploaded"] = True
            result[fid] = entry

    # Add forms from the new schema system that aren't already present
    for schema in list_form_schemas():
        if schema.form_id not in result and schema.form_id not in deleted:
            result[schema.form_id] = {
                "title": schema.title,
                "agency": schema.agency,
                "filing_fee": schema.filing_fee,
                "processing_time": schema.processing_time,
                "_uploaded": True,
                "_schema_source": schema.source,
                "_schema_version": schema.version,
            }

    return result


def get_all_fields(form_id: str) -> dict[str, list[FormField]]:
    """Return fields by section for any form (hardcoded or uploaded).

    For hardcoded forms, delegates to FIELD_DEFINITIONS.
    For uploaded forms, reconstructs FormField objects from config.
    """
    deleted = get_config_value("forms-assistant", "deleted_forms", [])
    if form_id in deleted:
        return {}

    # Check hardcoded first
    if form_id in FIELD_DEFINITIONS:
        return FIELD_DEFINITIONS[form_id]

    # Check uploaded forms (legacy config format)
    cfg = load_config("forms-assistant") or {}
    uploaded = cfg.get("uploaded_forms", {})
    form_cfg = uploaded.get(form_id)
    if form_cfg:
        fields_data = form_cfg.get("fields", [])
        sections: dict[str, list[FormField]] = {}

        for fd in fields_data:
            section = fd.get("section", "Page 1")
            ff = FormField(
                name=fd["pdf_field_name"],
                field_type=fd.get("field_type", "text"),
                required=fd.get("required", False),
                section=section,
                help_text=fd.get("help_text", ""),
                options=fd.get("options", []),
            )
            sections.setdefault(section, []).append(ff)

        return sections

    # Fall back to new FormSchema system
    schema = load_form_schema(form_id)
    if schema and schema.fields:
        sections = {}
        for f in schema.fields:
            sec = f.section or "General"
            ff = FormField(
                name=f.field_id,
                field_type=f.field_type,
                required=f.required,
                section=sec,
                help_text=f.help_text,
                options=f.options,
            )
            sections.setdefault(sec, []).append(ff)
        return sections

    return {}


def get_template_pdf_bytes(form_id: str) -> bytes | None:
    """Load the blank PDF template for an uploaded form.

    Returns None if the template file doesn't exist.
    """
    path = TEMPLATE_DIR / f"{form_id}.pdf"
    if not path.exists():
        return None
    return path.read_bytes()


def save_template_pdf(form_id: str, pdf_bytes: bytes) -> Path:
    """Save a blank PDF template and return the file path."""
    _ensure_template_dir()
    path = TEMPLATE_DIR / f"{form_id}.pdf"
    path.write_bytes(pdf_bytes)
    return path


def delete_template_pdf(form_id: str) -> bool:
    """Delete a PDF template file. Returns True if it existed."""
    path = TEMPLATE_DIR / f"{form_id}.pdf"
    if path.exists():
        path.unlink()
        return True
    return False


def is_uploaded_form(form_id: str) -> bool:
    """Check if a form has an uploaded PDF template."""
    cfg = load_config("forms-assistant") or {}
    uploaded = cfg.get("uploaded_forms", {})
    return form_id in uploaded


def get_field_roles(form_id: str) -> dict[str, str]:
    """Return a mapping of pdf_field_name -> role for auto-fill.

    Roles include attorney_* and preparer_* (filled from their
    respective stores). Only returns fields with a role other
    than "none".
    """
    cfg = load_config("forms-assistant") or {}
    uploaded = cfg.get("uploaded_forms", {})
    form_cfg = uploaded.get(form_id, {})
    fields = form_cfg.get("fields", [])

    roles: dict[str, str] = {}
    for fd in fields:
        role = fd.get("role", "none")
        if role and role != "none":
            roles[fd["pdf_field_name"]] = role

    return roles


def get_field_sf_mappings(form_id: str) -> dict[str, str]:
    """Return a mapping of pdf_field_name -> SF API field name.

    Checks the legacy config first, then falls back to the new
    MappingSet system (``app.mapping_store``).
    """
    # Legacy config format
    cfg = load_config("forms-assistant") or {}
    uploaded = cfg.get("uploaded_forms", {})
    form_cfg = uploaded.get(form_id, {})
    fields = form_cfg.get("fields", [])

    mappings: dict[str, str] = {}
    for fd in fields:
        sf = fd.get("sf_field", "")
        if sf:
            mappings[fd["pdf_field_name"]] = sf

    if mappings:
        return mappings

    # Fall back to new mapping store
    try:
        from app.mapping_store import load_mapping_set

        ms = load_mapping_set(form_id)
        if ms:
            for m in ms.get_approved_mappings():
                if m.sf_field:
                    mappings[m.field_id] = m.sf_field
    except ImportError:
        pass

    return mappings


def get_schema_version(form_id: str) -> int | None:
    """Return the latest schema version number, or None if no schema exists."""
    schema = load_form_schema(form_id)
    if schema:
        return schema.version
    return None


def get_form_source(form_id: str) -> str:
    """Return the source type for a form.

    Returns one of: "hardcoded", "uploaded_fillable", "uploaded_nonfillable",
    "uploaded" (legacy config), or "" if not found.
    """
    if form_id in FIELD_DEFINITIONS:
        return "hardcoded"

    schema = load_form_schema(form_id)
    if schema:
        return schema.source

    cfg = load_config("forms-assistant") or {}
    uploaded = cfg.get("uploaded_forms", {})
    if form_id in uploaded:
        return "uploaded"

    return ""
