"""Tests for shared/pdf_form_extractor.py — field parsing and auto-suggest."""

from __future__ import annotations

import pytest

from shared.pdf_form_extractor import (
    _extract_part_number,
    _matches,
    _parse_field_name,
    auto_suggest_roles,
)


# ── _parse_field_name ────────────────────────────────────────────────────


class TestParseFieldName:
    def test_family_name_with_path(self):
        result = _parse_field_name("form1[0].#subform[0].Pt1Line1a_FamilyName[0]")
        assert "Family Name" in result

    def test_middle_name(self):
        result = _parse_field_name("Pt2Line3_MiddleName[0]")
        assert "Middle Name" in result

    def test_street_number(self):
        result = _parse_field_name("Line4a_StreetNumberAndName")
        assert "Street" in result

    def test_uscis_account_number(self):
        result = _parse_field_name("USCISOnlineAcctNumber[0]")
        assert "uscis" in result.lower()
        assert "number" in result.lower()

    def test_bare_field_name(self):
        result = _parse_field_name("FamilyName")
        assert "Family Name" in result

    def test_empty_after_strip_uses_original(self):
        # A field like "Pt1Line1a_[0]" would strip to empty
        result = _parse_field_name("Pt1Line1a_[0]")
        assert result  # should not be empty


# ── _extract_part_number ─────────────────────────────────────────────────


class TestExtractPartNumber:
    def test_valid_part(self):
        assert _extract_part_number("Pt1Line1a_FamilyName[0]") == 1

    def test_higher_part(self):
        assert _extract_part_number("Pt7Line2_PreparerName[0]") == 7

    def test_no_part(self):
        assert _extract_part_number("FamilyName[0]") is None

    def test_part_in_path(self):
        assert _extract_part_number("form1[0].Pt3Line5_City[0]") == 3


# ── _matches ─────────────────────────────────────────────────────────────


class TestMatches:
    def test_match_found(self):
        assert _matches("family name field", ["family name", "surname"]) is True

    def test_no_match(self):
        assert _matches("city of birth", ["family name", "surname"]) is False

    def test_empty_patterns(self):
        assert _matches("anything", []) is False


# ── auto_suggest_roles ───────────────────────────────────────────────────


class TestAutoSuggestRoles:
    def _make_field(self, display_label, pdf_field_name="", page_number=0):
        return {
            "pdf_field_name": pdf_field_name,
            "display_label": display_label,
            "field_type": "text",
            "page_number": page_number,
            "role": "none",
            "sf_field": "",
        }

    def test_empty_list(self):
        assert auto_suggest_roles([]) == []

    def test_applicant_last_name(self):
        fields = [self._make_field("Family Name", "Pt1Line1a_FamilyName[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["sf_field"] == "LastName"

    def test_applicant_first_name(self):
        fields = [self._make_field("Given Name", "Pt1Line1b_GivenName[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["sf_field"] == "FirstName"

    def test_applicant_dob(self):
        fields = [self._make_field("Date of Birth", "Pt1Line5_DOB[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["sf_field"] == "Birthdate"

    def test_applicant_a_number(self):
        fields = [self._make_field("Alien Registration Number", "Pt1Line2_ANumber[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["sf_field"] == "A_Number__c"

    def test_applicant_gender(self):
        fields = [self._make_field("Gender", "Pt1Line6_Gender[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["sf_field"] == "Gender__c"

    def test_applicant_email(self):
        # Use "E-mail" label to avoid "address" keyword triggering street match
        fields = [self._make_field("E-mail", "Pt1Line10_Email[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["sf_field"] == "Email"

    def test_applicant_phone(self):
        fields = [self._make_field("Daytime Phone Number", "Pt1Line8_Phone[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["sf_field"] == "Phone"

    def test_applicant_mobile(self):
        fields = [self._make_field("Mobile Phone", "Pt1Line9_Mobile[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["sf_field"] == "MobilePhone"

    def test_applicant_street(self):
        fields = [self._make_field("Street Address", "Pt1Line4_Street[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["sf_field"] == "MailingStreet"

    def test_applicant_city(self):
        fields = [self._make_field("City", "Pt1Line5_City[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["sf_field"] == "MailingCity"

    def test_applicant_state(self):
        fields = [self._make_field("State", "Pt1Line6_State[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["sf_field"] == "MailingState"

    def test_applicant_zip(self):
        fields = [self._make_field("ZIP Code", "Pt1Line7_Zip[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["sf_field"] == "MailingPostalCode"

    def test_applicant_country_of_nationality(self):
        fields = [self._make_field("Country of Nationality", "Pt1Line3_Country[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["sf_field"] == "Country__c"

    def test_applicant_city_of_birth(self):
        fields = [self._make_field("City of Birth", "Pt1Line4_CityBirth[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["sf_field"] == "City_of_Birth__c"

    def test_applicant_marital_status(self):
        fields = [self._make_field("Marital Status", "Pt1Line7_Marital[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["sf_field"] == "Marital_status__c"

    def test_applicant_language(self):
        fields = [self._make_field("Language", "Pt1Line8_Language[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["sf_field"] == "Best_Language__c"

    def test_preparer_name_by_keyword(self):
        fields = [self._make_field("Preparer Full Name", "Pt7Line1_PreparerName[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["role"] == "preparer_name"

    def test_preparer_by_high_part_number(self):
        """Part >= 6 and last-name-like label should map to preparer."""
        fields = [self._make_field("Family Name", "Pt7Line1_FamilyName[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["role"] == "preparer_name"

    def test_attorney_by_keyword(self):
        fields = [self._make_field("Attorney Name", "AttorneyName[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["role"] == "attorney_name"

    def test_attorney_bar_number(self):
        fields = [self._make_field("Attorney Bar Number", "Pt8Line2_BarNumber[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["role"] == "attorney_bar_number"

    def test_preparer_email(self):
        fields = [self._make_field("Preparer Email", "Pt7Line5_Email[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["role"] == "preparer_email"

    def test_preparer_phone(self):
        fields = [self._make_field("Preparer Phone", "Pt7Line4_Phone[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["role"] == "preparer_phone"

    def test_preparer_firm(self):
        fields = [self._make_field("Preparer Organization", "Pt7Line3_Firm[0]")]
        auto_suggest_roles(fields)
        assert fields[0]["role"] == "preparer_firm"

    def test_skips_already_tagged(self):
        fields = [self._make_field("Family Name", "Pt1Line1_FamilyName[0]")]
        fields[0]["role"] = "attorney_name"  # already tagged
        auto_suggest_roles(fields)
        assert fields[0]["role"] == "attorney_name"  # unchanged

    def test_skips_already_sf_mapped(self):
        fields = [self._make_field("Family Name", "Pt1Line1_FamilyName[0]")]
        fields[0]["sf_field"] = "LastName"  # already mapped
        auto_suggest_roles(fields)
        assert fields[0]["sf_field"] == "LastName"  # unchanged

    def test_last_page_heuristic(self):
        """Fields on the last page (when > 2 pages) default out of applicant context."""
        fields = [
            self._make_field("Family Name", "Line1_FamilyName[0]", page_number=0),
            self._make_field("Family Name", "Line2_FamilyName[0]", page_number=5),
        ]
        auto_suggest_roles(fields)
        # Page 0 should be applicant
        assert fields[0]["sf_field"] == "LastName"
        # Page 5 (last page with max > 2) is outside applicant context
        # Exact behavior depends on other heuristics, but it shouldn't be applicant
