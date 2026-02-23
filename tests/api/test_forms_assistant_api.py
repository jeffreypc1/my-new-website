"""Tests for forms-assistant/app/api.py — FastAPI endpoints."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

_TOOL_DIR = str(Path(__file__).resolve().parent.parent.parent / "forms-assistant")


@pytest.fixture(autouse=True)
def _isolate_drafts(tmp_path):
    sys.path.insert(0, _TOOL_DIR)
    for k in list(sys.modules.keys()):
        if k == "app" or k.startswith("app."):
            del sys.modules[k]

    import app.form_definitions as form_def_mod

    data_dir = tmp_path / "drafts"
    data_dir.mkdir()
    with patch.object(form_def_mod, "DATA_DIR", data_dir):
        yield

    try:
        sys.path.remove(_TOOL_DIR)
    except ValueError:
        pass


@pytest.fixture()
def client():
    from app.api import app as _app
    return TestClient(_app)


# ── Form listing ──────────────────────────────────────────────────────────


def test_list_forms(client):
    resp = client.get("/api/forms")
    assert resp.status_code == 200
    forms = resp.json()
    assert isinstance(forms, list)
    assert len(forms) > 0
    for f in forms:
        assert "form_id" in f
        assert "title" in f


def test_get_form_fields_valid(client):
    forms = client.get("/api/forms").json()
    form_id = forms[0]["form_id"]
    resp = client.get(f"/api/forms/{form_id}/fields")
    assert resp.status_code == 200
    data = resp.json()
    assert data["form_id"] == form_id
    assert "sections" in data


def test_get_form_fields_unknown(client):
    assert client.get("/api/forms/FAKE-999/fields").status_code == 404


# ── Validation ────────────────────────────────────────────────────────────


def test_validate_form_empty_data(client):
    forms = client.get("/api/forms").json()
    form_id = forms[0]["form_id"]
    resp = client.post(f"/api/forms/{form_id}/validate", json={"data": {}})
    assert resp.status_code == 200
    data = resp.json()
    assert "completeness" in data
    assert "field_errors" in data


def test_validate_form_unknown_id(client):
    resp = client.post("/api/forms/FAKE-999/validate", json={"data": {}})
    assert resp.status_code == 404


# ── Export ────────────────────────────────────────────────────────────────


def test_export_json(client):
    forms = client.get("/api/forms").json()
    form_id = forms[0]["form_id"]
    resp = client.post(f"/api/forms/{form_id}/export", json={
        "data": {"first_name": "Maria", "last_name": "Garcia"},
        "format": "json",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["form_id"] == form_id
    assert data["data"]["first_name"] == "Maria"


def test_export_unsupported_format(client):
    forms = client.get("/api/forms").json()
    form_id = forms[0]["form_id"]
    resp = client.post(f"/api/forms/{form_id}/export", json={
        "data": {},
        "format": "xlsx",
    })
    assert resp.status_code == 400


def test_export_unknown_form(client):
    resp = client.post("/api/forms/FAKE-999/export", json={"data": {}, "format": "json"})
    assert resp.status_code == 404
