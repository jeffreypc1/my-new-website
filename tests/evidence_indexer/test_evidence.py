"""Tests for evidence-indexer/app/evidence.py — exhibit lettering, CRUD, and index generation.

These tests cover the core business logic: exhibit letter assignment,
reordering, case persistence, and document management.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

# Patch DATA_DIR before importing the module so it doesn't create dirs at import time
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "evidence-indexer"))

import app.evidence as evidence_mod
from app.evidence import (
    EvidenceItem,
    _case_path,
    _exhibit_letter,
    _docs_to_items,
    add_document,
    auto_assign_letters,
    delete_case,
    generate_index,
    list_cases,
    load_case,
    new_case_id,
    remove_document,
    reorder_exhibits,
    save_case,
    update_document,
)


@pytest.fixture(autouse=True)
def _isolate_data_dir(tmp_path):
    """Redirect case storage to tmp_path for every test."""
    data_dir = tmp_path / "cases"
    data_dir.mkdir(parents=True)
    with patch.object(evidence_mod, "DATA_DIR", data_dir):
        yield


# ── Exhibit lettering ────────────────────────────────────────────────────


class TestExhibitLetter:
    def test_first_letter(self):
        assert _exhibit_letter(0) == "A"

    def test_last_single_letter(self):
        assert _exhibit_letter(25) == "Z"

    def test_double_letter_aa(self):
        assert _exhibit_letter(26) == "AA"

    def test_double_letter_ab(self):
        assert _exhibit_letter(27) == "AB"

    def test_double_letter_az(self):
        assert _exhibit_letter(51) == "AZ"

    def test_double_letter_ba(self):
        assert _exhibit_letter(52) == "BA"

    def test_sequence_is_correct(self):
        letters = [_exhibit_letter(i) for i in range(30)]
        expected_start = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ["AA", "AB", "AC", "AD"]
        assert letters == expected_start


class TestAutoAssignLetters:
    def test_assigns_sequential_letters(self):
        items = [
            EvidenceItem(exhibit_letter="", title="Doc 1", category="Other"),
            EvidenceItem(exhibit_letter="", title="Doc 2", category="Other"),
            EvidenceItem(exhibit_letter="", title="Doc 3", category="Other"),
        ]
        result = auto_assign_letters(items)
        assert [i.exhibit_letter for i in result] == ["A", "B", "C"]

    def test_preserves_manual_letters(self):
        items = [
            EvidenceItem(exhibit_letter="X", title="Doc 1", category="Other"),
            EvidenceItem(exhibit_letter="", title="Doc 2", category="Other"),
        ]
        result = auto_assign_letters(items)
        assert result[0].exhibit_letter == "X"
        assert result[1].exhibit_letter == "B"

    def test_empty_list(self):
        assert auto_assign_letters([]) == []


class TestReorderExhibits:
    def test_reorder(self):
        items = [
            EvidenceItem(exhibit_letter="A", title="First", category="Other"),
            EvidenceItem(exhibit_letter="B", title="Second", category="Other"),
            EvidenceItem(exhibit_letter="C", title="Third", category="Other"),
        ]
        result = reorder_exhibits(items, [2, 0, 1])
        assert [i.title for i in result] == ["Third", "First", "Second"]
        assert [i.exhibit_letter for i in result] == ["A", "B", "C"]

    def test_out_of_range_indices_skipped(self):
        items = [
            EvidenceItem(exhibit_letter="A", title="First", category="Other"),
            EvidenceItem(exhibit_letter="B", title="Second", category="Other"),
        ]
        result = reorder_exhibits(items, [1, 99, 0])
        assert len(result) == 2
        assert [i.title for i in result] == ["Second", "First"]


# ── Index generation ─────────────────────────────────────────────────────


class TestGenerateIndex:
    def test_generates_rows(self):
        items = [
            EvidenceItem(
                exhibit_letter="A", title="Passport", category="Identity Documents",
                page_count=3, description="Copy of passport"
            ),
            EvidenceItem(
                exhibit_letter="B", title="Declaration", category="Declaration / Affidavit",
                page_count=10, description=""
            ),
        ]
        rows = generate_index(items)
        assert len(rows) == 2
        assert rows[0]["exhibit_letter"] == "A"
        assert rows[0]["title"] == "Passport"
        assert rows[0]["page_count"] == 3
        assert rows[1]["category"] == "Declaration / Affidavit"

    def test_empty_items(self):
        assert generate_index([]) == []


# ── Case persistence ─────────────────────────────────────────────────────


class TestCasePersistence:
    def test_save_and_load(self):
        case = save_case("test-001", "Jane Doe", "123-456-789", [])
        loaded = load_case("test-001")
        assert loaded is not None
        assert loaded["client_name"] == "Jane Doe"
        assert loaded["a_number"] == "123-456-789"

    def test_load_nonexistent(self):
        assert load_case("does-not-exist") is None

    def test_save_preserves_created_at(self):
        save_case("test-002", "First", "111", [])
        first = load_case("test-002")
        created = first["created_at"]

        # Save again (update)
        save_case("test-002", "Updated", "111", [])
        second = load_case("test-002")
        assert second["created_at"] == created
        assert second["client_name"] == "Updated"

    def test_delete_case(self):
        save_case("test-003", "To Delete", "", [])
        assert delete_case("test-003") is True
        assert load_case("test-003") is None

    def test_delete_nonexistent(self):
        assert delete_case("nope") is False


class TestListCases:
    def test_empty(self):
        assert list_cases() == []

    def test_lists_cases_sorted_by_updated(self):
        from unittest.mock import patch as _patch
        from datetime import datetime as _dt

        # Use explicit timestamps to guarantee ordering
        with _patch.object(evidence_mod, "datetime") as mock_dt:
            mock_dt.now.return_value = _dt(2024, 1, 1, 10, 0, 0)
            mock_dt.fromisoformat = _dt.fromisoformat
            save_case("old", "Old Case", "", [])

        with _patch.object(evidence_mod, "datetime") as mock_dt:
            mock_dt.now.return_value = _dt(2024, 6, 1, 10, 0, 0)
            mock_dt.fromisoformat = _dt.fromisoformat
            save_case("new", "New Case", "", [])

        cases = list_cases()
        assert len(cases) == 2
        # Most recently updated first
        assert cases[0]["case_id"] == "new"

    def test_includes_document_count(self):
        docs = [
            {"doc_id": "d1", "title": "Doc 1", "category": "Other",
             "exhibit_letter": "A", "page_count": 1, "date_added": "2024-01-01"},
            {"doc_id": "d2", "title": "Doc 2", "category": "Other",
             "exhibit_letter": "B", "page_count": 2, "date_added": "2024-01-01"},
        ]
        save_case("with-docs", "Client", "", docs)
        cases = list_cases()
        assert cases[0]["document_count"] == 2


# ── Document management ──────────────────────────────────────────────────


class TestAddDocument:
    def test_add_to_case(self):
        save_case("case-add", "Client", "", [])
        doc = add_document("case-add", title="Passport", category="Identity Documents")
        assert doc is not None
        assert doc["title"] == "Passport"
        assert doc["exhibit_letter"] == "A"

        # Add another
        doc2 = add_document("case-add", title="Declaration", category="Declaration / Affidavit")
        assert doc2["exhibit_letter"] == "B"

    def test_add_to_nonexistent_case(self):
        assert add_document("nope", title="X", category="Other") is None


class TestRemoveDocument:
    def test_remove(self):
        save_case("case-rm", "Client", "", [])
        doc = add_document("case-rm", title="Passport", category="Other")
        doc2 = add_document("case-rm", title="Declaration", category="Other")

        result = remove_document("case-rm", doc["doc_id"])
        assert result is True

        loaded = load_case("case-rm")
        assert len(loaded["documents"]) == 1
        # Remaining doc should be reassigned to "A"
        assert loaded["documents"][0]["exhibit_letter"] == "A"

    def test_remove_nonexistent_doc(self):
        save_case("case-rm2", "Client", "", [])
        assert remove_document("case-rm2", "nonexistent") is False

    def test_remove_from_nonexistent_case(self):
        assert remove_document("nope", "any") is False


class TestUpdateDocument:
    def test_update_fields(self):
        save_case("case-upd", "Client", "", [])
        doc = add_document("case-upd", title="Old Title", category="Other", page_count=1)

        updated = update_document("case-upd", doc["doc_id"], title="New Title", page_count=5)
        assert updated is not None
        assert updated["title"] == "New Title"
        assert updated["page_count"] == 5

    def test_update_nonexistent_doc(self):
        save_case("case-upd2", "Client", "", [])
        assert update_document("case-upd2", "nonexistent", title="X") is None

    def test_update_nonexistent_case(self):
        assert update_document("nope", "any", title="X") is None

    def test_disallowed_fields_ignored(self):
        save_case("case-upd3", "Client", "", [])
        doc = add_document("case-upd3", title="Test", category="Other")
        # "exhibit_letter" is not in allowed_fields
        updated = update_document("case-upd3", doc["doc_id"], exhibit_letter="ZZ")
        assert updated is not None
        # exhibit_letter should not have changed to ZZ via this function
        assert updated["exhibit_letter"] != "ZZ"


# ── _docs_to_items ───────────────────────────────────────────────────────


class TestDocsToItems:
    def test_converts_dict_to_item(self):
        docs = [
            {"exhibit_letter": "A", "title": "Doc", "category": "Other",
             "page_count": 3, "date_added": "2024-01-01", "box_url": "",
             "description": "test", "doc_id": "abc"},
        ]
        items = _docs_to_items(docs)
        assert len(items) == 1
        assert isinstance(items[0], EvidenceItem)
        assert items[0].title == "Doc"
        assert items[0].page_count == 3

    def test_handles_missing_keys(self):
        docs = [{"title": "Minimal"}]
        items = _docs_to_items(docs)
        assert items[0].title == "Minimal"
        assert items[0].exhibit_letter == ""
        assert items[0].category == "Other"


# ── _case_path sanitization ──────────────────────────────────────────────


class TestCasePath:
    def test_safe_id(self):
        path = _case_path("abc-123")
        assert path.name == "abc-123.json"

    def test_strips_dangerous_chars(self):
        path = _case_path("../../etc/passwd")
        # Should strip slashes and dots
        assert ".." not in path.name
        assert "/" not in path.name


# ── new_case_id ──────────────────────────────────────────────────────────


class TestNewCaseId:
    def test_returns_8_hex_chars(self):
        cid = new_case_id()
        assert len(cid) == 8
        int(cid, 16)  # should not raise

    def test_uniqueness(self):
        ids = {new_case_id() for _ in range(100)}
        assert len(ids) == 100
