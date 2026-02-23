"""Tests for shared/salesforce_client.py — helper functions and file I/O.

Focuses on pure-logic functions and file persistence that can be tested
without a live Salesforce connection. API-calling functions are tested
with mocks where practical.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import shared.salesforce_client as sf_mod


# ── _flatten_lc_record ───────────────────────────────────────────────────


class TestFlattenLcRecord:
    def test_strips_attributes(self):
        record = {"Id": "001", "Name": "Test", "attributes": {"type": "Legal_Case__c"}}
        result = sf_mod._flatten_lc_record(record)
        assert "attributes" not in result
        assert result["Id"] == "001"

    def test_flattens_relationship(self):
        record = {
            "Id": "001",
            "Primary_Attorney__r": {"Name": "Jane Doe"},
            "attributes": {"type": "Legal_Case__c"},
        }
        result = sf_mod._flatten_lc_record(record)
        assert result["Primary_Attorney__r_Name"] == "Jane Doe"
        assert "Primary_Attorney__r" not in result

    def test_removes_dict_without_name(self):
        record = {
            "Id": "001",
            "SomeRef__r": {"Type": "Unknown"},
            "attributes": {"type": "Legal_Case__c"},
        }
        result = sf_mod._flatten_lc_record(record)
        assert "SomeRef__r" not in result

    def test_multiple_relationships(self):
        record = {
            "Id": "001",
            "Primary_Attorney__r": {"Name": "Alice"},
            "Primary_Assistant__r": {"Name": "Bob"},
            "Hearing_Attorney__r": None,
            "attributes": {"type": "Legal_Case__c"},
        }
        result = sf_mod._flatten_lc_record(record)
        assert result["Primary_Attorney__r_Name"] == "Alice"
        assert result["Primary_Assistant__r_Name"] == "Bob"


# ── Active client persistence ────────────────────────────────────────────


class TestActiveClientPersistence:
    @pytest.fixture(autouse=True)
    def _isolate_path(self, tmp_path):
        path = tmp_path / "active_client.json"
        with patch.object(sf_mod, "_ACTIVE_CLIENT_PATH", path):
            yield

    def test_load_returns_none_when_missing(self):
        assert sf_mod.load_active_client() is None

    def test_save_and_load(self):
        record = {"Id": "003", "Name": "Test Client", "Customer_ID__c": "1234"}
        sf_mod.save_active_client(record)
        loaded = sf_mod.load_active_client()
        assert loaded["Name"] == "Test Client"
        assert loaded["Customer_ID__c"] == "1234"

    def test_clear(self):
        sf_mod.save_active_client({"Id": "003"})
        sf_mod.clear_active_client()
        assert sf_mod.load_active_client() is None

    def test_clear_when_no_file(self):
        sf_mod.clear_active_client()  # should not raise

    def test_corrupt_file_returns_none(self):
        sf_mod._ACTIVE_CLIENT_PATH.write_text("BAD JSON")
        assert sf_mod.load_active_client() is None


# ── Session persistence ──────────────────────────────────────────────────


class TestSessionPersistence:
    @pytest.fixture(autouse=True)
    def _isolate_session(self, tmp_path):
        path = tmp_path / ".sf_session.json"
        with patch.object(sf_mod, "_SF_SESSION_PATH", path):
            yield

    def test_save_session(self):
        mock_sf = MagicMock()
        mock_sf.session_id = "sess123"
        mock_sf.sf_instance = "na1.salesforce.com"
        sf_mod._save_session(mock_sf)
        data = json.loads(sf_mod._SF_SESSION_PATH.read_text())
        assert data["session_id"] == "sess123"
        assert data["sf_instance"] == "na1.salesforce.com"

    def test_restore_session_when_no_file(self):
        assert sf_mod._restore_session() is None


# ── DEFAULT_FIELDS ───────────────────────────────────────────────────────


class TestDefaultFields:
    def test_contains_core_fields(self):
        assert "Id" in sf_mod.DEFAULT_FIELDS
        assert "Customer_ID__c" in sf_mod.DEFAULT_FIELDS
        assert "FirstName" in sf_mod.DEFAULT_FIELDS
        assert "LastName" in sf_mod.DEFAULT_FIELDS
        assert "Email" in sf_mod.DEFAULT_FIELDS

    def test_no_duplicates(self):
        assert len(sf_mod.DEFAULT_FIELDS) == len(set(sf_mod.DEFAULT_FIELDS))
