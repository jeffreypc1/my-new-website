"""Tests for shared/attorney_store.py — attorney CRUD operations."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import shared.attorney_store as attorney_mod


@pytest.fixture(autouse=True)
def _isolate_attorney_files(tmp_path):
    """Redirect attorney file paths to tmp_path for every test."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    with patch.object(attorney_mod, "CONFIG_DIR", config_dir), \
         patch.object(attorney_mod, "ATTORNEYS_FILE", config_dir / "attorneys.json"):
        yield


# ── load_attorneys ───────────────────────────────────────────────────────


class TestLoadAttorneys:
    def test_empty_when_no_file(self):
        assert attorney_mod.load_attorneys() == []

    def test_loads_valid_list(self):
        data = [{"id": "abc", "name": "Jane Doe"}]
        attorney_mod.ATTORNEYS_FILE.write_text(json.dumps(data))
        assert attorney_mod.load_attorneys() == data

    def test_returns_empty_on_corrupt_json(self):
        attorney_mod.ATTORNEYS_FILE.write_text("BAD JSON{{{")
        assert attorney_mod.load_attorneys() == []

    def test_returns_empty_if_not_a_list(self):
        attorney_mod.ATTORNEYS_FILE.write_text(json.dumps({"not": "a list"}))
        assert attorney_mod.load_attorneys() == []


# ── save_attorneys ───────────────────────────────────────────────────────


class TestSaveAttorneys:
    def test_creates_file(self):
        data = [{"id": "1", "name": "Test"}]
        attorney_mod.save_attorneys(data)
        assert attorney_mod.ATTORNEYS_FILE.exists()
        loaded = json.loads(attorney_mod.ATTORNEYS_FILE.read_text())
        assert loaded == data

    def test_round_trip(self):
        data = [
            {"id": "a1", "name": "Alice", "bar": "12345"},
            {"id": "b2", "name": "Bob", "bar": "67890"},
        ]
        attorney_mod.save_attorneys(data)
        assert attorney_mod.load_attorneys() == data


# ── get_attorney_by_id ───────────────────────────────────────────────────


class TestGetAttorneyById:
    def test_found(self):
        data = [
            {"id": "a1", "name": "Alice"},
            {"id": "b2", "name": "Bob"},
        ]
        attorney_mod.save_attorneys(data)
        result = attorney_mod.get_attorney_by_id("b2")
        assert result is not None
        assert result["name"] == "Bob"

    def test_not_found(self):
        attorney_mod.save_attorneys([{"id": "a1", "name": "Alice"}])
        assert attorney_mod.get_attorney_by_id("nonexistent") is None

    def test_empty_store(self):
        assert attorney_mod.get_attorney_by_id("any") is None


# ── new_attorney_id ──────────────────────────────────────────────────────


class TestNewAttorneyId:
    def test_returns_string(self):
        aid = attorney_mod.new_attorney_id()
        assert isinstance(aid, str)

    def test_length_is_8(self):
        assert len(attorney_mod.new_attorney_id()) == 8

    def test_uniqueness(self):
        ids = {attorney_mod.new_attorney_id() for _ in range(100)}
        assert len(ids) == 100
