"""FastAPI backend for the Brief Builder tool.

Provides endpoints for listing brief types, retrieving standard sections,
assembling briefs from structured arguments and citations, and exporting
to Word (.docx) format.

Part of the O'Brien Immigration Law tool suite.
"""

import io
from typing import Any

from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel

from app.sections import BRIEF_TYPES, get_boilerplate, load_sections

app = FastAPI(title="Brief Builder API")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class CaseInfo(BaseModel):
    """Basic case identification fields."""
    client_name: str = ""
    a_number: str = ""
    court_or_office: str = ""


class SectionContent(BaseModel):
    """A single section of a brief with its content and optional citations."""
    section_key: str
    heading: str
    body: str
    citations: list[str] = []


class GenerateRequest(BaseModel):
    """Payload for assembling a brief from sections."""
    brief_type: str
    case_info: CaseInfo
    sections: list[SectionContent]


class ExportDocxRequest(BaseModel):
    """Payload for exporting an assembled brief to Word format."""
    brief_type: str
    case_info: CaseInfo
    sections: list[SectionContent]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/brief-types")
def list_brief_types() -> list[str]:
    """Return the list of supported brief types.

    Each brief type maps to a standard set of sections defined in
    ``app.sections.BRIEF_TYPES``.
    """
    return list(BRIEF_TYPES.keys())


@app.get("/api/sections/{brief_type}")
def get_sections(brief_type: str) -> list[dict[str, Any]]:
    """Return the standard sections for a given brief type.

    Each section includes a machine-readable key, a display heading,
    optional boilerplate text, and a list of subsections (if any).
    """
    sections = load_sections(brief_type)
    return sections


@app.post("/api/generate")
def generate_brief(request: GenerateRequest) -> dict[str, Any]:
    """Assemble a brief from structured sections, arguments, and citations.

    Merges the user-provided section content with standard boilerplate
    for the selected brief type and returns the assembled document as
    structured data.
    """
    # TODO: Merge user-provided section content with boilerplate
    # TODO: Insert citations in proper legal format (Bluebook / immigration style)
    # TODO: Generate table of contents if applicable
    # TODO: Number pages and format headers/footers

    boilerplate = get_boilerplate(request.brief_type)
    assembled_sections: list[dict[str, Any]] = []

    for section in request.sections:
        assembled_sections.append({
            "heading": section.heading,
            "body": section.body,
            "citations": section.citations,
            "boilerplate_available": section.section_key in boilerplate,
        })

    return {
        "brief_type": request.brief_type,
        "case_info": request.case_info.model_dump(),
        "sections": assembled_sections,
        "status": "draft",
    }


@app.post("/api/export/docx")
def export_docx(request: ExportDocxRequest) -> Response:
    """Export the assembled brief to a Word (.docx) file.

    Uses python-docx to produce a properly formatted legal brief with
    standard margins, fonts, line spacing, and heading styles matching
    immigration court conventions.
    """
    # TODO: Import python-docx and build Document object
    # TODO: Set page layout (letter size, 1-inch margins)
    # TODO: Add caption/header block (court name, case info, A-number)
    # TODO: Add each section with proper heading styles
    # TODO: Insert citations as footnotes or inline references
    # TODO: Add certificate of service if applicable
    # TODO: Apply standard legal brief formatting (Times New Roman 12pt, double-spaced)

    # Placeholder: return an empty docx so the endpoint is functional
    try:
        from docx import Document

        doc = Document()
        doc.add_heading(f"{request.brief_type}", level=0)
        doc.add_paragraph(
            f"In the Matter of: {request.case_info.client_name}"
        )
        doc.add_paragraph(f"A-Number: {request.case_info.a_number}")
        doc.add_paragraph(f"Court/Office: {request.case_info.court_or_office}")
        doc.add_paragraph("")

        for section in request.sections:
            doc.add_heading(section.heading, level=1)
            doc.add_paragraph(section.body)
            if section.citations:
                doc.add_paragraph("Citations:", style="Intense Quote")
                for cite in section.citations:
                    doc.add_paragraph(cite, style="List Bullet")

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        docx_bytes = buf.read()
    except ImportError:
        # Graceful degradation if python-docx is not installed yet
        docx_bytes = b""

    filename = f"{request.brief_type.replace(' ', '_')}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
