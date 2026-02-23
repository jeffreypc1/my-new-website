"""Tests for cover-letters/app/api.py — FastAPI endpoints."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

_TOOL_DIR = str(Path(__file__).resolve().parent.parent.parent / "cover-letters")


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


# ── Templates ─────────────────────────────────────────────────────────────


def test_list_templates(client):
    resp = client.get("/api/templates")
    assert resp.status_code == 200
    templates = resp.json()
    assert isinstance(templates, list)
    assert len(templates) > 0
    for t in templates:
        assert "case_type" in t


def test_get_valid_template(client):
    templates = client.get("/api/templates").json()
    case_type = templates[0]["case_type"]
    resp = client.get(f"/api/templates/{case_type}")
    assert resp.status_code == 200


def test_get_unknown_template(client):
    resp = client.get("/api/templates/NonExistentType")
    assert resp.status_code == 404


# ── Generate ──────────────────────────────────────────────────────────────


def test_generate_cover_letter(client):
    templates = client.get("/api/templates").json()
    case_type = templates[0]["case_type"]
    resp = client.post("/api/generate", json={
        "case_type": case_type,
        "client_name": "Maria Garcia",
        "a_number": "123-456-789",
        "enclosed_docs": [
            {"name": "Form I-589", "description": "Application for Asylum"},
        ],
        "attorney_name": "Jane Smith",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "text" in data
    assert "Maria Garcia" in data["text"]


def test_generate_minimal(client):
    templates = client.get("/api/templates").json()
    case_type = templates[0]["case_type"]
    resp = client.post("/api/generate", json={
        "case_type": case_type,
        "client_name": "Test",
    })
    assert resp.status_code == 200
    assert "text" in resp.json()


def test_export_docx(client):
    templates = client.get("/api/templates").json()
    case_type = templates[0]["case_type"]
    resp = client.post("/api/export/docx", json={
        "case_type": case_type,
        "client_name": "Test Client",
    })
    assert resp.status_code == 200
    assert "wordprocessingml" in resp.headers["content-type"]
    assert len(resp.content) > 0


# ── Draft CRUD ────────────────────────────────────────────────────────────


def test_draft_lifecycle(client):
    templates = client.get("/api/templates").json()
    case_type = templates[0]["case_type"]

    # Save
    save_resp = client.post("/api/drafts", json={
        "draft_id": "test-draft-01",
        "case_type": case_type,
        "client": {"name": "Test"},
        "attorney": {"name": "Attorney"},
    })
    assert save_resp.status_code == 200

    # List
    list_resp = client.get("/api/drafts")
    assert len(list_resp.json()) == 1

    # Get
    get_resp = client.get("/api/drafts/test-draft-01")
    assert get_resp.status_code == 200

    # Delete
    del_resp = client.delete("/api/drafts/test-draft-01")
    assert del_resp.status_code == 200

    # Confirm deleted
    assert client.get("/api/drafts/test-draft-01").status_code == 404


def test_get_nonexistent_draft(client):
    assert client.get("/api/drafts/nope").status_code == 404


def test_delete_nonexistent_draft(client):
    assert client.delete("/api/drafts/nope").status_code == 404
