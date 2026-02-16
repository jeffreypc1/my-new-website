"""FastAPI backend for the Cover Letter Generator tool.

Part of the O'Brien Immigration Law tool suite. Provides endpoints for
managing cover letter templates and generating formatted cover letters
from case data for various immigration filing types.
"""

from fastapi import FastAPI, Query
from pydantic import BaseModel

from app.templates import get_template, load_templates, render_template

app = FastAPI(title="Cover Letter Generator API")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class CaseData(BaseModel):
    """Input data for generating a cover letter."""

    case_type: str
    client_name: str
    a_number: str = ""
    receipt_number: str = ""
    filing_office: str = ""
    enclosed_documents: list[str] = []
    # TODO: Add additional fields as needed per case type:
    #   - priority_date, petitioner_name, beneficiary_name
    #   - court_date, judge_name (removal defense)
    #   - certification_date (U-Visa / T-Visa)


class GenerateRequest(BaseModel):
    """Request body for cover letter generation."""

    template_id: str
    case_data: CaseData


class ExportRequest(BaseModel):
    """Request body for DOCX export."""

    template_id: str
    case_data: CaseData
    # TODO: Add formatting options (letterhead toggle, font size, etc.)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/templates")
def list_templates(
    case_type: str | None = Query(None, description="Filter templates by case type"),
) -> list[dict]:
    """List all available cover letter templates.

    Returns a list of template metadata dicts with keys: id, name,
    case_type, description, and sections. Optionally filter by case type
    (e.g. "Asylum", "VAWA").

    TODO: Load templates from persistent storage (JSON files or database).
    """
    templates = load_templates()
    if case_type:
        templates = [t for t in templates if t.get("case_type") == case_type]
    return templates


@app.get("/api/templates/{template_id}")
def get_template_by_id(template_id: str) -> dict:
    """Retrieve a specific cover letter template by its ID.

    Returns the full template including its section definitions, placeholder
    fields, and default language blocks. Returns 404 if not found.

    TODO: Return proper HTTPException on missing template.
    """
    template = get_template(template_id)
    if template is None:
        return {"error": "Template not found"}
    return template


@app.post("/api/generate")
def generate_cover_letter(req: GenerateRequest) -> dict:
    """Generate a cover letter from a template and case data.

    Merges the selected template with the provided case data to produce
    a complete cover letter. The result includes:
    - rendered_text: the full letter as plain text
    - sections: list of rendered section dicts (heading + body)
    - warnings: any missing fields or validation issues

    Cover letters typically include:
    - Date and filing office address
    - RE: line with client name, A-number, receipt number
    - Purpose of filing
    - List of enclosed forms and supporting documents
    - Attorney signature block

    TODO: Implement actual template rendering with variable substitution.
    """
    rendered = render_template(req.template_id, req.case_data.model_dump())
    return {
        "rendered_text": rendered.get("text", ""),
        "sections": rendered.get("sections", []),
        "warnings": rendered.get("warnings", []),
    }


@app.post("/api/export/docx")
def export_to_docx(req: ExportRequest) -> dict:
    """Export a generated cover letter to Word (.docx) format.

    Creates a formatted Word document using python-docx with firm
    letterhead, proper formatting, and the rendered cover letter content.
    The document can then be uploaded to Google Docs via the Google
    Drive API for collaborative editing.

    Returns:
    - download_url: temporary URL to download the generated .docx file
    - filename: suggested filename for the download

    TODO: Implement DOCX generation with python-docx.
    TODO: Add optional Google Docs upload (similar to country-reports-tool).
    """
    # TODO: Generate the DOCX file and return a download link
    rendered = render_template(req.template_id, req.case_data.model_dump())
    return {
        "status": "not_implemented",
        "filename": f"cover_letter_{req.case_data.client_name}.docx",
        "rendered_text": rendered.get("text", ""),
    }
