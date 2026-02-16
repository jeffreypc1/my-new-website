"""FastAPI backend for the Evidence Indexer tool.

Provides endpoints for managing evidence packages, document metadata,
exhibit ordering, and exporting exhibit indexes and compiled bundles.

Part of the O'Brien Immigration Law tool suite.
"""

import io
from typing import Any

from fastapi import FastAPI, Query, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel

from app.evidence import (
    DOCUMENT_CATEGORIES,
    EvidenceItem,
    auto_assign_letters,
    generate_index,
    generate_index_docx,
    reorder_exhibits,
)

app = FastAPI(title="Evidence Indexer API")


# ---------------------------------------------------------------------------
# In-memory storage for evidence packages
# TODO: Persist to JSON files in data/ directory (same pattern as case-checklist).
# ---------------------------------------------------------------------------

_cases: dict[str, dict[str, Any]] = {}


def _get_or_create_case(case_id: str) -> dict[str, Any]:
    """Get or create an in-memory case record."""
    if case_id not in _cases:
        _cases[case_id] = {
            "case_id": case_id,
            "client_name": "",
            "documents": [],
            "next_doc_id": 1,
        }
    return _cases[case_id]


def _docs_to_items(case: dict) -> list[EvidenceItem]:
    """Convert stored document dicts to EvidenceItem objects."""
    return [
        EvidenceItem(
            exhibit_letter=d.get("exhibit_letter", ""),
            title=d.get("title", ""),
            category=d.get("category", "Other"),
            page_count=d.get("page_count", 0),
            date_added=d.get("date_added", ""),
            box_url=d.get("box_url", ""),
            description=d.get("description", ""),
            doc_id=d.get("doc_id", ""),
        )
        for d in case.get("documents", [])
    ]


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class AddDocumentRequest(BaseModel):
    """Payload for adding a document to an evidence package."""

    title: str
    category: str = "Other"
    description: str = ""
    page_count: int = 0
    box_url: str = ""


class UpdateDocumentRequest(BaseModel):
    """Payload for updating document metadata."""

    title: str | None = None
    exhibit_letter: str | None = None
    category: str | None = None
    description: str | None = None
    page_count: int | None = None


class ReorderRequest(BaseModel):
    """Payload for reordering exhibits."""

    new_order: list[int]  # List of current indices in desired new order


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/categories")
def list_categories() -> list[str]:
    """List standard immigration evidence document categories."""
    return DOCUMENT_CATEGORIES


@app.get("/api/cases")
def list_cases() -> list[dict[str, Any]]:
    """List all cases with evidence packages.

    Returns each case with its document count and exhibit letter range.

    TODO: Persist cases to disk and load on startup.
    TODO: Add pagination and filtering.
    """
    result = []
    for case_id, case in _cases.items():
        docs = case.get("documents", [])
        result.append({
            "case_id": case_id,
            "client_name": case.get("client_name", ""),
            "document_count": len(docs),
        })
    return result


@app.post("/api/cases/{case_id}/documents")
def add_document(case_id: str, request: AddDocumentRequest) -> dict[str, Any]:
    """Add a document to an evidence package.

    The document is assigned the next sequential exhibit letter automatically.
    The letter can be overridden later via the update endpoint.

    TODO: Support file upload (PDF) and auto-extract page count.
    TODO: Integrate with Box API for file references.
    """
    from datetime import date as _date

    case = _get_or_create_case(case_id)
    doc_id = str(case["next_doc_id"])
    case["next_doc_id"] += 1

    doc = {
        "doc_id": doc_id,
        "title": request.title,
        "category": request.category,
        "description": request.description,
        "page_count": request.page_count,
        "box_url": request.box_url,
        "date_added": _date.today().isoformat(),
        "exhibit_letter": "",  # Will be auto-assigned
    }
    case["documents"].append(doc)

    # Auto-assign exhibit letters to all documents
    items = _docs_to_items(case)
    items = auto_assign_letters(items)
    for i, item in enumerate(items):
        case["documents"][i]["exhibit_letter"] = item.exhibit_letter

    return doc


@app.put("/api/cases/{case_id}/documents/{doc_id}")
def update_document(
    case_id: str,
    doc_id: str,
    request: UpdateDocumentRequest,
) -> dict[str, Any]:
    """Update document metadata (label, exhibit letter, category, etc.).

    TODO: Re-validate exhibit letter uniqueness.
    TODO: Add audit logging for document changes.
    """
    case = _cases.get(case_id)
    if case is None:
        return {"error": f"Case not found: {case_id}"}

    doc = next((d for d in case["documents"] if d["doc_id"] == doc_id), None)
    if doc is None:
        return {"error": f"Document not found: {doc_id}"}

    if request.title is not None:
        doc["title"] = request.title
    if request.exhibit_letter is not None:
        doc["exhibit_letter"] = request.exhibit_letter
    if request.category is not None:
        doc["category"] = request.category
    if request.description is not None:
        doc["description"] = request.description
    if request.page_count is not None:
        doc["page_count"] = request.page_count

    return doc


@app.post("/api/cases/{case_id}/reorder")
def reorder_documents(case_id: str, request: ReorderRequest) -> list[dict[str, Any]]:
    """Reorder exhibits and reassign exhibit letters.

    Accepts a list of current indices in the desired new order.
    All exhibit letters are reassigned sequentially after reordering.

    TODO: Validate new_order indices.
    TODO: Support drag-and-drop single-item moves.
    """
    case = _cases.get(case_id)
    if case is None:
        return [{"error": f"Case not found: {case_id}"}]

    items = _docs_to_items(case)
    reordered = reorder_exhibits(items, request.new_order)

    # Update the case documents in the new order
    old_docs = case["documents"]
    new_docs = []
    for idx in request.new_order:
        if 0 <= idx < len(old_docs):
            new_docs.append(old_docs[idx])

    # Apply new exhibit letters
    for i, item in enumerate(reordered):
        if i < len(new_docs):
            new_docs[i]["exhibit_letter"] = item.exhibit_letter

    case["documents"] = new_docs
    return new_docs


@app.post("/api/cases/{case_id}/export/index")
def export_index(case_id: str) -> Response:
    """Export the exhibit index as a Word (.docx) document.

    Generates a formatted table listing all exhibits with their letters,
    titles, categories, and page counts.
    """
    case = _cases.get(case_id)
    if case is None:
        return Response(content=b"", status_code=404)

    items = _docs_to_items(case)
    client_name = case.get("client_name", "")
    docx_bytes = generate_index_docx(items, case_name=client_name)

    filename = f"exhibit_index_{case_id}.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/cases/{case_id}/export/bundle")
def export_bundle(case_id: str) -> dict[str, Any]:
    """Compile an exhibit bundle PDF with tab pages.

    Follows the same pattern as country-reports-tool/app/exhibit_compiler.py:
    downloads PDFs from Box, inserts tab divider pages between exhibits,
    merges into a single PDF, and adds Bates-style page numbers.

    TODO: Implement PDF compilation using pymupdf.
    TODO: Share exhibit_compiler code with country-reports-tool.
    TODO: Support configurable tab page styling.
    TODO: Return the compiled PDF bytes as a download response.
    """
    case = _cases.get(case_id)
    if case is None:
        return {"error": f"Case not found: {case_id}"}

    items = _docs_to_items(case)

    # TODO: For each item with a box_url:
    #   1. Download the PDF from Box
    #   2. Insert a tab divider page (TAB A, TAB B, etc.)
    #   3. Append the document pages
    #   4. Add Bates-style page numbers to content pages
    #   5. Return the merged PDF bytes

    return {
        "status": "not_implemented",
        "case_id": case_id,
        "document_count": len(items),
        "message": (
            "Bundle compilation is not yet implemented. "
            "Will follow the same pattern as country-reports-tool exhibit compiler."
        ),
    }
