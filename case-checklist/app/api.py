"""FastAPI backend for the Case Checklist tool.

Provides RESTful endpoints for managing immigration cases and their
associated checklists, including CRUD operations, item-level updates,
and progress/status reporting.

Part of the O'Brien Immigration Law tool suite.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from app.checklists import (
    CASE_TYPES,
    add_custom_item,
    create_case,
    delete_case,
    get_case_progress,
    list_cases,
    load_case,
    save_case,
    update_item,
)

app = FastAPI(title="Case Checklist API — O'Brien Immigration Law")


# ── Request / response models ────────────────────────────────────────────────


class CreateCaseRequest(BaseModel):
    """Payload for creating a new case."""

    client_name: str
    case_type: str
    a_number: str = ""
    attorney: str = ""


class UpdateItemRequest(BaseModel):
    """Payload for updating a single checklist item."""

    is_completed: bool | None = None
    deadline: str | None = None
    notes: str | None = None


class AddItemRequest(BaseModel):
    """Payload for adding a custom checklist item."""

    title: str
    category: str = "Filing"
    deadline: str | None = None


# ── Endpoints ────────────────────────────────────────────────────────────────


@app.get("/api/case-types")
def get_case_types() -> list[str]:
    """List all available case types."""
    return CASE_TYPES


@app.get("/api/cases")
def get_cases(
    status: str | None = Query(None, description="Filter by status (Active/Completed)"),
    case_type: str | None = Query(None, description="Filter by case type"),
) -> list[dict[str, Any]]:
    """List all cases with progress summaries.

    Supports optional filtering by status and case type.
    """
    cases = list_cases()

    if status:
        cases = [c for c in cases if c.get("status") == status]
    if case_type:
        cases = [c for c in cases if c.get("case_type") == case_type]

    # Attach progress summary to each case
    for case in cases:
        case["progress"] = get_case_progress(case)

    return cases


@app.post("/api/cases", status_code=201)
def create_new_case(request: CreateCaseRequest) -> dict[str, Any]:
    """Create a new case with checklist auto-populated from template."""
    if request.case_type not in CASE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown case type: {request.case_type}. "
            f"Valid types: {', '.join(CASE_TYPES)}",
        )
    case = create_case(
        client_name=request.client_name,
        case_type=request.case_type,
        a_number=request.a_number,
        attorney=request.attorney,
    )
    case["progress"] = get_case_progress(case)
    return case


@app.get("/api/cases/{case_id}")
def get_case(case_id: str) -> dict[str, Any]:
    """Get a single case by ID, including full checklist and progress."""
    case = load_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")
    case["progress"] = get_case_progress(case)
    return case


@app.delete("/api/cases/{case_id}")
def remove_case(case_id: str) -> dict[str, str]:
    """Delete a case by ID."""
    deleted = delete_case(case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")
    return {"status": "deleted", "case_id": case_id}


@app.put("/api/cases/{case_id}/items/{item_id}")
def update_checklist_item(
    case_id: str,
    item_id: str,
    request: UpdateItemRequest,
) -> dict[str, Any]:
    """Update a specific checklist item (toggle completion, set deadline, add notes)."""
    updates: dict[str, Any] = {}
    if request.is_completed is not None:
        updates["is_completed"] = request.is_completed
    if request.deadline is not None:
        updates["deadline"] = request.deadline
    if request.notes is not None:
        updates["notes"] = request.notes

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided.")

    result = update_item(case_id, item_id, updates)
    if result is None:
        raise HTTPException(status_code=404, detail="Case or item not found.")
    result["progress"] = get_case_progress(result)
    return result


@app.post("/api/cases/{case_id}/items", status_code=201)
def add_checklist_item(case_id: str, request: AddItemRequest) -> dict[str, Any]:
    """Add a custom checklist item to an existing case."""
    result = add_custom_item(
        case_id=case_id,
        title=request.title,
        category=request.category,
        deadline=request.deadline,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")
    result["progress"] = get_case_progress(result)
    return result


@app.get("/api/cases/{case_id}/progress")
def get_progress(case_id: str) -> dict[str, Any]:
    """Get completion progress for a specific case."""
    case = load_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"Case not found: {case_id}")
    progress = get_case_progress(case)
    progress["case_id"] = case_id
    progress["status"] = case.get("status", "Active")
    return progress
