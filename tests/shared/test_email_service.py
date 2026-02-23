"""Tests for shared/email_service.py — template merging and email sending."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from shared.email_service import merge_template, send_email


# ── Template merging ─────────────────────────────────────────────────────


class TestMergeTemplate:
    def test_direct_sf_field_names(self, sample_client_record):
        subject = "Hello {FirstName}"
        body = "Dear {Name}, your A-Number is {A_Number__c}."
        merged_subj, merged_body = merge_template(subject, body, sample_client_record)
        assert merged_subj == "Hello Maria"
        assert "Maria Garcia" in merged_body
        assert "123-456-789" in merged_body

    def test_friendly_aliases(self, sample_client_record):
        subject = "Welcome {first_name}"
        body = "Country: {country}, Language: {language}"
        merged_subj, merged_body = merge_template(subject, body, sample_client_record)
        assert merged_subj == "Welcome Maria"
        assert "Guatemala" in merged_body
        assert "Spanish" in merged_body

    def test_unresolved_placeholders_left_intact(self, sample_client_record):
        subject = "Hello {unknown_field}"
        body = "Value: {does_not_exist}"
        merged_subj, merged_body = merge_template(subject, body, sample_client_record)
        assert merged_subj == "Hello {unknown_field}"
        assert merged_body == "Value: {does_not_exist}"

    def test_mixed_resolved_and_unresolved(self, sample_client_record):
        body = "{first_name} - {unknown} - {last_name}"
        _, merged_body = merge_template("", body, sample_client_record)
        assert merged_body == "Maria - {unknown} - Garcia"

    def test_empty_template(self, sample_client_record):
        subject, body = merge_template("", "", sample_client_record)
        assert subject == ""
        assert body == ""

    def test_no_placeholders(self, sample_client_record):
        subject, body = merge_template("Plain subject", "Plain body", sample_client_record)
        assert subject == "Plain subject"
        assert body == "Plain body"

    def test_all_aliases(self, sample_client_record):
        """Verify several aliases from the _ALIAS_MAP resolve correctly."""
        body = (
            "{name} {email} {phone} {mobile} {dob} {gender} "
            "{marital_status} {court} {case_type} {customer_id}"
        )
        _, merged = merge_template("", body, sample_client_record)
        assert "Maria Garcia" in merged
        assert "maria@example.com" in merged
        assert "555-0101" in merged
        assert "555-0100" in merged
        assert "1990-05-15" in merged

    def test_case_insensitive_alias(self, sample_client_record):
        """Alias lookup should be case-insensitive."""
        _, merged = merge_template("", "{FIRST_NAME}", sample_client_record)
        assert merged == "Maria"


# ── Email sending ────────────────────────────────────────────────────────


class TestSendEmail:
    def test_success(self):
        mock_sf = MagicMock()
        mock_sf.restful.return_value = [{"isSuccess": True}]
        result = send_email(
            sf_connection=mock_sf,
            contact_id="003XXX",
            to_email="test@example.com",
            subject="Test",
            body="Hello",
            sender_name="Office",
        )
        assert result["success"] is True
        mock_sf.restful.assert_called_once()

    def test_api_error(self):
        mock_sf = MagicMock()
        mock_sf.restful.return_value = [
            {"isSuccess": False, "errors": [{"message": "Invalid email"}]}
        ]
        result = send_email(
            sf_connection=mock_sf,
            contact_id="003XXX",
            to_email="bad",
            subject="Test",
            body="Hello",
            sender_name="Office",
        )
        assert result["success"] is False
        assert "Invalid email" in result["error"]

    def test_exception_handling(self):
        mock_sf = MagicMock()
        mock_sf.restful.side_effect = Exception("Connection failed")
        result = send_email(
            sf_connection=mock_sf,
            contact_id="003XXX",
            to_email="test@example.com",
            subject="Test",
            body="Hello",
            sender_name="Office",
        )
        assert result["success"] is False
        assert "Connection failed" in result["error"]

    def test_empty_response_treated_as_success(self):
        mock_sf = MagicMock()
        mock_sf.restful.return_value = []
        result = send_email(
            sf_connection=mock_sf,
            contact_id="003XXX",
            to_email="test@example.com",
            subject="Test",
            body="Hello",
            sender_name="Office",
        )
        assert result["success"] is True
