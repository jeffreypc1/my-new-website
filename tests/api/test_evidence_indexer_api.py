"""Tests for evidence-indexer/app/api.py — FastAPI endpoints."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

_TOOL_DIR = str(Path(__file__).resolve().parent.parent.parent / "evidence-indexer")


@pytest.fixture(autouse=True)
def _isolate_data(tmp_path):
    sys.path.insert(0, _TOOL_DIR)
    for k in list(sys.modules.keys()):
        if k == "app" or k.startswith("app."):
            del sys.modules[k]

    import app.evidence as evidence_mod

    data_dir = tmp_path / "cases"
    data_dir.mkdir()
    with patch.object(evidence_mod, "DATA_DIR", data_dir):
        yield

    try:
        sys.path.remove(_TOOL_DIR)
    except ValueError:
        pass


@pytest.fixture()
def client():
    from app.api import app as _app
    return TestClient(_app)


# ── Categories ────────────────────────────────────────────────────────────


def test_get_categories(client):
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    cats = resp.json()
    assert isinstance(cats, list)
    assert "Identity Documents" in cats
    assert "Other" in cats


# ── Case CRUD ─────────────────────────────────────────────────────────────


def test_list_cases_empty(client):
    resp = client.get("/api/cases")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_case(client):
    resp = client.post("/api/cases", json={
        "client_name": "Maria Garcia",
        "a_number": "123-456-789",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["client_name"] == "Maria Garcia"
    assert data["documents"] == []
    assert "id" in data


def test_get_case(client):
    create = client.post("/api/cases", json={"client_name": "Test"})
    case_id = create.json()["id"]
    resp = client.get(f"/api/cases/{case_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == case_id


def test_get_nonexistent_case(client):
    assert client.get("/api/cases/nope").status_code == 404


def test_delete_case(client):
    create = client.post("/api/cases", json={"client_name": "Del"})
    case_id = create.json()["id"]
    resp = client.delete(f"/api/cases/{case_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    assert client.get(f"/api/cases/{case_id}").status_code == 404


def test_delete_nonexistent_case(client):
    assert client.delete("/api/cases/nope").status_code == 404


# ── Document CRUD ─────────────────────────────────────────────────────────


@pytest.fixture()
def case_id(client):
    resp = client.post("/api/cases", json={"client_name": "Doc Test"})
    return resp.json()["id"]


def test_add_document(client, case_id):
    resp = client.post(f"/api/cases/{case_id}/documents", json={
        "title": "Passport",
        "category": "Identity Documents",
        "page_count": 3,
    })
    assert resp.status_code == 200
    doc = resp.json()
    assert doc["title"] == "Passport"
    assert doc["exhibit_letter"] == "A"


def test_add_multiple_documents(client, case_id):
    client.post(f"/api/cases/{case_id}/documents", json={"title": "Doc A", "category": "Other"})
    client.post(f"/api/cases/{case_id}/documents", json={"title": "Doc B", "category": "Other"})
    case = client.get(f"/api/cases/{case_id}").json()
    letters = [d["exhibit_letter"] for d in case["documents"]]
    assert letters == ["A", "B"]


def test_add_document_to_nonexistent_case(client):
    resp = client.post("/api/cases/nope/documents", json={"title": "X", "category": "Other"})
    assert resp.status_code == 404


def test_update_document(client, case_id):
    add = client.post(f"/api/cases/{case_id}/documents", json={"title": "Old", "category": "Other"})
    doc_id = add.json()["doc_id"]
    resp = client.put(f"/api/cases/{case_id}/documents/{doc_id}", json={
        "title": "Updated",
        "page_count": 10,
    })
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"
    assert resp.json()["page_count"] == 10


def test_update_nonexistent_document(client, case_id):
    resp = client.put(f"/api/cases/{case_id}/documents/fake", json={"title": "X"})
    assert resp.status_code == 404


def test_remove_document(client, case_id):
    add = client.post(f"/api/cases/{case_id}/documents", json={"title": "Del", "category": "Other"})
    doc_id = add.json()["doc_id"]
    resp = client.delete(f"/api/cases/{case_id}/documents/{doc_id}")
    assert resp.status_code == 200
    case = client.get(f"/api/cases/{case_id}").json()
    assert len(case["documents"]) == 0


def test_remove_nonexistent_document(client, case_id):
    assert client.delete(f"/api/cases/{case_id}/documents/fake").status_code == 404


# ── Reorder ───────────────────────────────────────────────────────────────


def test_reorder_documents(client, case_id):
    client.post(f"/api/cases/{case_id}/documents", json={"title": "First", "category": "Other"})
    client.post(f"/api/cases/{case_id}/documents", json={"title": "Second", "category": "Other"})
    client.post(f"/api/cases/{case_id}/documents", json={"title": "Third", "category": "Other"})

    resp = client.post(f"/api/cases/{case_id}/reorder", json={"new_order": [2, 0, 1]})
    assert resp.status_code == 200
    docs = resp.json()
    assert docs[0]["title"] == "Third"
    assert docs[0]["exhibit_letter"] == "A"
    assert docs[1]["title"] == "First"
    assert docs[1]["exhibit_letter"] == "B"


def test_reorder_nonexistent_case(client):
    assert client.post("/api/cases/nope/reorder", json={"new_order": [0]}).status_code == 404


# ── Export ────────────────────────────────────────────────────────────────


def test_export_index_docx(client, case_id):
    client.post(f"/api/cases/{case_id}/documents", json={"title": "Passport", "category": "Identity Documents"})
    resp = client.post(f"/api/cases/{case_id}/export/index")
    assert resp.status_code == 200
    assert "wordprocessingml" in resp.headers["content-type"]
    assert len(resp.content) > 0


def test_export_index_nonexistent(client):
    assert client.post("/api/cases/nope/export/index").status_code == 404


def test_export_bundle_not_implemented(client, case_id):
    resp = client.post(f"/api/cases/{case_id}/export/bundle")
    assert resp.status_code == 200
    assert resp.json()["status"] == "not_implemented"
