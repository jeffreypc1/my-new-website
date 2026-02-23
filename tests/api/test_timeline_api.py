"""Tests for timeline-builder/app/api.py — FastAPI endpoints."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

_TOOL_DIR = str(Path(__file__).resolve().parent.parent.parent / "timeline-builder")


@pytest.fixture(autouse=True)
def _isolate_data(tmp_path):
    sys.path.insert(0, _TOOL_DIR)
    for k in list(sys.modules.keys()):
        if k == "app" or k.startswith("app."):
            del sys.modules[k]

    import app.events as events_mod

    data_dir = tmp_path / "timelines"
    data_dir.mkdir()
    with patch.object(events_mod, "DATA_DIR", data_dir):
        yield

    try:
        sys.path.remove(_TOOL_DIR)
    except ValueError:
        pass


@pytest.fixture()
def client():
    from app.api import app as _app
    return TestClient(_app)


# ── Timeline CRUD ─────────────────────────────────────────────────────────


def test_list_timelines_empty(client):
    resp = client.get("/api/timelines")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_timeline(client):
    resp = client.post("/api/timelines", json={
        "case_name": "Smith v. USCIS",
        "client_name": "Jane Smith",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["client_name"] == "Jane Smith"
    assert data["case_name"] == "Smith v. USCIS"
    assert "id" in data
    assert data["events"] == []


def test_get_timeline(client):
    create = client.post("/api/timelines", json={"client_name": "Test"})
    tl_id = create.json()["id"]
    resp = client.get(f"/api/timelines/{tl_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == tl_id


def test_get_nonexistent_timeline(client):
    assert client.get("/api/timelines/nope").status_code == 404


def test_delete_timeline(client):
    create = client.post("/api/timelines", json={"client_name": "Del"})
    tl_id = create.json()["id"]
    del_resp = client.delete(f"/api/timelines/{tl_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True
    assert client.get(f"/api/timelines/{tl_id}").status_code == 404


def test_delete_nonexistent_timeline(client):
    assert client.delete("/api/timelines/nope").status_code == 404


# ── Event CRUD ────────────────────────────────────────────────────────────


@pytest.fixture()
def timeline_id(client):
    resp = client.post("/api/timelines", json={"client_name": "Event Test"})
    return resp.json()["id"]


def _first_category():
    from app.events import EVENT_CATEGORIES
    return list(EVENT_CATEGORIES.keys())[0]


def test_add_event(client, timeline_id):
    cat = _first_category()
    resp = client.post(f"/api/timelines/{timeline_id}/events", json={
        "title": "Entered US",
        "date_text": "March 2019",
        "category": cat,
        "description": "Arrived at the border",
    })
    assert resp.status_code == 201
    events = resp.json()["events"]
    assert any(e["title"] == "Entered US" for e in events)


def test_add_event_invalid_category(client, timeline_id):
    resp = client.post(f"/api/timelines/{timeline_id}/events", json={
        "title": "Test",
        "date_text": "2020",
        "category": "FakeCategory",
    })
    assert resp.status_code == 422


def test_add_event_to_nonexistent_timeline(client):
    cat = _first_category()
    resp = client.post("/api/timelines/nope/events", json={
        "title": "Test",
        "date_text": "2020",
        "category": cat,
    })
    assert resp.status_code == 404


def test_update_event(client, timeline_id):
    cat = _first_category()
    add = client.post(f"/api/timelines/{timeline_id}/events", json={
        "title": "Original",
        "date_text": "2019",
        "category": cat,
    })
    event_id = add.json()["events"][0]["id"]

    update = client.put(f"/api/timelines/{timeline_id}/events/{event_id}", json={
        "title": "Updated",
        "description": "New desc",
    })
    assert update.status_code == 200
    events = update.json()["events"]
    matched = next(e for e in events if e["id"] == event_id)
    assert matched["title"] == "Updated"
    assert matched["description"] == "New desc"


def test_delete_event(client, timeline_id):
    cat = _first_category()
    add = client.post(f"/api/timelines/{timeline_id}/events", json={
        "title": "To Delete",
        "date_text": "2020",
        "category": cat,
    })
    event_id = add.json()["events"][0]["id"]

    del_resp = client.delete(f"/api/timelines/{timeline_id}/events/{event_id}")
    assert del_resp.status_code == 200
    events = del_resp.json()["events"]
    assert not any(e["id"] == event_id for e in events)


def test_delete_nonexistent_event(client, timeline_id):
    assert client.delete(f"/api/timelines/{timeline_id}/events/fake-id").status_code == 404


# ── Export ────────────────────────────────────────────────────────────────


def test_export_docx(client, timeline_id):
    cat = _first_category()
    client.post(f"/api/timelines/{timeline_id}/events", json={
        "title": "Arrived",
        "date_text": "2019",
        "category": cat,
    })
    resp = client.get(f"/api/timelines/{timeline_id}/export/docx")
    assert resp.status_code == 200
    assert "wordprocessingml" in resp.headers["content-type"]
    assert len(resp.content) > 0


def test_export_docx_nonexistent(client):
    assert client.get("/api/timelines/nope/export/docx").status_code == 404
