"""Tests for shared/box_client.py — Box folder ID parsing."""

from __future__ import annotations

import pytest

from shared.box_client import parse_folder_id


class TestParseFolderId:
    def test_bare_numeric_id(self):
        assert parse_folder_id("163957038141") == "163957038141"

    def test_direct_folder_url(self):
        assert parse_folder_id(
            "https://app.box.com/folder/163957038141"
        ) == "163957038141"

    def test_folder_url_with_query_params(self):
        assert parse_folder_id(
            "https://app.box.com/folder/163957038141?s=abc123"
        ) == "163957038141"

    def test_whitespace_stripped(self):
        assert parse_folder_id("  163957038141  ") == "163957038141"

    def test_non_numeric_non_url_returned_as_is(self):
        """When input is not a URL and not numeric, return it unchanged."""
        assert parse_folder_id("some-custom-id") == "some-custom-id"

    def test_folder_url_with_subdomain(self):
        assert parse_folder_id(
            "https://mycompany.app.box.com/folder/12345678"
        ) == "12345678"
