"""FastAPI backend for the Declaration Drafter tool."""

from __future__ import annotations

import io
from datetime import date

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, Inches
from fastapi import FastAPI
from pydantic import BaseModel

from app.prompts import (
    DECLARATION_PROMPTS,
    DECLARATION_TYPES,
    PERJURY_CLAUSE,
    build_declaration_text,
    format_numbered_paragraphs,
)

app = FastAPI(title="Declaration Drafter API")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class DeclarantInfo(BaseModel):
    name: str
    country_of_origin: str = ""
    language: str = "English"
    a_number: str = ""


class GenerateRequest(BaseModel):
    declaration_type: str
    declarant: DeclarantInfo
    answers: dict[str, str]


class ExportDocxRequest(BaseModel):
    declaration_type: str
    declarant: DeclarantInfo
    answers: dict[str, str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/declaration-types")
def list_declaration_types() -> list[str]:
    """Return the available declaration types."""
    return DECLARATION_TYPES


@app.get("/api/prompts/{declaration_type}")
def get_prompts(declaration_type: str) -> list[dict]:
    """Return the guided prompt sections and questions for a declaration type.

    Returns a 404-style empty list if the declaration type is unknown.
    """
    sections = DECLARATION_PROMPTS.get(declaration_type, [])
    return sections


@app.post("/api/generate")
def generate_declaration(req: GenerateRequest) -> dict:
    """Assemble a declaration from the answers to guided prompts.

    Returns the full declaration text and paragraph count.
    """
    text = build_declaration_text(
        answers=req.answers,
        declaration_type=req.declaration_type,
        declarant_name=req.declarant.name,
    )
    paragraphs = format_numbered_paragraphs(req.answers, req.declaration_type)
    return {
        "declaration_text": text,
        "paragraph_count": len(paragraphs),
        "declaration_type": req.declaration_type,
        "declarant_name": req.declarant.name,
    }


@app.post("/api/export/docx")
def export_docx(req: ExportDocxRequest):
    """Export the declaration to a Word document with proper formatting.

    Returns a .docx file as an octet-stream download.
    """
    from fastapi.responses import StreamingResponse

    doc = _build_docx(
        answers=req.answers,
        declaration_type=req.declaration_type,
        declarant_name=req.declarant.name,
        country_of_origin=req.declarant.country_of_origin,
        a_number=req.declarant.a_number,
    )

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    safe_name = req.declarant.name.replace(" ", "_")
    filename = f"Declaration_{safe_name}.docx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# DOCX builder
# ---------------------------------------------------------------------------

def _build_docx(
    answers: dict[str, str],
    declaration_type: str,
    declarant_name: str,
    country_of_origin: str = "",
    a_number: str = "",
) -> Document:
    """Build a python-docx Document with proper declaration formatting.

    Layout:
      - Title (declaration type + declarant name)
      - Caption block (A-number, country of origin)
      - Numbered body paragraphs from answers
      - Penalty-of-perjury closing clause
      - Signature line
    """
    doc = Document()

    # -- Page margins --
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # -- Title --
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_para.add_run(f"DECLARATION OF {declarant_name.upper()}")
    title_run.bold = True
    title_run.font.size = Pt(14)
    title_run.font.name = "Times New Roman"

    # -- Caption / header info --
    if a_number or country_of_origin:
        caption_parts: list[str] = []
        if a_number:
            caption_parts.append(f"A# {a_number}")
        if country_of_origin:
            caption_parts.append(f"Country of Origin: {country_of_origin}")
        caption_para = doc.add_paragraph()
        caption_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption_run = caption_para.add_run(" | ".join(caption_parts))
        caption_run.font.size = Pt(10)
        caption_run.font.name = "Times New Roman"

    # -- Declaration type subtitle --
    type_para = doc.add_paragraph()
    type_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    type_run = type_para.add_run(declaration_type)
    type_run.italic = True
    type_run.font.size = Pt(11)
    type_run.font.name = "Times New Roman"

    # -- Opening statement --
    opening = doc.add_paragraph()
    opening_run = opening.add_run(
        f"I, {declarant_name}, hereby declare under penalty of perjury "
        "that the following statements are true and correct:"
    )
    opening_run.font.size = Pt(12)
    opening_run.font.name = "Times New Roman"

    # -- Numbered paragraphs --
    paragraphs = format_numbered_paragraphs(answers, declaration_type)
    for idx, para_text in enumerate(paragraphs, start=1):
        para = doc.add_paragraph()
        run = para.add_run(f"{idx}. {para_text}")
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"
        para_format = para.paragraph_format
        para_format.space_after = Pt(6)
        para_format.line_spacing = 1.5
        # TODO: use proper list numbering style instead of manual numbering

    # -- Perjury clause --
    doc.add_paragraph()  # blank line
    perjury_para = doc.add_paragraph()
    perjury_run = perjury_para.add_run(PERJURY_CLAUSE.format(name=declarant_name))
    perjury_run.font.size = Pt(12)
    perjury_run.font.name = "Times New Roman"

    # -- Signature block --
    doc.add_paragraph()  # blank line
    sig_line = doc.add_paragraph()
    sig_line.add_run("____________________________").font.name = "Times New Roman"

    name_line = doc.add_paragraph()
    name_run = name_line.add_run(declarant_name)
    name_run.font.size = Pt(12)
    name_run.font.name = "Times New Roman"

    date_line = doc.add_paragraph()
    date_run = date_line.add_run(f"Date: {date.today().strftime('%B %d, %Y')}")
    date_run.font.size = Pt(12)
    date_run.font.name = "Times New Roman"

    return doc
