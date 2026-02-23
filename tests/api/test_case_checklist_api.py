"""Tests for case-checklist/app/api.py — FastAPI endpoints."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

_TOOL_DIR = str(Path(__file__).resolve().parent.parent.parent / "case-checklist")


@pytest.fixture(autouse=True)
def _isolate_data(tmp_path):
    sys.path.insert(0, _TOOL_DIR)
    for k in list(sys.modules.keys()):
        if k == "app" or k.startswith("app."):
            del sys.modules[k]

    import app.checklists as checklists_mod

    data_dir = tmp_path / "cases"
    data_dir.mkdir()
    with patch.object(checklists_mod, "DATA_DIR", data_dir):
        yield

    try:
        sys.path.remove(_TOOL_DIR)
    except ValueError:
        pass


@pytest.fixture()
def client():
    from app.api import app as _app
    return TestClient(_app)


# ── Case types ────────────────────────────────────────────────────────────


def test_list_case_types(client):
    resp = client.get("/api/case-types")
    assert resp.status_code == 200
    types = resp.json()
    assert isinstance(types, list)
    assert len(types) > 0


# ── Case CRUD ─────────────────────────────────────────────────────────────


def test_create_case(client):
    case_types = client.get("/api/case-types").json()
    first_type = case_types[0]
    resp = client.post("/api/cases", json={
        "client_name": "Maria Garcia",
        "case_type": first_type,
        "a_number": "123-456-789",
        "attorney": "John Smith",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["client_name"] == "Maria Garcia"
    assert data["case_type"] == first_type
    assert "items" in data
    assert "progress" in data


def test_create_case_invalid_type(client):
    resp = client.post("/api/cases", json={
        "client_name": "Test",
        "case_type": "Totally Made Up Case Type",
    })
    assert resp.status_code == 400


def test_list_cases_empty(client):
    resp = client.get("/api/cases")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_case(client):
    case_types = client.get("/api/case-types").json()
    create = client.post("/api/cases", json={
        "client_name": "Test Client",
        "case_type": case_types[0],
    })
    case_id = create.json()["id"]

    resp = client.get(f"/api/cases/{case_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == case_id


def test_get_nonexistent_case(client):
    assert client.get("/api/cases/nope").status_code == 404


def test_delete_case(client):
    case_types = client.get("/api/case-types").json()
    create = client.post("/api/cases", json={
        "client_name": "Delete Me",
        "case_type": case_types[0],
    })
    case_id = create.json()["id"]

    del_resp = client.delete(f"/api/cases/{case_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deleted"

    assert client.get(f"/api/cases/{case_id}").status_code == 404


def test_delete_nonexistent_case(client):
    assert client.delete("/api/cases/nope").status_code == 404


# ── Filtering ─────────────────────────────────────────────────────────────


def test_filter_by_status(client):
    case_types = client.get("/api/case-types").json()
    client.post("/api/cases", json={"client_name": "A", "case_type": case_types[0]})
    resp = client.get("/api/cases?status=Active")
    assert resp.status_code == 200
    cases = resp.json()
    assert all(c.get("status") == "Active" for c in cases)


def test_filter_by_case_type(client):
    case_types = client.get("/api/case-types").json()
    client.post("/api/cases", json={"client_name": "A", "case_type": case_types[0]})
    client.post("/api/cases", json={"client_name": "B", "case_type": case_types[0]})
    resp = client.get(f"/api/cases?case_type={case_types[0]}")
    assert resp.status_code == 200
    cases = resp.json()
    assert all(c["case_type"] == case_types[0] for c in cases)


# ── Checklist item updates ────────────────────────────────────────────────


def test_update_item_complete(client):
    case_types = client.get("/api/case-types").json()
    create = client.post("/api/cases", json={
        "client_name": "Update Test",
        "case_type": case_types[0],
    })
    case = create.json()
    case_id = case["id"]
    items = case.get("items", [])

    if not items:
        pytest.skip("No checklist items in template")

    item_id = items[0]["id"]
    resp = client.put(f"/api/cases/{case_id}/items/{item_id}", json={
        "is_completed": True,
        "notes": "Done",
    })
    assert resp.status_code == 200
    updated_items = resp.json()["items"]
    matched = next(i for i in updated_items if i["id"] == item_id)
    assert matched["is_completed"] is True
    assert matched["notes"] == "Done"


def test_update_item_no_updates(client):
    """Empty update payload should 400."""
    case_types = client.get("/api/case-types").json()
    create = client.post("/api/cases", json={"client_name": "T", "case_type": case_types[0]})
    case_id = create.json()["id"]
    items = create.json().get("items", [])
    if not items:
        pytest.skip("No items")
    item_id = items[0]["id"]
    resp = client.put(f"/api/cases/{case_id}/items/{item_id}", json={})
    assert resp.status_code == 400


def test_add_custom_item(client):
    case_types = client.get("/api/case-types").json()
    create = client.post("/api/cases", json={"client_name": "T", "case_type": case_types[0]})
    case_id = create.json()["id"]

    resp = client.post(f"/api/cases/{case_id}/items", json={
        "title": "Custom task",
        "category": "Filing",
    })
    assert resp.status_code == 201
    items = resp.json()["items"]
    assert any(i["title"] == "Custom task" for i in items)


def test_get_progress(client):
    case_types = client.get("/api/case-types").json()
    create = client.post("/api/cases", json={"client_name": "T", "case_type": case_types[0]})
    case_id = create.json()["id"]

    resp = client.get(f"/api/cases/{case_id}/progress")
    assert resp.status_code == 200
    data = resp.json()
    assert "case_id" in data
    assert "status" in data
