"""FastAPI backend for the Case Checklist tool.

Provides endpoints for managing immigration cases and their associated
checklists, including case creation with auto-populated checklists,
status tracking, and checklist item updates.

Part of the O'Brien Immigration Law tool suite.
"""

from typing import Any

from fastapi import FastAPI, Query
from pydantic import BaseModel

from app.checklists import (
    CASE_TYPE_CHECKLISTS,
    create_case,
    load_case,
    load_cases,
    save_case,
    update_item,
)

app = FastAPI(title="Case Checklist API")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class CreateCaseRequest(BaseModel):
    """Payload for creating a new case with an auto-populated checklist."""

    case_id: str
    client_name: str
    case_type: str
    a_number: str = ""


class UpdateCaseRequest(BaseModel):
    """Payload for updating case metadata or checklist items."""

    status: str | None = None
    client_name: str | None = None
    a_number: str | None = None
    checklist_updates: list[dict[str, Any]] | None = None
    # checklist_updates: list of {"index": int, "completed": bool, "notes": str}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/case-types")
def list_case_types() -> list[dict[str, Any]]:
    """List all case types with their checklist item counts.

    Returns each case type name along with the number of checklist items
    and the categories covered by that checklist.
    """
    result = []
    for case_type, items in CASE_TYPE_CHECKLISTS.items():
        categories = sorted({item.category for item in items})
        result.append({
            "case_type": case_type,
            "item_count": len(items),
            "categories": categories,
            "items": [
                {
                    "label": item.label,
                    "required": item.required,
                    "category": item.category,
                    "deadline_days": item.deadline_days,
                }
                for item in items
            ],
        })
    return result


@app.get("/api/cases")
def list_active_cases(
    status: str | None = Query(None, description="Filter by status"),
    case_type: str | None = Query(None, description="Filter by case type"),
) -> list[dict[str, Any]]:
    """List all active cases with summary info.

    Returns each case with its metadata and checklist completion percentage.
    Supports optional filtering by status and case type.

    TODO: Add pagination support.
    TODO: Add sorting options (by deadline, by name, by creation date).
    """
    cases = load_cases()

    if status:
        cases = [c for c in cases if c.get("status") == status]
    if case_type:
        cases = [c for c in cases if c.get("case_type") == case_type]

    # Add completion summary to each case
    for case in cases:
        checklist = case.get("checklist", [])
        total = len(checklist)
        completed = sum(1 for item in checklist if item.get("completed"))
        case["completion"] = {
            "total": total,
            "completed": completed,
            "pct": round((completed / total) * 100) if total > 0 else 0,
        }

    return cases


@app.post("/api/cases")
def create_new_case(request: CreateCaseRequest) -> dict[str, Any]:
    """Create a new case with an auto-populated checklist.

    The checklist is pre-filled based on the case type. Each item includes
    a label, category, required status, and deadline (if applicable).

    TODO: Validate that case_id is unique.
    TODO: Support custom checklist items in addition to the template.
    """
    case = create_case(
        case_id=request.case_id,
        client_name=request.client_name,
        case_type=request.case_type,
        a_number=request.a_number,
    )
    return case


@app.put("/api/cases/{case_id}")
def update_case(case_id: str, request: UpdateCaseRequest) -> dict[str, Any]:
    """Update case metadata and/or checklist items.

    Supports updating the case status, client name, A-number, and
    individual checklist items. Checklist updates should be provided
    as a list of dicts with 'index' and the fields to update.

    TODO: Add validation for status transitions.
    TODO: Add audit logging for checklist changes.
    """
    case = load_case(case_id)
    if case is None:
        return {"error": f"Case not found: {case_id}"}

    # Update case-level metadata
    if request.status is not None:
        case["status"] = request.status
    if request.client_name is not None:
        case["client_name"] = request.client_name
    if request.a_number is not None:
        case["a_number"] = request.a_number

    # Update individual checklist items
    if request.checklist_updates:
        for update in request.checklist_updates:
            index = update.get("index")
            if index is not None:
                updates = {k: v for k, v in update.items() if k != "index"}
                update_item(case_id, index, updates)

    # Re-read the case after updates
    case = load_case(case_id)
    if case is None:
        return {"error": "Failed to reload case after update."}

    save_case(case)
    return case


@app.get("/api/cases/{case_id}/status")
def get_case_status(case_id: str) -> dict[str, Any]:
    """Get the completion status of a specific case.

    Returns detailed status including per-category completion, overdue items,
    and upcoming deadlines.

    TODO: Add deadline computation relative to current date.
    TODO: Add urgency color coding (red/yellow/green).
    """
    case = load_case(case_id)
    if case is None:
        return {"error": f"Case not found: {case_id}"}

    checklist = case.get("checklist", [])
    total = len(checklist)
    completed = sum(1 for item in checklist if item.get("completed"))

    # Per-category breakdown
    categories: dict[str, dict] = {}
    for item in checklist:
        cat = item.get("category", "General")
        if cat not in categories:
            categories[cat] = {"total": 0, "completed": 0}
        categories[cat]["total"] += 1
        if item.get("completed"):
            categories[cat]["completed"] += 1

    # Find overdue items
    # TODO: Implement actual date comparison using deadline_date field
    overdue_items = [
        item["label"]
        for item in checklist
        if not item.get("completed") and item.get("deadline_date")
    ]

    return {
        "case_id": case_id,
        "status": case.get("status", "Unknown"),
        "completion": {
            "total": total,
            "completed": completed,
            "pct": round((completed / total) * 100) if total > 0 else 0,
        },
        "categories": categories,
        "overdue_items": overdue_items,
    }
