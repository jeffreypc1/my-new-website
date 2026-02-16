"""FastAPI backend for the Forms Assistant tool.

Provides endpoints for listing supported immigration forms, retrieving
field definitions and requirements, validating form data completeness,
exporting completed form data, and managing drafts.

Part of the O'Brien Immigration Law tool suite.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.form_definitions import (
    SUPPORTED_FORMS,
    check_completeness,
    delete_form_draft,
    get_fields_for_form,
    list_form_drafts,
    load_form_draft,
    new_draft_id,
    save_form_draft,
    validate_field,
)

app = FastAPI(title="Forms Assistant API")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class ValidateRequest(BaseModel):
    """Payload for validating form data completeness."""

    data: dict[str, str]


class ExportRequest(BaseModel):
    """Payload for exporting completed form data."""

    data: dict[str, str]
    format: str = "json"  # "json", "csv", "pdf"


class SaveDraftRequest(BaseModel):
    """Payload for saving a form draft."""

    form_id: str
    form_data: dict[str, str]
    current_section: int = 0


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/forms")
def list_forms() -> list[dict[str, Any]]:
    """List all supported immigration forms.

    Returns form metadata including title, agency, filing fee, and
    processing time for each supported form.
    """
    return [
        {
            "form_id": form_id,
            "title": meta["title"],
            "agency": meta["agency"],
            "filing_fee": meta["filing_fee"],
            "processing_time": meta["processing_time"],
            "sections": meta["sections"],
        }
        for form_id, meta in SUPPORTED_FORMS.items()
    ]


@app.get("/api/forms/{form_id}/fields")
def get_form_fields(form_id: str) -> dict[str, Any]:
    """Get field definitions and requirements for a specific form.

    Returns all fields organized by section, including field type,
    required status, help text, and validation rules.
    """
    form_meta = SUPPORTED_FORMS.get(form_id)
    if form_meta is None:
        raise HTTPException(status_code=404, detail=f"Unknown form: {form_id}")

    fields_dict = get_fields_for_form(form_id)
    sections: dict[str, list[dict]] = {}

    for section_name in form_meta["sections"]:
        field_list = fields_dict.get(section_name, [])
        sections[section_name] = [
            {
                "name": f.name,
                "field_type": f.field_type,
                "required": f.required,
                "help_text": f.help_text,
                "options": f.options,
                "validation_rules": f.validation_rules,
            }
            for f in field_list
        ]

    return {
        "form_id": form_id,
        "title": form_meta["title"],
        "sections": sections,
    }


@app.post("/api/forms/{form_id}/validate")
def validate_form(form_id: str, request: ValidateRequest) -> dict[str, Any]:
    """Validate form data completeness and correctness.

    Checks all provided field values against the form's field definitions,
    including required field checks, format validation, and type checking.

    Returns a completeness report with any validation errors.
    """
    if form_id not in SUPPORTED_FORMS:
        raise HTTPException(status_code=404, detail=f"Unknown form: {form_id}")

    completeness = check_completeness(form_id, request.data)

    # Run individual field validations
    field_errors: dict[str, list[str]] = {}
    fields_dict = get_fields_for_form(form_id)
    for _section_name, fields in fields_dict.items():
        for field_def in fields:
            value = request.data.get(field_def.name, "")
            errors = validate_field(field_def, value)
            if errors:
                field_errors[field_def.name] = errors

    return {
        "form_id": form_id,
        "completeness": completeness,
        "field_errors": field_errors,
    }


@app.post("/api/forms/{form_id}/export")
def export_form(form_id: str, request: ExportRequest) -> dict[str, Any]:
    """Export completed form data in the requested format.

    Supports JSON export (default). PDF and CSV export are planned.
    """
    form_meta = SUPPORTED_FORMS.get(form_id)
    if form_meta is None:
        raise HTTPException(status_code=404, detail=f"Unknown form: {form_id}")

    if request.format == "json":
        return {
            "form_id": form_id,
            "title": form_meta["title"],
            "data": request.data,
            "format": "json",
        }

    raise HTTPException(
        status_code=400,
        detail=f"Export format '{request.format}' is not yet supported.",
    )


# ---------------------------------------------------------------------------
# Draft endpoints
# ---------------------------------------------------------------------------

@app.get("/api/drafts")
def list_drafts() -> list[dict[str, Any]]:
    """List all saved form drafts, newest first."""
    return list_form_drafts()


@app.post("/api/drafts")
def create_draft(request: SaveDraftRequest) -> dict[str, Any]:
    """Create a new form draft."""
    draft_id = new_draft_id()
    draft = save_form_draft(draft_id, request.form_id, request.form_data, request.current_section)
    return draft


@app.get("/api/drafts/{draft_id}")
def get_draft(draft_id: str) -> dict[str, Any]:
    """Load a specific draft by ID."""
    draft = load_form_draft(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail=f"Draft not found: {draft_id}")
    return draft


@app.put("/api/drafts/{draft_id}")
def update_draft(draft_id: str, request: SaveDraftRequest) -> dict[str, Any]:
    """Update an existing draft."""
    existing = load_form_draft(draft_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Draft not found: {draft_id}")
    draft = save_form_draft(draft_id, request.form_id, request.form_data, request.current_section)
    return draft


@app.delete("/api/drafts/{draft_id}")
def remove_draft(draft_id: str) -> dict[str, str]:
    """Delete a draft by ID."""
    deleted = delete_form_draft(draft_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Draft not found: {draft_id}")
    return {"status": "deleted", "draft_id": draft_id}
