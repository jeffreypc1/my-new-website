"""Tests for legal-research/app/api.py — FastAPI endpoints."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

_TOOL_DIR = str(Path(__file__).resolve().parent.parent.parent / "legal-research")


@pytest.fixture(autouse=True)
def _isolate_data(tmp_path):
    sys.path.insert(0, _TOOL_DIR)
    for k in list(sys.modules.keys()):
        if k == "app" or k.startswith("app."):
            del sys.modules[k]

    import app.case_law as case_law_mod

    data_dir = tmp_path / "collections"
    data_dir.mkdir()
    with patch.object(case_law_mod, "DATA_DIR", data_dir):
        yield

    try:
        sys.path.remove(_TOOL_DIR)
    except ValueError:
        pass


@pytest.fixture()
def client():
    from app.api import app as _app
    return TestClient(_app)


# ── Search & topics ───────────────────────────────────────────────────────


def test_list_topics(client):
    resp = client.get("/api/topics")
    assert resp.status_code == 200
    topics = resp.json()
    assert isinstance(topics, list)
    assert len(topics) > 0


def test_search_returns_results(client):
    resp = client.get("/api/search?q=asylum")
    assert resp.status_code == 200
    results = resp.json()
    assert isinstance(results, list)


def test_search_with_topic_filter(client):
    topics = client.get("/api/topics").json()
    resp = client.get(f"/api/search?q=matter&topics={topics[0]}")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_search_requires_query(client):
    resp = client.get("/api/search")
    assert resp.status_code == 422


def test_search_respects_limit(client):
    resp = client.get("/api/search?q=a&n=2")
    assert resp.status_code == 200
    assert len(resp.json()) <= 2


# ── Decision lookup ───────────────────────────────────────────────────────


def test_get_known_decision(client):
    resp = client.get("/api/decisions/matter-of-acosta")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Matter of Acosta"
    assert "citation" in data
    assert "holding" in data


def test_get_unknown_decision(client):
    assert client.get("/api/decisions/fake-case-xyz").status_code == 404


# ── Collections CRUD ──────────────────────────────────────────────────────


def test_create_collection(client):
    resp = client.post("/api/collections", json={
        "case_name": "Matter of Garcia",
        "a_number": "123-456",
        "decisions": [
            {
                "name": "Matter of Acosta",
                "citation": "19 I&N Dec. 211",
                "court": "BIA",
                "date": "1985-03-01",
                "holding": "Defines PSG",
                "topics": ["PSG"],
            }
        ],
        "notes": "Key PSG cases",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["case_name"] == "Matter of Garcia"
    assert len(data["decisions"]) == 1
    assert "id" in data


def test_list_collections_empty(client):
    resp = client.get("/api/collections")
    assert resp.status_code == 200
    assert resp.json() == []


def test_collection_lifecycle(client):
    # Create
    create = client.post("/api/collections", json={
        "case_name": "Test Case",
        "decisions": [],
        "notes": "",
    })
    assert create.status_code == 200
    coll_id = create.json()["id"]

    # List
    list_resp = client.get("/api/collections")
    assert len(list_resp.json()) == 1

    # Get
    get_resp = client.get(f"/api/collections/{coll_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == coll_id

    # Delete
    del_resp = client.delete(f"/api/collections/{coll_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deleted"

    # Confirm gone
    assert client.get(f"/api/collections/{coll_id}").status_code == 404


def test_get_nonexistent_collection(client):
    assert client.get("/api/collections/nope").status_code == 404


def test_delete_nonexistent_collection(client):
    assert client.delete("/api/collections/nope").status_code == 404
