"""Form field definitions for the Forms Assistant tool.

Provides structured metadata for USCIS immigration forms including field
definitions, section layouts, validation rules, filing requirements,
and draft persistence.

Part of the O'Brien Immigration Law tool suite.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.config_store import get_config_value


@dataclass
class FormField:
    """A single field within an immigration form."""

    name: str
    field_type: str  # "text", "date", "select", "checkbox", "textarea", "phone", "email"
    required: bool = False
    section: str = ""
    help_text: str = ""
    validation_rules: dict = field(default_factory=dict)
    options: list[str] = field(default_factory=list)  # For select fields


# ---------------------------------------------------------------------------
# Supported forms with metadata
# ---------------------------------------------------------------------------

_DEFAULT_SUPPORTED_FORMS: dict[str, dict] = {
    "I-589": {
        "title": "Application for Asylum and for Withholding of Removal",
        "agency": "USCIS / EOIR",
        "filing_fee": "None",
        "processing_time": "Varies (affirmative: 6-18 months; defensive: depends on court)",
        "sections": [
            "Part A: Information About You",
            "Part B: Information About Your Spouse and Children",
            "Part C: Last Address",
            "Part D: Background Information",
            "Supplement A: Particular Social Group",
            "Supplement B: Additional Information",
        ],
    },
    "I-130": {
        "title": "Petition for Alien Relative",
        "agency": "USCIS",
        "filing_fee": "$535",
        "processing_time": "7-33 months (varies by category and service center)",
        "sections": [
            "Part 1: Relationship",
            "Part 2: Information About You (Petitioner)",
            "Part 3: Information About Beneficiary",
            "Part 4: Additional Information About Beneficiary",
            "Part 5: Other Information",
        ],
    },
    "I-485": {
        "title": "Application to Register Permanent Residence or Adjust Status",
        "agency": "USCIS",
        "filing_fee": "$1,140 (age 14-78); $750 (under 14)",
        "processing_time": "8-26 months",
        "sections": [
            "Part 1: Information About You",
            "Part 2: Application Type",
            "Part 3: Processing Information",
            "Part 4: Accommodations for Individuals with Disabilities",
            "Part 5: Additional Information",
        ],
    },
    "I-765": {
        "title": "Application for Employment Authorization",
        "agency": "USCIS",
        "filing_fee": "$410 (or $0 for asylum-based)",
        "processing_time": "3-7 months",
        "sections": [
            "Part 1: Reason for Applying",
            "Part 2: Information About You",
            "Part 3: Applicant's Statement",
        ],
    },
    "I-131": {
        "title": "Application for Travel Document",
        "agency": "USCIS",
        "filing_fee": "$575",
        "processing_time": "3-10 months",
        "sections": [
            "Part 1: Information About You",
            "Part 2: Application Type",
            "Part 3: Processing Information",
            "Part 4: Information About Your Proposed Travel",
        ],
    },
    "I-290B": {
        "title": "Notice of Appeal or Motion",
        "agency": "USCIS / AAO",
        "filing_fee": "$675",
        "processing_time": "6-18 months",
        "sections": [
            "Part 1: Information About You",
            "Part 2: Information About the Appeal or Motion",
            "Part 3: Basis for the Appeal or Motion",
        ],
    },
    "I-360": {
        "title": "Petition for Amerasian, Widow(er), or Special Immigrant (VAWA)",
        "agency": "USCIS",
        "filing_fee": "None (VAWA self-petitions)",
        "processing_time": "12-24 months",
        "sections": [
            "Part 1: Information About You",
            "Part 2: Classification Sought",
            "Part 3: Additional Information",
            "Part 4: Processing Information",
        ],
    },
    "N-400": {
        "title": "Application for Naturalization",
        "agency": "USCIS",
        "filing_fee": "$710",
        "processing_time": "6-12 months",
        "sections": [
            "Part 1: Information About Your Eligibility",
            "Part 2: Information About You",
            "Part 3: Accommodations for Individuals with Disabilities",
            "Part 4: Information About Your Residence",
            "Part 5: Information About Your Parents",
            "Part 6: Information About Your Marital History",
            "Part 7: Information About Your Children",
            "Part 8: Additional Information",
        ],
    },
    "I-140": {
        "title": "Immigrant Petition for Alien Workers",
        "agency": "USCIS",
        "filing_fee": "$700",
        "processing_time": "6-18 months (premium processing available)",
        "sections": [
            "Part 1: Information About the Petitioner",
            "Part 2: Petition Type",
            "Part 3: Information About the Beneficiary",
            "Part 4: Processing Information",
            "Part 5: Additional Information",
        ],
    },
    "I-129": {
        "title": "Petition for Nonimmigrant Worker",
        "agency": "USCIS",
        "filing_fee": "$460",
        "processing_time": "2-6 months (premium processing available)",
        "sections": [
            "Part 1: Information About the Petitioner",
            "Part 2: Information About the Request",
            "Part 3: Information About the Beneficiary",
            "Part 4: Processing Information",
        ],
    },
    "I-539": {
        "title": "Application to Extend/Change Nonimmigrant Status",
        "agency": "USCIS",
        "filing_fee": "$370",
        "processing_time": "3-12 months",
        "sections": [
            "Part 1: Information About You",
            "Part 2: Application Type",
            "Part 3: Processing Information",
            "Part 4: Additional Information",
        ],
    },
    "I-90": {
        "title": "Application to Replace Permanent Resident Card",
        "agency": "USCIS",
        "filing_fee": "$455",
        "processing_time": "6-12 months",
        "sections": [
            "Part 1: Information About You",
            "Part 2: Reason for Application",
            "Part 3: Processing Information",
        ],
    },
    "I-751": {
        "title": "Petition to Remove Conditions on Residence",
        "agency": "USCIS",
        "filing_fee": "$595",
        "processing_time": "12-24 months",
        "sections": [
            "Part 1: Information About You",
            "Part 2: Information About the Joint Petition (or Waiver)",
            "Part 3: Additional Information",
        ],
    },
    "I-864": {
        "title": "Affidavit of Support Under Section 213A of the INA",
        "agency": "USCIS",
        "filing_fee": "None (filed with I-485 or visa application)",
        "processing_time": "N/A (adjudicated with underlying petition)",
        "sections": [
            "Part 1: Basis for Filing",
            "Part 2: Information About the Sponsor",
            "Part 3: Information About the Immigrant",
            "Part 4: Sponsor's Household Size",
            "Part 5: Sponsor's Income and Employment",
            "Part 6: Sponsor's Assets",
        ],
    },
    "I-821D": {
        "title": "Consideration of Deferred Action for Childhood Arrivals (DACA)",
        "agency": "USCIS",
        "filing_fee": "$495 (with I-765 and biometrics)",
        "processing_time": "3-6 months",
        "sections": [
            "Part 1: Information About You",
            "Part 2: Basis for DACA Request",
            "Part 3: Additional Information",
        ],
    },
    "G-28": {
        "title": "Notice of Entry of Appearance as Attorney or Accredited Representative",
        "agency": "USCIS / EOIR / CBP",
        "filing_fee": "None",
        "processing_time": "N/A (filed with substantive applications)",
        "sections": [
            "Part 1: Information About Attorney/Representative",
            "Part 2: Information About the Client",
            "Part 3: Consent and Signature",
        ],
    },
}

# ── Config-aware loading (JSON override with hardcoded fallback) ─────────────
SUPPORTED_FORMS: dict[str, dict] = get_config_value("forms-assistant", "supported_forms", _DEFAULT_SUPPORTED_FORMS)


# ---------------------------------------------------------------------------
# I-589 detailed field definitions
# ---------------------------------------------------------------------------

I589_FIELDS: dict[str, list[FormField]] = {
    "Part A: Information About You": [
        FormField(
            name="full_name",
            field_type="text",
            required=True,
            section="Part A",
            help_text="Your complete legal name as it appears on your passport or travel document.",
        ),
        FormField(
            name="other_names",
            field_type="textarea",
            required=False,
            section="Part A",
            help_text="List any other names you have used (maiden name, aliases, etc.).",
        ),
        FormField(
            name="date_of_birth",
            field_type="date",
            required=True,
            section="Part A",
            help_text="Your date of birth (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="a_number",
            field_type="text",
            required=False,
            section="Part A",
            help_text="Your Alien Registration Number, if any (9 digits).",
            validation_rules={"pattern": r"^A?\d{9}$"},
        ),
        FormField(
            name="country_of_nationality",
            field_type="text",
            required=True,
            section="Part A",
            help_text="Your country of nationality or citizenship.",
        ),
        FormField(
            name="gender",
            field_type="select",
            required=True,
            section="Part A",
            help_text="Select your gender.",
            options=["Male", "Female"],
        ),
        FormField(
            name="marital_status",
            field_type="select",
            required=True,
            section="Part A",
            help_text="Your current marital status.",
            options=["Single", "Married", "Divorced", "Widowed"],
        ),
        FormField(
            name="us_address",
            field_type="textarea",
            required=True,
            section="Part A",
            help_text="Your current address in the United States.",
        ),
        FormField(
            name="phone_number",
            field_type="text",
            required=False,
            section="Part A",
            help_text="Your telephone number.",
        ),
        FormField(
            name="immigration_status",
            field_type="text",
            required=True,
            section="Part A",
            help_text="Your current immigration status (e.g., B-1, F-1, None/EWI).",
        ),
        FormField(
            name="date_of_last_arrival",
            field_type="date",
            required=True,
            section="Part A",
            help_text="Date of your last arrival in the United States.",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="i94_number",
            field_type="text",
            required=False,
            section="Part A",
            help_text="Your I-94 Arrival/Departure Record number.",
        ),
    ],
    "Part B: Information About Your Spouse and Children": [
        FormField(
            name="spouse_name",
            field_type="text",
            required=False,
            section="Part B",
            help_text="Full name of your spouse, if applicable.",
        ),
        FormField(
            name="spouse_dob",
            field_type="date",
            required=False,
            section="Part B",
            help_text="Spouse's date of birth.",
        ),
        FormField(
            name="spouse_nationality",
            field_type="text",
            required=False,
            section="Part B",
            help_text="Spouse's country of nationality.",
        ),
        FormField(
            name="spouse_included",
            field_type="checkbox",
            required=False,
            section="Part B",
            help_text="Check if your spouse is included in this application.",
        ),
        FormField(
            name="children",
            field_type="textarea",
            required=False,
            section="Part B",
            help_text="List all children (name, DOB, nationality, location).",
        ),
    ],
    "Part C: Last Address": [
        FormField(
            name="last_address_abroad",
            field_type="textarea",
            required=True,
            section="Part C",
            help_text="Your last address outside the United States.",
        ),
    ],
    "Part D: Background Information": [
        FormField(
            name="persecution_claim",
            field_type="textarea",
            required=True,
            section="Part D",
            help_text=(
                "Describe in detail why you are applying for asylum. Include all "
                "past harm, threats, and reasons you fear return. Attach additional "
                "pages as a declaration if needed."
            ),
        ),
        FormField(
            name="protected_ground",
            field_type="select",
            required=True,
            section="Part D",
            help_text="Select the primary protected ground for your claim.",
            options=[
                "Race",
                "Religion",
                "Nationality",
                "Political Opinion",
                "Particular Social Group",
            ],
        ),
        FormField(
            name="organization_membership",
            field_type="textarea",
            required=False,
            section="Part D",
            help_text="List any organizations you belong to or have belonged to.",
        ),
    ],
    "Supplement A: Particular Social Group": [
        FormField(
            name="psg_definition",
            field_type="textarea",
            required=False,
            section="Supplement A",
            help_text=(
                "If claiming membership in a particular social group, define "
                "the group with specificity. Address immutability, particularity, "
                "and social distinction per Matter of M-E-V-G-."
            ),
        ),
    ],
    "Supplement B: Additional Information": [
        FormField(
            name="additional_info",
            field_type="textarea",
            required=False,
            section="Supplement B",
            help_text="Provide any additional information supporting your application.",
        ),
    ],
}


# ---------------------------------------------------------------------------
# I-130 detailed field definitions
# ---------------------------------------------------------------------------

I130_FIELDS: dict[str, list[FormField]] = {
    "Part 1: Relationship": [
        FormField(
            name="relationship_type",
            field_type="select",
            required=True,
            section="Part 1",
            help_text="Select the relationship of the beneficiary to the petitioner.",
            options=["Spouse", "Parent", "Child"],
        ),
        FormField(
            name="petitioner_status",
            field_type="select",
            required=True,
            section="Part 1",
            help_text="Select the petitioner's immigration status.",
            options=["U.S. Citizen", "Lawful Permanent Resident"],
        ),
    ],
    "Part 2: Information About You (Petitioner)": [
        FormField(
            name="petitioner_name",
            field_type="text",
            required=True,
            section="Part 2",
            help_text="Full legal name of the petitioner.",
        ),
        FormField(
            name="petitioner_dob",
            field_type="date",
            required=True,
            section="Part 2",
            help_text="Petitioner's date of birth (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="petitioner_country_of_birth",
            field_type="text",
            required=False,
            section="Part 2",
            help_text="Country where the petitioner was born.",
        ),
        FormField(
            name="petitioner_ssn",
            field_type="text",
            required=False,
            section="Part 2",
            help_text="Petitioner's Social Security Number (9 digits).",
            validation_rules={"pattern": r"^\d{3}-?\d{2}-?\d{4}$"},
        ),
        FormField(
            name="petitioner_address",
            field_type="textarea",
            required=True,
            section="Part 2",
            help_text="Petitioner's current mailing address.",
        ),
        FormField(
            name="petitioner_phone",
            field_type="text",
            required=False,
            section="Part 2",
            help_text="Petitioner's daytime telephone number.",
        ),
    ],
    "Part 3: Information About Beneficiary": [],
    "Part 4: Additional Information About Beneficiary": [],
    "Part 5: Other Information": [],
}


# ---------------------------------------------------------------------------
# I-485 detailed field definitions
# ---------------------------------------------------------------------------

I485_FIELDS: dict[str, list[FormField]] = {
    "Part 1: Information About You": [
        FormField(
            name="applicant_name",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Your full legal name as it appears on your passport or travel document.",
        ),
        FormField(
            name="applicant_dob",
            field_type="date",
            required=True,
            section="Part 1",
            help_text="Your date of birth (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="applicant_country_of_birth",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Country where you were born.",
        ),
        FormField(
            name="applicant_nationality",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Your country of nationality or citizenship.",
        ),
        FormField(
            name="applicant_ssn",
            field_type="text",
            required=False,
            section="Part 1",
            help_text="Your Social Security Number, if any.",
            validation_rules={"pattern": r"^\d{3}-?\d{2}-?\d{4}$"},
        ),
        FormField(
            name="applicant_a_number",
            field_type="text",
            required=False,
            section="Part 1",
            help_text="Your Alien Registration Number (A-Number), if any.",
            validation_rules={"pattern": r"^A?\d{9}$"},
        ),
        FormField(
            name="applicant_uscis_account",
            field_type="text",
            required=False,
            section="Part 1",
            help_text="Your USCIS Online Account Number, if any.",
        ),
        FormField(
            name="applicant_gender",
            field_type="select",
            required=True,
            section="Part 1",
            help_text="Select your gender.",
            options=["Male", "Female"],
        ),
        FormField(
            name="applicant_marital_status",
            field_type="select",
            required=True,
            section="Part 1",
            help_text="Your current marital status.",
            options=["Single", "Married", "Divorced", "Widowed"],
        ),
        FormField(
            name="current_address",
            field_type="textarea",
            required=True,
            section="Part 1",
            help_text="Your current physical address in the United States.",
        ),
    ],
    "Part 2: Application Type": [],
    "Part 3: Processing Information": [],
    "Part 4: Accommodations for Individuals with Disabilities": [],
    "Part 5: Additional Information": [],
}


# ---------------------------------------------------------------------------
# I-765 detailed field definitions
# ---------------------------------------------------------------------------

I765_FIELDS: dict[str, list[FormField]] = {
    "Part 1: Reason for Applying": [
        FormField(
            name="eligibility_category",
            field_type="select",
            required=True,
            section="Part 1",
            help_text="Select the eligibility category for your EAD application.",
            options=[
                "(c)(8) - Asylum Applicant",
                "(c)(9) - Adjustment Pending",
                "(a)(12) - TPS",
                "(c)(10) - Withholding Applicant",
            ],
        ),
        FormField(
            name="application_type",
            field_type="select",
            required=True,
            section="Part 1",
            help_text="Select whether this is an initial, renewal, or replacement application.",
            options=["Initial", "Renewal", "Replacement"],
        ),
    ],
    "Part 2: Information About You": [
        FormField(
            name="applicant_name",
            field_type="text",
            required=True,
            section="Part 2",
            help_text="Your full legal name.",
        ),
        FormField(
            name="applicant_dob",
            field_type="date",
            required=True,
            section="Part 2",
            help_text="Your date of birth (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="country_of_birth",
            field_type="text",
            required=True,
            section="Part 2",
            help_text="Country where you were born.",
        ),
        FormField(
            name="a_number",
            field_type="text",
            required=False,
            section="Part 2",
            help_text="Your Alien Registration Number (A-Number), if any.",
            validation_rules={"pattern": r"^A?\d{9}$"},
        ),
        FormField(
            name="ssn",
            field_type="text",
            required=False,
            section="Part 2",
            help_text="Your Social Security Number, if any.",
            validation_rules={"pattern": r"^\d{3}-?\d{2}-?\d{4}$"},
        ),
        FormField(
            name="current_address",
            field_type="textarea",
            required=True,
            section="Part 2",
            help_text="Your current mailing address in the United States.",
        ),
    ],
    "Part 3: Applicant's Statement": [],
}


# ---------------------------------------------------------------------------
# I-131 detailed field definitions
# ---------------------------------------------------------------------------

I131_FIELDS: dict[str, list[FormField]] = {
    "Part 1: Information About You": [
        FormField(
            name="applicant_name",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Your full legal name.",
        ),
        FormField(
            name="applicant_dob",
            field_type="date",
            required=True,
            section="Part 1",
            help_text="Your date of birth (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="country_of_birth",
            field_type="text",
            required=False,
            section="Part 1",
            help_text="Country where you were born.",
        ),
        FormField(
            name="a_number",
            field_type="text",
            required=False,
            section="Part 1",
            help_text="Your Alien Registration Number (A-Number), if any.",
            validation_rules={"pattern": r"^A?\d{9}$"},
        ),
        FormField(
            name="current_address",
            field_type="textarea",
            required=True,
            section="Part 1",
            help_text="Your current mailing address in the United States.",
        ),
    ],
    "Part 2: Application Type": [
        FormField(
            name="document_type",
            field_type="select",
            required=True,
            section="Part 2",
            help_text="Select the type of travel document you are requesting.",
            options=["Advance Parole", "Reentry Permit", "Refugee Travel Document"],
        ),
        FormField(
            name="purpose_of_trip",
            field_type="textarea",
            required=False,
            section="Part 2",
            help_text="Describe the purpose of your proposed travel.",
        ),
        FormField(
            name="countries_to_visit",
            field_type="text",
            required=False,
            section="Part 2",
            help_text="List the countries you plan to visit.",
        ),
        FormField(
            name="departure_date",
            field_type="date",
            required=False,
            section="Part 2",
            help_text="Planned departure date (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="return_date",
            field_type="date",
            required=False,
            section="Part 2",
            help_text="Planned return date (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
    ],
    "Part 3: Processing Information": [],
    "Part 4: Information About Your Proposed Travel": [],
}


# ---------------------------------------------------------------------------
# I-290B detailed field definitions
# ---------------------------------------------------------------------------

I290B_FIELDS: dict[str, list[FormField]] = {
    "Part 1: Information About You": [
        FormField(
            name="appellant_name",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Full legal name of the appellant or movant.",
        ),
        FormField(
            name="a_number",
            field_type="text",
            required=False,
            section="Part 1",
            help_text="Your Alien Registration Number (A-Number), if any.",
            validation_rules={"pattern": r"^A?\d{9}$"},
        ),
        FormField(
            name="receipt_number",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="The receipt number from the decision being appealed or reconsidered.",
        ),
    ],
    "Part 2: Information About the Appeal or Motion": [
        FormField(
            name="filing_type",
            field_type="select",
            required=True,
            section="Part 2",
            help_text="Select whether you are filing an appeal, motion to reopen, or motion to reconsider.",
            options=["Appeal", "Motion to Reopen", "Motion to Reconsider"],
        ),
        FormField(
            name="basis_summary",
            field_type="textarea",
            required=True,
            section="Part 2",
            help_text=(
                "Summarize the basis for your appeal or motion. Include the specific "
                "errors of law or fact you believe were made in the original decision."
            ),
        ),
    ],
    "Part 3: Basis for the Appeal or Motion": [],
}


# ---------------------------------------------------------------------------
# I-360 detailed field definitions
# ---------------------------------------------------------------------------

I360_FIELDS: dict[str, list[FormField]] = {
    "Part 1: Information About You": [
        FormField(
            name="petitioner_name",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Full legal name of the self-petitioner.",
        ),
        FormField(
            name="petitioner_dob",
            field_type="date",
            required=True,
            section="Part 1",
            help_text="Your date of birth (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="country_of_birth",
            field_type="text",
            required=False,
            section="Part 1",
            help_text="Country where you were born.",
        ),
        FormField(
            name="a_number",
            field_type="text",
            required=False,
            section="Part 1",
            help_text="Your Alien Registration Number (A-Number), if any.",
            validation_rules={"pattern": r"^A?\d{9}$"},
        ),
    ],
    "Part 2: Classification Sought": [
        FormField(
            name="classification",
            field_type="select",
            required=True,
            section="Part 2",
            help_text="Select the classification you are seeking.",
            options=[
                "VAWA Self-Petitioner - Spouse",
                "VAWA Self-Petitioner - Child",
                "Special Immigrant Juvenile",
            ],
        ),
        FormField(
            name="abuser_name",
            field_type="text",
            required=False,
            section="Part 2",
            help_text="Full legal name of the abuser (if VAWA self-petition).",
        ),
        FormField(
            name="abuser_status",
            field_type="select",
            required=False,
            section="Part 2",
            help_text="Immigration status of the abuser.",
            options=["U.S. Citizen", "Lawful Permanent Resident"],
        ),
    ],
    "Part 3: Additional Information": [],
    "Part 4: Processing Information": [],
}


# ---------------------------------------------------------------------------
# N-400 detailed field definitions
# ---------------------------------------------------------------------------

N400_FIELDS: dict[str, list[FormField]] = {
    "Part 1: Information About Your Eligibility": [
        FormField(
            name="eligibility_basis",
            field_type="select",
            required=True,
            section="Part 1",
            help_text="Select the basis for your eligibility to naturalize.",
            options=[
                "5 years as LPR",
                "3 years as LPR married to USC",
                "Military service",
                "Other (specify)",
            ],
        ),
    ],
    "Part 2: Information About You": [
        FormField(
            name="full_name",
            field_type="text",
            required=True,
            section="Part 2",
            help_text="Your full legal name as it appears on your permanent resident card.",
        ),
        FormField(
            name="date_of_birth",
            field_type="date",
            required=True,
            section="Part 2",
            help_text="Your date of birth (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="a_number",
            field_type="text",
            required=True,
            section="Part 2",
            help_text="Your Alien Registration Number (9 digits).",
            validation_rules={"pattern": r"^A?\d{9}$"},
        ),
        FormField(
            name="country_of_birth",
            field_type="text",
            required=True,
            section="Part 2",
            help_text="Country where you were born.",
        ),
        FormField(
            name="country_of_nationality",
            field_type="text",
            required=True,
            section="Part 2",
            help_text="Your country of nationality.",
        ),
        FormField(
            name="date_of_lpr",
            field_type="date",
            required=True,
            section="Part 2",
            help_text="Date you became a lawful permanent resident (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="ssn",
            field_type="text",
            required=False,
            section="Part 2",
            help_text="Your Social Security Number.",
            validation_rules={"pattern": r"^\d{3}-?\d{2}-?\d{4}$"},
        ),
        FormField(
            name="gender",
            field_type="select",
            required=True,
            section="Part 2",
            help_text="Select your gender.",
            options=["Male", "Female"],
        ),
        FormField(
            name="marital_status",
            field_type="select",
            required=True,
            section="Part 2",
            help_text="Your current marital status.",
            options=["Single", "Married", "Divorced", "Widowed", "Annulled", "Separated"],
        ),
        FormField(
            name="current_address",
            field_type="textarea",
            required=True,
            section="Part 2",
            help_text="Your current physical address.",
        ),
        FormField(
            name="phone_number",
            field_type="text",
            required=False,
            section="Part 2",
            help_text="Your daytime telephone number.",
        ),
        FormField(
            name="email",
            field_type="text",
            required=False,
            section="Part 2",
            help_text="Your email address.",
        ),
    ],
    "Part 3: Accommodations for Individuals with Disabilities": [],
    "Part 4: Information About Your Residence": [],
    "Part 5: Information About Your Parents": [],
    "Part 6: Information About Your Marital History": [],
    "Part 7: Information About Your Children": [],
    "Part 8: Additional Information": [],
}


# ---------------------------------------------------------------------------
# I-140 detailed field definitions
# ---------------------------------------------------------------------------

I140_FIELDS: dict[str, list[FormField]] = {
    "Part 1: Information About the Petitioner": [
        FormField(
            name="petitioner_name",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Full legal name of the petitioning employer or self-petitioner.",
        ),
        FormField(
            name="petitioner_ein",
            field_type="text",
            required=False,
            section="Part 1",
            help_text="Employer Identification Number (EIN).",
        ),
        FormField(
            name="petitioner_address",
            field_type="textarea",
            required=True,
            section="Part 1",
            help_text="Petitioner's business address.",
        ),
        FormField(
            name="petitioner_phone",
            field_type="text",
            required=False,
            section="Part 1",
            help_text="Petitioner's phone number.",
        ),
    ],
    "Part 2: Petition Type": [
        FormField(
            name="classification",
            field_type="select",
            required=True,
            section="Part 2",
            help_text="Select the immigrant classification sought.",
            options=[
                "EB-1A: Extraordinary Ability",
                "EB-1B: Outstanding Professor/Researcher",
                "EB-1C: Multinational Manager/Executive",
                "EB-2: Advanced Degree / Exceptional Ability",
                "EB-2 NIW: National Interest Waiver",
                "EB-3: Skilled Worker / Professional",
                "EB-3: Other (Unskilled) Worker",
            ],
        ),
        FormField(
            name="job_title",
            field_type="text",
            required=True,
            section="Part 2",
            help_text="The offered job title.",
        ),
        FormField(
            name="salary",
            field_type="text",
            required=False,
            section="Part 2",
            help_text="Annual salary or wage offered.",
        ),
    ],
    "Part 3: Information About the Beneficiary": [
        FormField(
            name="beneficiary_name",
            field_type="text",
            required=True,
            section="Part 3",
            help_text="Full legal name of the beneficiary.",
        ),
        FormField(
            name="beneficiary_dob",
            field_type="date",
            required=True,
            section="Part 3",
            help_text="Beneficiary's date of birth (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="beneficiary_country_of_birth",
            field_type="text",
            required=True,
            section="Part 3",
            help_text="Beneficiary's country of birth.",
        ),
        FormField(
            name="beneficiary_a_number",
            field_type="text",
            required=False,
            section="Part 3",
            help_text="Beneficiary's A-Number, if any.",
            validation_rules={"pattern": r"^A?\d{9}$"},
        ),
    ],
    "Part 4: Processing Information": [],
    "Part 5: Additional Information": [],
}


# ---------------------------------------------------------------------------
# I-864 detailed field definitions
# ---------------------------------------------------------------------------

I864_FIELDS: dict[str, list[FormField]] = {
    "Part 1: Basis for Filing": [
        FormField(
            name="filing_basis",
            field_type="select",
            required=True,
            section="Part 1",
            help_text="Select the basis for filing this affidavit.",
            options=[
                "Petitioner filing for spouse/relative",
                "Joint sponsor",
                "Substitute sponsor",
                "5% owner of petitioning entity",
            ],
        ),
    ],
    "Part 2: Information About the Sponsor": [
        FormField(
            name="sponsor_name",
            field_type="text",
            required=True,
            section="Part 2",
            help_text="Full legal name of the financial sponsor.",
        ),
        FormField(
            name="sponsor_dob",
            field_type="date",
            required=True,
            section="Part 2",
            help_text="Sponsor's date of birth (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="sponsor_address",
            field_type="textarea",
            required=True,
            section="Part 2",
            help_text="Sponsor's current address.",
        ),
        FormField(
            name="sponsor_ssn",
            field_type="text",
            required=True,
            section="Part 2",
            help_text="Sponsor's Social Security Number.",
            validation_rules={"pattern": r"^\d{3}-?\d{2}-?\d{4}$"},
        ),
        FormField(
            name="sponsor_citizenship",
            field_type="select",
            required=True,
            section="Part 2",
            help_text="Sponsor's citizenship status.",
            options=["U.S. Citizen", "Lawful Permanent Resident"],
        ),
    ],
    "Part 3: Information About the Immigrant": [
        FormField(
            name="immigrant_name",
            field_type="text",
            required=True,
            section="Part 3",
            help_text="Full legal name of the immigrant being sponsored.",
        ),
        FormField(
            name="immigrant_a_number",
            field_type="text",
            required=False,
            section="Part 3",
            help_text="Immigrant's A-Number, if any.",
            validation_rules={"pattern": r"^A?\d{9}$"},
        ),
    ],
    "Part 4: Sponsor's Household Size": [
        FormField(
            name="household_size",
            field_type="text",
            required=True,
            section="Part 4",
            help_text="Total number of persons in the sponsor's household (including sponsor, immigrants, dependents).",
        ),
    ],
    "Part 5: Sponsor's Income and Employment": [
        FormField(
            name="current_employer",
            field_type="text",
            required=False,
            section="Part 5",
            help_text="Sponsor's current employer name.",
        ),
        FormField(
            name="annual_income",
            field_type="text",
            required=True,
            section="Part 5",
            help_text="Sponsor's current annual income.",
        ),
    ],
    "Part 6: Sponsor's Assets": [],
}


# ---------------------------------------------------------------------------
# I-821D detailed field definitions
# ---------------------------------------------------------------------------

I821D_FIELDS: dict[str, list[FormField]] = {
    "Part 1: Information About You": [
        FormField(
            name="full_name",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Your full legal name.",
        ),
        FormField(
            name="date_of_birth",
            field_type="date",
            required=True,
            section="Part 1",
            help_text="Your date of birth (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="country_of_birth",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Country where you were born.",
        ),
        FormField(
            name="country_of_citizenship",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Your country of citizenship.",
        ),
        FormField(
            name="a_number",
            field_type="text",
            required=False,
            section="Part 1",
            help_text="Your A-Number, if any.",
            validation_rules={"pattern": r"^A?\d{9}$"},
        ),
        FormField(
            name="current_address",
            field_type="textarea",
            required=True,
            section="Part 1",
            help_text="Your current address in the United States.",
        ),
    ],
    "Part 2: Basis for DACA Request": [
        FormField(
            name="request_type",
            field_type="select",
            required=True,
            section="Part 2",
            help_text="Select whether this is an initial request or renewal.",
            options=["Initial Request", "Renewal"],
        ),
        FormField(
            name="date_first_entry",
            field_type="date",
            required=True,
            section="Part 2",
            help_text="Date of your first entry into the United States (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="manner_of_entry",
            field_type="text",
            required=False,
            section="Part 2",
            help_text="How you entered the U.S. (e.g., EWI, B-2, F-1).",
        ),
        FormField(
            name="education_status",
            field_type="select",
            required=True,
            section="Part 2",
            help_text="Your current education status.",
            options=[
                "Currently in school",
                "High school diploma",
                "GED",
                "Honorable discharge from military",
            ],
        ),
    ],
    "Part 3: Additional Information": [],
}


# ---------------------------------------------------------------------------
# G-28 detailed field definitions
# ---------------------------------------------------------------------------

G28_FIELDS: dict[str, list[FormField]] = {
    "Part 1: Information About Attorney/Representative": [
        FormField(
            name="attorney_name",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Full name of the attorney or accredited representative.",
        ),
        FormField(
            name="attorney_bar_number",
            field_type="text",
            required=False,
            section="Part 1",
            help_text="Attorney's bar number or accreditation number.",
        ),
        FormField(
            name="attorney_firm",
            field_type="text",
            required=False,
            section="Part 1",
            help_text="Name of law firm or recognized organization.",
        ),
        FormField(
            name="attorney_address",
            field_type="textarea",
            required=True,
            section="Part 1",
            help_text="Attorney's business address.",
        ),
        FormField(
            name="attorney_phone",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Attorney's telephone number.",
        ),
        FormField(
            name="attorney_email",
            field_type="text",
            required=False,
            section="Part 1",
            help_text="Attorney's email address.",
        ),
    ],
    "Part 2: Information About the Client": [
        FormField(
            name="client_name",
            field_type="text",
            required=True,
            section="Part 2",
            help_text="Full legal name of the client.",
        ),
        FormField(
            name="client_a_number",
            field_type="text",
            required=False,
            section="Part 2",
            help_text="Client's A-Number, if any.",
            validation_rules={"pattern": r"^A?\d{9}$"},
        ),
        FormField(
            name="client_address",
            field_type="textarea",
            required=False,
            section="Part 2",
            help_text="Client's current address.",
        ),
    ],
    "Part 3: Consent and Signature": [],
}


# ---------------------------------------------------------------------------
# I-129 detailed field definitions
# ---------------------------------------------------------------------------

I129_FIELDS: dict[str, list[FormField]] = {
    "Part 1: Information About the Petitioner": [
        FormField(
            name="petitioner_name",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Full legal name of the petitioning employer.",
        ),
        FormField(
            name="petitioner_ein",
            field_type="text",
            required=False,
            section="Part 1",
            help_text="Employer Identification Number (FEIN).",
        ),
        FormField(
            name="petitioner_address",
            field_type="textarea",
            required=True,
            section="Part 1",
            help_text="Petitioner's business address.",
        ),
    ],
    "Part 2: Information About the Request": [
        FormField(
            name="classification",
            field_type="select",
            required=True,
            section="Part 2",
            help_text="Nonimmigrant classification sought.",
            options=[
                "H-1B: Specialty Occupation",
                "H-2A: Temporary Agricultural Worker",
                "H-2B: Temporary Non-Agricultural Worker",
                "L-1A: Intracompany Transferee (Manager/Executive)",
                "L-1B: Intracompany Transferee (Specialized Knowledge)",
                "O-1A: Extraordinary Ability (Sciences/Business/Education/Athletics)",
                "O-1B: Extraordinary Ability (Arts)",
                "P-1: Internationally Recognized Athlete/Entertainer",
                "TN: USMCA Professional",
            ],
        ),
        FormField(
            name="request_type",
            field_type="select",
            required=True,
            section="Part 2",
            help_text="Type of request.",
            options=["New petition", "Extension", "Change of employer", "Amendment"],
        ),
    ],
    "Part 3: Information About the Beneficiary": [
        FormField(
            name="beneficiary_name",
            field_type="text",
            required=True,
            section="Part 3",
            help_text="Full legal name of the beneficiary.",
        ),
        FormField(
            name="beneficiary_dob",
            field_type="date",
            required=True,
            section="Part 3",
            help_text="Beneficiary's date of birth (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="beneficiary_country_of_birth",
            field_type="text",
            required=True,
            section="Part 3",
            help_text="Beneficiary's country of birth.",
        ),
    ],
    "Part 4: Processing Information": [],
}


# ---------------------------------------------------------------------------
# I-539 detailed field definitions
# ---------------------------------------------------------------------------

I539_FIELDS: dict[str, list[FormField]] = {
    "Part 1: Information About You": [
        FormField(
            name="applicant_name",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Your full legal name.",
        ),
        FormField(
            name="date_of_birth",
            field_type="date",
            required=True,
            section="Part 1",
            help_text="Your date of birth (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="country_of_birth",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Country where you were born.",
        ),
        FormField(
            name="i94_number",
            field_type="text",
            required=False,
            section="Part 1",
            help_text="Your I-94 Arrival/Departure Record number.",
        ),
        FormField(
            name="current_status",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Your current nonimmigrant status (e.g., B-2, F-1, H-4).",
        ),
        FormField(
            name="current_address",
            field_type="textarea",
            required=True,
            section="Part 1",
            help_text="Your current address in the United States.",
        ),
    ],
    "Part 2: Application Type": [
        FormField(
            name="request_type",
            field_type="select",
            required=True,
            section="Part 2",
            help_text="Select whether you are requesting an extension or change of status.",
            options=["Extension of Stay", "Change of Status"],
        ),
        FormField(
            name="requested_status",
            field_type="text",
            required=True,
            section="Part 2",
            help_text="The nonimmigrant classification you are requesting (e.g., B-2, F-1).",
        ),
        FormField(
            name="requested_until",
            field_type="date",
            required=False,
            section="Part 2",
            help_text="Requested extension date (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
    ],
    "Part 3: Processing Information": [],
    "Part 4: Additional Information": [],
}


# ---------------------------------------------------------------------------
# I-90 detailed field definitions
# ---------------------------------------------------------------------------

I90_FIELDS: dict[str, list[FormField]] = {
    "Part 1: Information About You": [
        FormField(
            name="full_name",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Your full legal name as it appears on your permanent resident card.",
        ),
        FormField(
            name="date_of_birth",
            field_type="date",
            required=True,
            section="Part 1",
            help_text="Your date of birth (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="a_number",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Your Alien Registration Number (A-Number).",
            validation_rules={"pattern": r"^A?\d{9}$"},
        ),
        FormField(
            name="current_address",
            field_type="textarea",
            required=True,
            section="Part 1",
            help_text="Your current mailing address.",
        ),
    ],
    "Part 2: Reason for Application": [
        FormField(
            name="reason",
            field_type="select",
            required=True,
            section="Part 2",
            help_text="Select the reason for applying.",
            options=[
                "Card expired or will expire within 6 months",
                "Card was lost, stolen, or destroyed",
                "Name or other biographic info changed",
                "Commuter status conversion",
                "Card contains incorrect data",
                "Never received card",
            ],
        ),
    ],
    "Part 3: Processing Information": [],
}


# ---------------------------------------------------------------------------
# I-751 detailed field definitions
# ---------------------------------------------------------------------------

I751_FIELDS: dict[str, list[FormField]] = {
    "Part 1: Information About You": [
        FormField(
            name="full_name",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Your full legal name.",
        ),
        FormField(
            name="date_of_birth",
            field_type="date",
            required=True,
            section="Part 1",
            help_text="Your date of birth (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="a_number",
            field_type="text",
            required=True,
            section="Part 1",
            help_text="Your Alien Registration Number.",
            validation_rules={"pattern": r"^A?\d{9}$"},
        ),
        FormField(
            name="date_of_marriage",
            field_type="date",
            required=True,
            section="Part 1",
            help_text="Date of your marriage (mm/dd/yyyy).",
            validation_rules={"format": "mm/dd/yyyy"},
        ),
        FormField(
            name="current_address",
            field_type="textarea",
            required=True,
            section="Part 1",
            help_text="Your current address.",
        ),
    ],
    "Part 2: Information About the Joint Petition (or Waiver)": [
        FormField(
            name="petition_type",
            field_type="select",
            required=True,
            section="Part 2",
            help_text="Select the type of petition.",
            options=[
                "Joint petition with spouse",
                "Waiver: marriage entered in good faith but terminated",
                "Waiver: extreme cruelty / battering",
                "Waiver: extreme hardship upon removal",
            ],
        ),
        FormField(
            name="spouse_name",
            field_type="text",
            required=False,
            section="Part 2",
            help_text="Full name of your U.S. citizen or LPR spouse.",
        ),
    ],
    "Part 3: Additional Information": [],
}


# ---------------------------------------------------------------------------
# Field lookup: form_id -> fields dict
# ---------------------------------------------------------------------------

FIELD_DEFINITIONS: dict[str, dict[str, list[FormField]]] = {
    "I-589": I589_FIELDS,
    "I-130": I130_FIELDS,
    "I-485": I485_FIELDS,
    "I-765": I765_FIELDS,
    "I-131": I131_FIELDS,
    "I-290B": I290B_FIELDS,
    "I-360": I360_FIELDS,
    "N-400": N400_FIELDS,
    "I-140": I140_FIELDS,
    "I-129": I129_FIELDS,
    "I-539": I539_FIELDS,
    "I-90": I90_FIELDS,
    "I-751": I751_FIELDS,
    "I-864": I864_FIELDS,
    "I-821D": I821D_FIELDS,
    "G-28": G28_FIELDS,
}


def get_fields_for_form(form_id: str) -> dict[str, list[FormField]]:
    """Return the field definitions dict for a given form_id.

    Args:
        form_id: The form identifier (e.g. "I-589").

    Returns:
        Dict mapping section names to lists of FormField objects.
        Empty dict if the form is not recognized or deleted.
    """
    # Check if this form has been deleted
    deleted = get_config_value("forms-assistant", "deleted_forms", [])
    if form_id in deleted:
        return {}
    return FIELD_DEFINITIONS.get(form_id, {})


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_field(field_def: FormField, value: str) -> list[str]:
    """Validate a single form field value against its definition.

    Args:
        field_def: The FormField definition with validation rules.
        value: The user-provided value for the field.

    Returns:
        List of validation error messages. Empty list means valid.
    """
    errors: list[str] = []

    # Required check
    if field_def.required and not str(value).strip():
        label = field_def.name.replace("_", " ").title()
        errors.append(f"{label} is required.")

    # Skip further validation if empty and not required
    if not str(value).strip():
        return errors

    # Pattern validation
    pattern = field_def.validation_rules.get("pattern")
    if pattern:
        if not re.match(pattern, str(value).strip()):
            label = field_def.name.replace("_", " ").title()
            errors.append(f"{label} format is invalid.")

    # Date format validation
    date_format = field_def.validation_rules.get("format")
    if date_format == "mm/dd/yyyy" and str(value).strip():
        if not re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", str(value).strip()):
            label = field_def.name.replace("_", " ").title()
            errors.append(f"{label} must be in mm/dd/yyyy format.")

    # Select field validation
    if field_def.field_type == "select" and field_def.options and str(value).strip():
        if str(value).strip() not in field_def.options:
            label = field_def.name.replace("_", " ").title()
            errors.append(f"{label} must be one of: {', '.join(field_def.options)}.")

    return errors


def check_completeness(
    form_id: str,
    data: dict[str, str],
) -> dict:
    """Check how complete a form submission is.

    Args:
        form_id: The form identifier (e.g. "I-589").
        data: Dict mapping field names to their values.

    Returns:
        Dict with keys:
        - total_fields: total number of fields
        - completed_fields: number of fields with values
        - required_missing: list of required fields without values
        - completion_pct: percentage complete (0-100)
        - errors: list of validation errors
    """
    form_meta = SUPPORTED_FORMS.get(form_id)
    if not form_meta:
        return {"error": f"Unknown form: {form_id}"}

    fields_dict = get_fields_for_form(form_id)
    if not fields_dict:
        return {
            "total_fields": 0,
            "completed_fields": 0,
            "required_missing": [],
            "completion_pct": 0,
            "errors": ["Detailed field definitions not yet available for this form."],
        }

    all_fields = [f for section_fields in fields_dict.values() for f in section_fields]

    if not all_fields:
        return {
            "total_fields": 0,
            "completed_fields": 0,
            "required_missing": [],
            "completion_pct": 0,
            "errors": [],
        }

    total = len(all_fields)
    completed = sum(1 for f in all_fields if str(data.get(f.name, "")).strip())
    required_missing = [
        f.name for f in all_fields
        if f.required and not str(data.get(f.name, "")).strip()
    ]

    # Collect all validation errors
    all_errors: list[str] = []
    for f in all_fields:
        val = str(data.get(f.name, ""))
        errs = validate_field(f, val)
        all_errors.extend(errs)

    pct = round((completed / total) * 100) if total > 0 else 0

    return {
        "total_fields": total,
        "completed_fields": completed,
        "required_missing": required_missing,
        "completion_pct": pct,
        "errors": all_errors,
    }


# ---------------------------------------------------------------------------
# Draft persistence (delegated to app.draft_store -- re-exported for compat)
# ---------------------------------------------------------------------------

from app.draft_store import (  # noqa: E402, F401
    new_draft_id,
    save_form_draft,
    load_form_draft,
    list_form_drafts,
    delete_form_draft,
)
