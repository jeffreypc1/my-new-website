"""Tests for brief-builder/app/api.py — FastAPI endpoints."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

_TOOL_DIR = str(Path(__file__).resolve().parent.parent.parent / "brief-builder")


@pytest.fixture(autouse=True)
def _isolate_drafts(tmp_path):
    sys.path.insert(0, _TOOL_DIR)
    for k in list(sys.modules.keys()):
        if k == "app" or k.startswith("app."):
            del sys.modules[k]

    import app.drafts as drafts_mod

    data_dir = tmp_path / "drafts"
    data_dir.mkdir()
    with patch.object(drafts_mod, "DATA_DIR", data_dir):
        yield

    try:
        sys.path.remove(_TOOL_DIR)
    except ValueError:
        pass


@pytest.fixture()
def client():
    from app.api import app as _app
    return TestClient(_app)


# ── Brief types & sections ────────────────────────────────────────────────


def test_list_brief_types(client):
    resp = client.get("/api/brief-types")
    assert resp.status_code == 200
    types = resp.json()
    assert isinstance(types, list)
    assert len(types) > 0
    assert "Asylum Merits Brief" in types


def test_get_sections_valid(client):
    resp = client.get("/api/sections/Asylum Merits Brief")
    assert resp.status_code == 200
    sections = resp.json()
    assert isinstance(sections, list)


# ── Generate ──────────────────────────────────────────────────────────────


def test_generate_brief(client):
    payload = {
        "brief_type": "Asylum Merits Brief",
        "case_info": {
            "client_name": "Maria Garcia",
            "a_number": "123-456-789",
            "court_or_office": "Los Angeles",
            "ij_name": "Smith",
            "hearing_date": "2024-06-01",
        },
        "sections": [
            {
                "section_key": "statement_of_facts",
                "heading": "Statement of Facts",
                "body": "The respondent arrived in 2019.",
                "citations": [],
            }
        ],
    }
    resp = client.post("/api/generate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["brief_type"] == "Asylum Merits Brief"
    assert data["case_info"]["client_name"] == "Maria Garcia"
    assert len(data["sections"]) == 1
    assert data["sections"][0]["heading"] == "Statement of Facts"


def test_generate_empty_sections(client):
    payload = {
        "brief_type": "Motion to Reopen",
        "case_info": {"client_name": "Test"},
        "sections": [],
    }
    resp = client.post("/api/generate", json=payload)
    assert resp.status_code == 200
    assert resp.json()["sections"] == []


# ── Export docx ───────────────────────────────────────────────────────────


def test_export_docx_returns_bytes(client):
    payload = {
        "brief_type": "Asylum Merits Brief",
        "case_info": {"client_name": "Test", "a_number": ""},
        "sections": [
            {
                "section_key": "intro",
                "heading": "Introduction",
                "body": "This brief is submitted on behalf of respondent.",
                "citations": ["Matter of Acosta"],
            }
        ],
    }
    resp = client.post("/api/export/docx", json=payload)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert len(resp.content) > 0


# ── Draft CRUD ────────────────────────────────────────────────────────────


def test_create_draft(client):
    payload = {
        "brief_type": "Asylum Merits Brief",
        "case_info": {"client_name": "Test"},
        "section_content": {"intro": "Some text"},
    }
    resp = client.post("/api/drafts", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["brief_type"] == "Asylum Merits Brief"


def test_list_drafts_empty(client):
    resp = client.get("/api/drafts")
    assert resp.status_code == 200
    assert resp.json() == []


def test_draft_round_trip(client):
    # Create
    create_resp = client.post("/api/drafts", json={
        "brief_type": "Bond Brief",
        "case_info": {"client_name": "Jane"},
        "section_content": {"intro": "Hello"},
    })
    draft_id = create_resp.json()["id"]

    # Get
    get_resp = client.get(f"/api/drafts/{draft_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["brief_type"] == "Bond Brief"

    # List
    list_resp = client.get("/api/drafts")
    assert len(list_resp.json()) == 1

    # Delete
    del_resp = client.delete(f"/api/drafts/{draft_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True

    # Verify gone
    assert client.get(f"/api/drafts/{draft_id}").status_code == 404


def test_get_nonexistent_draft(client):
    assert client.get("/api/drafts/nope").status_code == 404


def test_delete_nonexistent_draft(client):
    assert client.delete("/api/drafts/nope").status_code == 404
