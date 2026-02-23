"""Tests for declaration-drafter/app/api.py — FastAPI endpoints."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

_TOOL_DIR = str(Path(__file__).resolve().parent.parent.parent / "declaration-drafter")


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


# ── Declaration types & prompts ───────────────────────────────────────────


def test_list_declaration_types(client):
    resp = client.get("/api/declaration-types")
    assert resp.status_code == 200
    types = resp.json()
    assert isinstance(types, list)
    assert len(types) > 0


def test_get_prompts_valid(client):
    types = client.get("/api/declaration-types").json()
    resp = client.get(f"/api/prompts/{types[0]}")
    assert resp.status_code == 200
    sections = resp.json()
    assert isinstance(sections, list)


def test_get_prompts_unknown(client):
    resp = client.get("/api/prompts/FakeDeclarationType")
    assert resp.status_code == 404


# ── Generate ──────────────────────────────────────────────────────────────


def test_generate_declaration(client):
    types = client.get("/api/declaration-types").json()
    first_type = types[0]
    resp = client.post("/api/generate", json={
        "declaration_type": first_type,
        "declarant": {
            "name": "Maria Garcia",
            "country_of_origin": "Guatemala",
            "language": "Spanish",
            "a_number": "123-456-789",
            "interpreter_name": "Carlos Lopez",
        },
        "answers": {
            "background": "I was born in Guatemala City.",
        },
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["declarant_name"] == "Maria Garcia"
    assert data["declaration_type"] == first_type
    assert "paragraph_count" in data


def test_generate_minimal(client):
    types = client.get("/api/declaration-types").json()
    resp = client.post("/api/generate", json={
        "declaration_type": types[0],
        "declarant": {"name": "Test"},
        "answers": {},
    })
    assert resp.status_code == 200


# ── Export docx ───────────────────────────────────────────────────────────


def test_export_docx(client):
    types = client.get("/api/declaration-types").json()
    resp = client.post("/api/export/docx", json={
        "declaration_type": types[0],
        "declarant": {
            "name": "Test Person",
            "country_of_origin": "El Salvador",
            "language": "Spanish",
            "a_number": "",
            "interpreter_name": "Jane",
        },
        "answers": {"background": "I fled my country."},
    })
    assert resp.status_code == 200
    assert "wordprocessingml" in resp.headers["content-type"]
    assert len(resp.content) > 0


# ── Draft CRUD ────────────────────────────────────────────────────────────


def test_draft_lifecycle(client):
    types = client.get("/api/declaration-types").json()

    # Create
    create = client.post("/api/drafts", json={
        "declaration_type": types[0],
        "declarant": {"name": "Test"},
        "answers": {"q1": "answer"},
    })
    assert create.status_code == 200
    draft_id = create.json()["id"]

    # List
    assert len(client.get("/api/drafts").json()) == 1

    # Get
    assert client.get(f"/api/drafts/{draft_id}").status_code == 200

    # Delete
    assert client.delete(f"/api/drafts/{draft_id}").status_code == 200
    assert client.get(f"/api/drafts/{draft_id}").status_code == 404


def test_get_nonexistent_draft(client):
    assert client.get("/api/drafts/nope").status_code == 404
