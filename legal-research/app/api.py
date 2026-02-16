"""FastAPI backend for the Legal Research tool.

Provides endpoints for searching indexed case law and BIA decisions,
retrieving full decision text, browsing legal topics, and managing
persistent collections of relevant decisions for a case.

Part of the O'Brien Immigration Law tool suite.
"""

from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from app.case_law import (
    KEY_DECISIONS,
    LEGAL_TOPICS,
    delete_collection,
    get_by_citation,
    list_collections,
    load_collection,
    new_collection_id,
    save_collection,
    search_decisions,
)

app = FastAPI(title="Legal Research API")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class CollectionDecision(BaseModel):
    """A single decision reference within a saved collection."""

    name: str = ""
    citation: str = ""
    court: str = ""
    date: str = ""
    holding: str = ""
    topics: list[str] = []


class CreateCollectionRequest(BaseModel):
    """Payload for saving a collection of decisions for a case."""

    case_name: str
    a_number: str = ""
    decisions: list[CollectionDecision]
    notes: str = ""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/api/search")
def search_case_law(
    q: str = Query(..., min_length=1, description="Search query"),
    topics: list[str] | None = Query(None, description="Filter by legal topics"),
    n: int = Query(20, ge=1, le=100, description="Number of results"),
) -> list[dict[str, Any]]:
    """Search indexed case law and BIA decisions.

    Returns matching decisions with name, citation, court, date, and holding.
    Supports free-text search with optional topic filtering.
    """
    results = search_decisions(q, topics=topics, limit=n)
    return [
        {
            "name": r.name,
            "citation": r.citation,
            "court": r.court,
            "date": r.date,
            "holding": r.holding,
            "topics": r.topics,
        }
        for r in results
    ]


@app.get("/api/decisions/{decision_id}")
def get_decision(decision_id: str) -> dict[str, Any]:
    """Get the full text and metadata of a specific decision.

    Args:
        decision_id: The decision key (e.g. "matter-of-acosta").

    Returns:
        Full decision record including name, citation, court, date,
        holding, full_text, and topics.
    """
    decision = KEY_DECISIONS.get(decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail=f"Decision not found: {decision_id}")
    return {
        "id": decision_id,
        "name": decision.name,
        "citation": decision.citation,
        "court": decision.court,
        "date": decision.date,
        "holding": decision.holding,
        "full_text": decision.full_text or "(Full text not yet indexed)",
        "topics": decision.topics,
    }


@app.get("/api/topics")
def list_topics() -> list[str]:
    """List all legal topics available for filtering."""
    return LEGAL_TOPICS


@app.post("/api/collections")
def create_collection(request: CreateCollectionRequest) -> dict[str, Any]:
    """Save a collection of relevant decisions for a case.

    Persists the collection to a JSON file in data/collections/ and
    returns the saved collection with its assigned ID.
    """
    collection_id = new_collection_id()
    decisions = [d.model_dump() for d in request.decisions]
    collection = save_collection(
        collection_id=collection_id,
        case_name=request.case_name,
        a_number=request.a_number,
        decisions=decisions,
        notes=request.notes,
    )
    return collection


@app.get("/api/collections")
def get_collections() -> list[dict[str, Any]]:
    """List all saved collections."""
    return list_collections()


@app.get("/api/collections/{collection_id}")
def get_collection(collection_id: str) -> dict[str, Any]:
    """Get a specific saved collection by ID."""
    collection = load_collection(collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail=f"Collection not found: {collection_id}")
    return collection


@app.delete("/api/collections/{collection_id}")
def remove_collection(collection_id: str) -> dict[str, str]:
    """Delete a saved collection by ID."""
    if not delete_collection(collection_id):
        raise HTTPException(status_code=404, detail=f"Collection not found: {collection_id}")
    return {"status": "deleted", "id": collection_id}
