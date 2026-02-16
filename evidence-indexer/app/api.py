"""FastAPI backend for the Evidence Indexer tool.

Provides endpoints for managing evidence packages, document metadata,
exhibit ordering, and exporting exhibit indexes and compiled bundles.
Uses JSON file persistence via the evidence module.

Part of the O'Brien Immigration Law tool suite.
"""

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.evidence import (
    DOCUMENT_CATEGORIES,
    EvidenceItem,
    _docs_to_items,
    add_document,
    auto_assign_letters,
    delete_case,
    generate_index,
    generate_index_docx,
    list_cases,
    load_case,
    new_case_id,
    remove_document,
    reorder_exhibits,
    save_case,
    update_document,
)

app = FastAPI(title="Evidence Indexer API")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class CreateCaseRequest(BaseModel):
    """Payload for creating a new case."""

    client_name: str = ""
    a_number: str = ""


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
    box_url: str | None = None


class ReorderRequest(BaseModel):
    """Payload for reordering exhibits."""

    new_order: list[int]  # List of current indices in desired new order


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/api/categories")
def get_categories() -> list[str]:
    """List standard immigration evidence document categories."""
    return DOCUMENT_CATEGORIES


@app.get("/api/cases")
def get_cases() -> list[dict[str, Any]]:
    """List all cases with evidence packages.

    Returns each case with its document count and last-updated timestamp.
    """
    return list_cases()


@app.post("/api/cases")
def create_case(request: CreateCaseRequest) -> dict[str, Any]:
    """Create a new empty evidence case.

    Returns the newly created case data.
    """
    case_id = new_case_id()
    return save_case(
        case_id=case_id,
        client_name=request.client_name,
        a_number=request.a_number,
        documents=[],
    )


@app.get("/api/cases/{case_id}")
def get_case(case_id: str) -> dict[str, Any]:
    """Get a single case with all its documents."""
    case_data = load_case(case_id)
    if case_data is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")
    return case_data


@app.delete("/api/cases/{case_id}")
def delete_case_endpoint(case_id: str) -> dict[str, str]:
    """Delete a case and its data."""
    if not delete_case(case_id):
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")
    return {"status": "deleted", "case_id": case_id}


@app.post("/api/cases/{case_id}/documents")
def add_document_endpoint(case_id: str, request: AddDocumentRequest) -> dict[str, Any]:
    """Add a document to an evidence package.

    The document is assigned the next sequential exhibit letter automatically.
    """
    doc = add_document(
        case_id=case_id,
        title=request.title,
        category=request.category,
        description=request.description,
        page_count=request.page_count,
        box_url=request.box_url,
    )
    if doc is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")
    return doc


@app.put("/api/cases/{case_id}/documents/{doc_id}")
def update_document_endpoint(
    case_id: str,
    doc_id: str,
    request: UpdateDocumentRequest,
) -> dict[str, Any]:
    """Update document metadata (title, exhibit letter, category, etc.)."""
    updates = {}
    if request.title is not None:
        updates["title"] = request.title
    if request.category is not None:
        updates["category"] = request.category
    if request.description is not None:
        updates["description"] = request.description
    if request.page_count is not None:
        updates["page_count"] = request.page_count
    if request.box_url is not None:
        updates["box_url"] = request.box_url

    doc = update_document(case_id, doc_id, **updates)
    if doc is None:
        raise HTTPException(
            status_code=404,
            detail=f"Case or document not found: {case_id}/{doc_id}",
        )
    return doc


@app.delete("/api/cases/{case_id}/documents/{doc_id}")
def remove_document_endpoint(case_id: str, doc_id: str) -> dict[str, str]:
    """Remove a document from an evidence package and reassign exhibit letters."""
    if not remove_document(case_id, doc_id):
        raise HTTPException(
            status_code=404,
            detail=f"Case or document not found: {case_id}/{doc_id}",
        )
    return {"status": "removed", "doc_id": doc_id}


@app.post("/api/cases/{case_id}/reorder")
def reorder_documents(case_id: str, request: ReorderRequest) -> list[dict[str, Any]]:
    """Reorder exhibits and reassign exhibit letters.

    Accepts a list of current indices in the desired new order.
    All exhibit letters are reassigned sequentially after reordering.
    """
    case_data = load_case(case_id)
    if case_data is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")

    documents = case_data.get("documents", [])
    items = _docs_to_items(documents)
    reordered = reorder_exhibits(items, request.new_order)

    # Build new documents list in the reordered sequence
    new_docs = []
    for idx in request.new_order:
        if 0 <= idx < len(documents):
            new_docs.append(documents[idx])

    # Apply new exhibit letters
    for i, item in enumerate(reordered):
        if i < len(new_docs):
            new_docs[i]["exhibit_letter"] = item.exhibit_letter

    save_case(
        case_id=case_data["id"],
        client_name=case_data.get("client_name", ""),
        a_number=case_data.get("a_number", ""),
        documents=new_docs,
    )

    return new_docs


@app.post("/api/cases/{case_id}/export/index")
def export_index(case_id: str) -> Response:
    """Export the exhibit index as a Word (.docx) document.

    Generates a formatted table listing all exhibits with their letters,
    titles, categories, and page counts.
    """
    case_data = load_case(case_id)
    if case_data is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")

    documents = case_data.get("documents", [])
    items = _docs_to_items(documents)
    client_name = case_data.get("client_name", "")
    docx_bytes = generate_index_docx(items, case_name=client_name)

    if not docx_bytes:
        raise HTTPException(
            status_code=500,
            detail="Could not generate Word document. Is python-docx installed?",
        )

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

    Not yet implemented -- returns a status message.
    """
    case_data = load_case(case_id)
    if case_data is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")

    documents = case_data.get("documents", [])

    return {
        "status": "not_implemented",
        "case_id": case_id,
        "document_count": len(documents),
        "message": (
            "Bundle compilation is not yet implemented. "
            "Will follow the same pattern as country-reports-tool exhibit compiler."
        ),
    }
