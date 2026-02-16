"""FastAPI backend for the Forms Assistant tool.

Provides endpoints for listing supported immigration forms, retrieving
field definitions and requirements, validating form data completeness,
and exporting completed form data.

Part of the O'Brien Immigration Law tool suite.
"""

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from app.form_definitions import (
    I589_FIELDS,
    SUPPORTED_FORMS,
    FormField,
    check_completeness,
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

    TODO: Add detailed field definitions for forms beyond I-589.
    TODO: Return proper 404 HTTPException when form not found.
    """
    form_meta = SUPPORTED_FORMS.get(form_id)
    if form_meta is None:
        return {"error": f"Unknown form: {form_id}"}

    # Build field definitions per section
    if form_id == "I-589":
        sections = {}
        for section_name, fields in I589_FIELDS.items():
            sections[section_name] = [
                {
                    "name": f.name,
                    "field_type": f.field_type,
                    "required": f.required,
                    "help_text": f.help_text,
                    "options": f.options,
                    "validation_rules": f.validation_rules,
                }
                for f in fields
            ]
    else:
        # Placeholder for forms without detailed field definitions
        sections = {
            section: []
            for section in form_meta["sections"]
        }

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

    TODO: Implement cross-field validation (e.g. spouse fields required
          only if marital status is "Married").
    TODO: Add section-level validation summaries.
    """
    completeness = check_completeness(form_id, request.data)

    # Run individual field validations for I-589
    field_errors: dict[str, list[str]] = {}
    if form_id == "I-589":
        for _section_name, fields in I589_FIELDS.items():
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

    TODO: Implement PDF export using python-docx or reportlab.
    TODO: Implement CSV export for spreadsheet compatibility.
    TODO: Map exported data to actual USCIS form field positions.
    TODO: Pre-fill official PDF forms using pdfrw or PyPDF.
    """
    form_meta = SUPPORTED_FORMS.get(form_id)
    if form_meta is None:
        return {"error": f"Unknown form: {form_id}"}

    if request.format == "json":
        return {
            "form_id": form_id,
            "title": form_meta["title"],
            "data": request.data,
            "format": "json",
        }

    # TODO: Implement other export formats
    return {
        "form_id": form_id,
        "status": "not_implemented",
        "message": f"Export format '{request.format}' is not yet supported.",
    }
