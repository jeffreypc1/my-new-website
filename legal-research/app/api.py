"""FastAPI backend for the Legal Research tool.

Provides endpoints for searching indexed case law and BIA decisions,
retrieving full decision text, browsing legal topics, and saving
collections of relevant decisions for a case.

Part of the O'Brien Immigration Law tool suite.
"""

from typing import Any

from fastapi import FastAPI, Query
from pydantic import BaseModel

from app.case_law import (
    KEY_DECISIONS,
    LEGAL_TOPICS,
    CaseLaw,
    get_by_citation,
    search_decisions,
)

app = FastAPI(title="Legal Research API")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class CollectionItem(BaseModel):
    """A single decision reference within a saved collection."""

    decision_key: str
    citation: str
    relevance_note: str = ""


class CreateCollectionRequest(BaseModel):
    """Payload for saving a collection of decisions for a case."""

    case_name: str
    a_number: str = ""
    decisions: list[CollectionItem]
    notes: str = ""


# ---------------------------------------------------------------------------
# In-memory storage for saved collections
# TODO: Persist collections to JSON files in data/ directory.
# ---------------------------------------------------------------------------

_collections: list[dict[str, Any]] = []


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

    TODO: Implement semantic search using ChromaDB vector store.
    TODO: Add circuit-specific filtering (e.g. 9th Circuit only).
    TODO: Add date range filtering.
    TODO: Support Boolean operators (AND, OR, NOT).
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

    TODO: Load full decision text from indexed documents.
    TODO: Return proper 404 HTTPException when not found.
    """
    decision = KEY_DECISIONS.get(decision_id)
    if decision is None:
        return {"error": f"Decision not found: {decision_id}"}
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
    """List all legal topics available for filtering.

    Returns the standard immigration law topics: asylum, withholding, CAT,
    particular social group, nexus, credibility, firm resettlement, one-year bar.
    """
    return LEGAL_TOPICS


@app.post("/api/collections")
def create_collection(request: CreateCollectionRequest) -> dict[str, Any]:
    """Save a collection of relevant decisions for a case.

    Stores the collection in memory (for now) and returns the saved
    collection with its assigned ID.

    TODO: Persist collections to JSON files in data/ directory.
    TODO: Add update and delete endpoints.
    TODO: Associate collections with case IDs from the case-checklist tool.
    """
    collection_id = len(_collections) + 1
    collection = {
        "id": collection_id,
        "case_name": request.case_name,
        "a_number": request.a_number,
        "decisions": [d.model_dump() for d in request.decisions],
        "notes": request.notes,
    }
    _collections.append(collection)
    return collection
