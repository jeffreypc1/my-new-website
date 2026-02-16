"""FastAPI backend for the Timeline Builder tool."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.events import (
    EVENT_CATEGORIES,
    TimelineEvent,
    add_event,
    list_timelines,
    load_timeline,
    parse_approximate_date,
    save_timeline,
    sort_events,
)

app = FastAPI(title="Timeline Builder API")


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class EventIn(BaseModel):
    date_text: str
    description: str
    category: str
    location: str = ""
    evidence_ref: str = ""


class TimelineCreate(BaseModel):
    name: str
    client: str = ""


class EventUpdate(BaseModel):
    """Payload for PUT /api/timelines/{id}/events — full replacement list."""
    events: list[EventIn]


class ExportRequest(BaseModel):
    timeline_id: str


# ---------------------------------------------------------------------------
# Timeline CRUD
# ---------------------------------------------------------------------------

@app.get("/api/timelines")
def api_list_timelines() -> list[dict]:
    """Return summary info for all saved timelines."""
    return list_timelines()


@app.get("/api/timelines/{timeline_id}")
def api_get_timeline(timeline_id: str) -> dict:
    """Return the full timeline with events."""
    timeline = load_timeline(timeline_id)
    if not timeline.get("name"):
        raise HTTPException(status_code=404, detail="Timeline not found")
    return timeline


@app.post("/api/timelines")
def api_create_timeline(body: TimelineCreate) -> dict:
    """Create a new empty timeline and return it."""
    timeline_id = uuid.uuid4().hex[:12]
    timeline = {
        "id": timeline_id,
        "name": body.name,
        "client": body.client,
        "events": [],
    }
    save_timeline(timeline)
    return timeline


@app.put("/api/timelines/{timeline_id}/events")
def api_update_events(timeline_id: str, body: EventUpdate) -> dict:
    """Replace the full event list for a timeline.

    Each incoming event is parsed to generate a sortable date key, then the
    list is re-sorted chronologically and persisted.
    """
    timeline = load_timeline(timeline_id)
    if not timeline.get("name"):
        raise HTTPException(status_code=404, detail="Timeline not found")

    new_events = []
    for ev in body.events:
        if ev.category not in EVENT_CATEGORIES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid category '{ev.category}'. "
                       f"Must be one of: {', '.join(EVENT_CATEGORIES)}",
            )
        te = TimelineEvent(
            date_text=ev.date_text,
            date_sortable=parse_approximate_date(ev.date_text),
            description=ev.description,
            category=ev.category,
            location=ev.location,
            evidence_ref=ev.evidence_ref,
        )
        new_events.append(te.__dict__)

    timeline["events"] = new_events
    sort_events(timeline)
    save_timeline(timeline)
    return timeline


# ---------------------------------------------------------------------------
# Export endpoints
# ---------------------------------------------------------------------------

@app.post("/api/export/docx")
def api_export_docx(body: ExportRequest):
    """Export a timeline as a Word document with a chronological table.

    Returns the .docx file bytes as an attachment.
    """
    timeline = load_timeline(body.timeline_id)
    if not timeline.get("name"):
        raise HTTPException(status_code=404, detail="Timeline not found")

    # TODO: Build a python-docx Document with a table containing columns:
    #   Date | Event | Category | Location | Evidence
    # Return as StreamingResponse with media_type=
    #   "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    raise HTTPException(status_code=501, detail="DOCX export not yet implemented")


@app.post("/api/export/pdf")
def api_export_pdf(body: ExportRequest):
    """Export a visual timeline as a PDF.

    Returns the PDF file bytes as an attachment.
    """
    timeline = load_timeline(body.timeline_id)
    if not timeline.get("name"):
        raise HTTPException(status_code=404, detail="Timeline not found")

    # TODO: Generate a visual timeline graphic (e.g. with matplotlib / reportlab)
    #   and return as StreamingResponse with media_type="application/pdf"
    raise HTTPException(status_code=501, detail="PDF export not yet implemented")
