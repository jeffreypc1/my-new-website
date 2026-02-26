"""Cover letter templates for Filing Assembler.

Each case type has a structured template with standard enclosed documents,
filing offices, required fields, and a render() function that produces
the complete cover letter text from case data.
"""

from __future__ import annotations

import sys as _sys
from datetime import date
from pathlib import Path as _Path

_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent.parent))
from shared.config_store import get_config_value, load_config, save_config

import json


# ---------------------------------------------------------------------------
# Filing office address book
# ---------------------------------------------------------------------------

_DEFAULT_FILING_OFFICES: dict[str, str] = {
    "USCIS Nebraska Service Center": (
        "USCIS Nebraska Service Center\n"
        "P.O. Box 87589\n"
        "Lincoln, NE 68501-7589"
    ),
    "USCIS Texas Service Center": (
        "USCIS Texas Service Center\n"
        "6046 N. Belt Line Road, Suite 172\n"
        "Irving, TX 75038-0001"
    ),
    "USCIS Vermont Service Center": (
        "USCIS Vermont Service Center\n"
        "75 Lower Welden Street\n"
        "St. Albans, VT 05479-0001"
    ),
    "USCIS California Service Center": (
        "USCIS California Service Center\n"
        "P.O. Box 30111\n"
        "Laguna Niguel, CA 92607-0111"
    ),
    "USCIS Potomac Service Center": (
        "USCIS Potomac Service Center\n"
        "131 South Dearborn, 3rd Floor\n"
        "Chicago, IL 60603-5517"
    ),
    "USCIS Chicago Lockbox": (
        "USCIS Chicago Lockbox\n"
        "131 South Dearborn, 3rd Floor\n"
        "Chicago, IL 60603-5517"
    ),
    "USCIS Dallas Lockbox": (
        "USCIS Dallas Lockbox\n"
        "P.O. Box 650888\n"
        "Dallas, TX 75265"
    ),
    "USCIS Phoenix Lockbox": (
        "USCIS Phoenix Lockbox\n"
        "P.O. Box 21281\n"
        "Phoenix, AZ 85036"
    ),
    "USCIS Lewisville Lockbox": (
        "USCIS Lewisville Lockbox\n"
        "2501 S. State Hwy 121 Business\n"
        "Suite 400\n"
        "Lewisville, TX 75067"
    ),
    "Immigration Court": (
        "[Immigration Court Name]\n"
        "[Court Address]\n"
        "[City, State ZIP]"
    ),
    "Board of Immigration Appeals": (
        "Board of Immigration Appeals\n"
        "Clerk's Office\n"
        "5107 Leesburg Pike, Suite 2000\n"
        "Falls Church, VA 22041"
    ),
    "USCIS Vermont Service Center (VAWA Unit)": (
        "USCIS Vermont Service Center\n"
        "VAWA Unit\n"
        "75 Lower Welden Street\n"
        "St. Albans, VT 05479-0001"
    ),
    "Other": "",
}


# ---------------------------------------------------------------------------
# Recipient address book (structured entries with categories)
# ---------------------------------------------------------------------------

_DEFAULT_RECIPIENT_ADDRESSES: list[dict] = [
    # USCIS Service Centers (5)
    {
        "id": "uscis_nebraska",
        "name": "USCIS Nebraska Service Center",
        "category": "USCIS Service Center",
        "address": "USCIS Nebraska Service Center\nP.O. Box 87589\nLincoln, NE 68501-7589",
        "salutation": "Dear Sir or Madam:",
    },
    {
        "id": "uscis_texas",
        "name": "USCIS Texas Service Center",
        "category": "USCIS Service Center",
        "address": "USCIS Texas Service Center\n6046 N. Belt Line Road, Suite 172\nIrving, TX 75038-0001",
        "salutation": "Dear Sir or Madam:",
    },
    {
        "id": "uscis_vermont",
        "name": "USCIS Vermont Service Center",
        "category": "USCIS Service Center",
        "address": "USCIS Vermont Service Center\n75 Lower Welden Street\nSt. Albans, VT 05479-0001",
        "salutation": "Dear Sir or Madam:",
    },
    {
        "id": "uscis_california",
        "name": "USCIS California Service Center",
        "category": "USCIS Service Center",
        "address": "USCIS California Service Center\nP.O. Box 30111\nLaguna Niguel, CA 92607-0111",
        "salutation": "Dear Sir or Madam:",
    },
    {
        "id": "uscis_potomac",
        "name": "USCIS Potomac Service Center",
        "category": "USCIS Service Center",
        "address": "USCIS Potomac Service Center\n131 South Dearborn, 3rd Floor\nChicago, IL 60603-5517",
        "salutation": "Dear Sir or Madam:",
    },
    # USCIS Lockboxes (4)
    {
        "id": "uscis_chicago_lockbox",
        "name": "USCIS Chicago Lockbox",
        "category": "USCIS Lockbox",
        "address": "USCIS Chicago Lockbox\n131 South Dearborn, 3rd Floor\nChicago, IL 60603-5517",
        "salutation": "Dear Sir or Madam:",
    },
    {
        "id": "uscis_dallas_lockbox",
        "name": "USCIS Dallas Lockbox",
        "category": "USCIS Lockbox",
        "address": "USCIS Dallas Lockbox\nP.O. Box 650888\nDallas, TX 75265",
        "salutation": "Dear Sir or Madam:",
    },
    {
        "id": "uscis_phoenix_lockbox",
        "name": "USCIS Phoenix Lockbox",
        "category": "USCIS Lockbox",
        "address": "USCIS Phoenix Lockbox\nP.O. Box 21281\nPhoenix, AZ 85036",
        "salutation": "Dear Sir or Madam:",
    },
    {
        "id": "uscis_lewisville_lockbox",
        "name": "USCIS Lewisville Lockbox",
        "category": "USCIS Lockbox",
        "address": "USCIS Lewisville Lockbox\n2501 S. State Hwy 121 Business\nSuite 400\nLewisville, TX 75067",
        "salutation": "Dear Sir or Madam:",
    },
    # EOIR Immigration Court (2)
    {
        "id": "immigration_court",
        "name": "Immigration Court",
        "category": "EOIR Immigration Court",
        "address": "[Immigration Court Name]\n[Court Address]\n[City, State ZIP]",
        "salutation": "Dear Sir or Madam:",
    },
    {
        "id": "bia",
        "name": "Board of Immigration Appeals",
        "category": "EOIR Immigration Court",
        "address": "Board of Immigration Appeals\nClerk's Office\n5107 Leesburg Pike, Suite 2000\nFalls Church, VA 22041",
        "salutation": "Dear Sir or Madam:",
    },
    # Other (1)
    {
        "id": "uscis_vermont_vawa",
        "name": "USCIS Vermont Service Center (VAWA Unit)",
        "category": "Other",
        "address": "USCIS Vermont Service Center\nVAWA Unit\n75 Lower Welden Street\nSt. Albans, VT 05479-0001",
        "salutation": "Dear Sir or Madam:",
    },
    # Asylum Offices (8)
    {
        "id": "asylum_arlington",
        "name": "Arlington Asylum Office",
        "category": "Asylum Office",
        "address": "Arlington Asylum Office\n1525 Wilson Boulevard, Suite 200\nArlington, VA 22209",
        "salutation": "Dear Sir or Madam:",
    },
    {
        "id": "asylum_chicago",
        "name": "Chicago Asylum Office",
        "category": "Asylum Office",
        "address": "Chicago Asylum Office\n181 West Madison Street, Suite 3000\nChicago, IL 60602",
        "salutation": "Dear Sir or Madam:",
    },
    {
        "id": "asylum_houston",
        "name": "Houston Asylum Office",
        "category": "Asylum Office",
        "address": "Houston Asylum Office\n1919 Smith Street, 7th Floor\nHouston, TX 77002",
        "salutation": "Dear Sir or Madam:",
    },
    {
        "id": "asylum_los_angeles",
        "name": "Los Angeles Asylum Office",
        "category": "Asylum Office",
        "address": "Los Angeles Asylum Office\n1585 South Manchester Avenue\nAnaheim, CA 92802",
        "salutation": "Dear Sir or Madam:",
    },
    {
        "id": "asylum_miami",
        "name": "Miami Asylum Office",
        "category": "Asylum Office",
        "address": "Miami Asylum Office\n8801 NW 7th Avenue, Suite 100\nMiami, FL 33150",
        "salutation": "Dear Sir or Madam:",
    },
    {
        "id": "asylum_newark",
        "name": "Newark Asylum Office",
        "category": "Asylum Office",
        "address": "Newark Asylum Office\n1200 Wall Street West, 4th Floor\nLyndhurst, NJ 07071",
        "salutation": "Dear Sir or Madam:",
    },
    {
        "id": "asylum_new_york",
        "name": "New York Asylum Office",
        "category": "Asylum Office",
        "address": "New York Asylum Office\n1065 Stewart Avenue, Suite 200\nBethpage, NY 11714",
        "salutation": "Dear Sir or Madam:",
    },
    {
        "id": "asylum_san_francisco",
        "name": "San Francisco Asylum Office",
        "category": "Asylum Office",
        "address": "San Francisco Asylum Office\n75 Hawthorne Street, Suite 200\nSan Francisco, CA 94105",
        "salutation": "Dear Sir or Madam:",
    },
]

RECIPIENT_CATEGORIES: list[str] = [
    "USCIS Service Center",
    "USCIS Lockbox",
    "EOIR Immigration Court",
    "Asylum Office",
    "Other",
]


def get_recipient_addresses() -> list[dict]:
    """Load recipient addresses from config, seeding defaults on first call."""
    config = load_config("recipient-addresses")
    if config is not None:
        return config.get("addresses", [])
    # First call: seed defaults
    save_recipient_addresses(_DEFAULT_RECIPIENT_ADDRESSES)
    return list(_DEFAULT_RECIPIENT_ADDRESSES)


def save_recipient_addresses(addresses: list[dict]) -> None:
    """Persist recipient addresses to config."""
    save_config("recipient-addresses", {"addresses": addresses})


# ---------------------------------------------------------------------------
# Template definitions by case type
# ---------------------------------------------------------------------------

_DEFAULT_TEMPLATES: dict[str, dict] = {
    "Asylum (I-589)": {
        "case_type": "Asylum (I-589)",
        "form_numbers": ["I-589"],
        "filing_offices": [
            "USCIS Nebraska Service Center",
            "USCIS Texas Service Center",
            "USCIS Chicago Lockbox",
            "Immigration Court",
            "Board of Immigration Appeals",
            "Other",
        ],
        "standard_enclosed_docs": [
            "Form I-589, Application for Asylum and for Withholding of Removal",
            "Applicant's personal declaration",
            "Country condition reports and supporting documentation",
            "Supporting evidence (photographs, medical records, police reports)",
            "Legal brief / memorandum of law in support of application",
            "Form G-28, Notice of Entry of Appearance as Attorney",
            "Copies of identity documents (passport, national ID)",
            "Translations and translator certifications (if applicable)",
        ],
        "required_fields": ["client_name", "filing_office"],
        "purpose_paragraph": (
            "Please accept this letter as the cover letter for the enclosed "
            "Form I-589, Application for Asylum and for Withholding of Removal, "
            "filed on behalf of the above-referenced applicant, {client_name}. "
            "The applicant seeks asylum in the United States pursuant to Section "
            "208 of the Immigration and Nationality Act (INA) and withholding of "
            "removal pursuant to INA Section 241(b)(3) and the Convention Against "
            "Torture."
        ),
        "closing_paragraph": (
            "Should you require any additional information or documentation "
            "regarding this application, please do not hesitate to contact our "
            "office. We respectfully request that all correspondence regarding "
            "this matter be directed to the undersigned attorney of record. "
            "Thank you for your time and attention to this matter."
        ),
    },
    "Family-Based (I-130/I-485)": {
        "case_type": "Family-Based (I-130/I-485)",
        "form_numbers": ["I-130", "I-485", "I-765", "I-131", "I-864"],
        "filing_offices": [
            "USCIS Chicago Lockbox",
            "USCIS Dallas Lockbox",
            "USCIS Phoenix Lockbox",
            "USCIS Lewisville Lockbox",
            "USCIS Nebraska Service Center",
            "USCIS Texas Service Center",
            "USCIS California Service Center",
            "USCIS Potomac Service Center",
            "Other",
        ],
        "standard_enclosed_docs": [
            "Form I-130, Petition for Alien Relative",
            "Form I-485, Application to Register Permanent Residence or Adjust Status",
            "Form I-765, Application for Employment Authorization",
            "Form I-131, Application for Travel Document",
            "Form I-864, Affidavit of Support Under Section 213A of the INA",
            "Form G-28, Notice of Entry of Appearance as Attorney",
            "Civil documents (birth certificates, marriage certificate)",
            "Evidence of bona fide marriage (joint accounts, photos, lease agreements)",
            "Passport-style photographs of petitioner and beneficiary",
            "Copies of immigration documents (passport, I-94, prior approvals)",
            "Certified English translations of foreign language documents",
            "Form I-693, Report of Medical Examination and Vaccination Record (sealed)",
        ],
        "required_fields": ["client_name", "filing_office"],
        "purpose_paragraph": (
            "Please accept this letter as the cover letter for the enclosed "
            "Form I-130, Petition for Alien Relative, and Form I-485, Application "
            "to Register Permanent Residence or Adjust Status, along with "
            "accompanying applications, filed on behalf of the above-referenced "
            "petitioner and beneficiary, {client_name}. The applicant seeks "
            "adjustment of status to lawful permanent resident based on an "
            "approved family-based immigrant petition."
        ),
        "closing_paragraph": (
            "Should you require any additional information or documentation "
            "regarding this filing, please do not hesitate to contact our "
            "office. We respectfully request that all correspondence regarding "
            "this matter be directed to the undersigned attorney of record. "
            "Thank you for your time and consideration."
        ),
    },
    "Employment-Based": {
        "case_type": "Employment-Based",
        "form_numbers": ["I-140", "I-485"],
        "filing_offices": [
            "USCIS Nebraska Service Center",
            "USCIS Texas Service Center",
            "USCIS Dallas Lockbox",
            "USCIS Chicago Lockbox",
            "USCIS Potomac Service Center",
            "Other",
        ],
        "standard_enclosed_docs": [
            "Form I-140, Immigrant Petition for Alien Workers",
            "Form I-485, Application to Register Permanent Residence or Adjust Status",
            "Approved Labor Certification (PERM ETA Form 9089)",
            "Employer support letter describing position and qualifications",
            "Form G-28, Notice of Entry of Appearance as Attorney",
            "Evidence of education (diplomas, transcripts, credential evaluations)",
            "Evidence of employment experience (letters from prior employers)",
            "Copies of immigration documents (passport, I-94, current visa status)",
            "Form I-765, Application for Employment Authorization (if concurrent filing)",
            "Form I-131, Application for Travel Document (if concurrent filing)",
            "Passport-style photographs",
        ],
        "required_fields": ["client_name", "filing_office"],
        "purpose_paragraph": (
            "Please accept this letter as the cover letter for the enclosed "
            "Form I-140, Immigrant Petition for Alien Workers, and accompanying "
            "applications filed on behalf of the above-referenced beneficiary, "
            "{client_name}. The petitioning employer seeks classification of the "
            "beneficiary under the applicable employment-based immigrant visa "
            "category."
        ),
        "closing_paragraph": (
            "Should you require any additional information or documentation "
            "regarding this petition, please do not hesitate to contact our "
            "office. We respectfully request that all correspondence regarding "
            "this matter be directed to the undersigned attorney of record. "
            "Thank you for your time and consideration."
        ),
    },
    "VAWA (I-360)": {
        "case_type": "VAWA (I-360)",
        "form_numbers": ["I-360"],
        "filing_offices": [
            "USCIS Vermont Service Center (VAWA Unit)",
            "Other",
        ],
        "standard_enclosed_docs": [
            "Form I-360, Petition for Amerasian, Widow(er), or Special Immigrant",
            "Personal declaration of the self-petitioner",
            "Evidence of qualifying relationship (marriage certificate, birth certificate)",
            "Evidence of abuser's U.S. citizenship or lawful permanent residence",
            "Evidence of battery or extreme cruelty (police reports, medical records, "
            "restraining orders, photographs, affidavits)",
            "Evidence of good faith marriage (joint accounts, photos, lease agreements, "
            "affidavits of friends/family)",
            "Evidence of good moral character",
            "Evidence of residence in the United States",
            "Form G-28, Notice of Entry of Appearance as Attorney",
            "Copies of identity and immigration documents",
            "Certified English translations of foreign language documents",
        ],
        "required_fields": ["client_name", "filing_office"],
        "confidentiality_notice": (
            "CONFIDENTIALITY NOTICE: This filing contains information protected "
            "under the Violence Against Women Act (VAWA). Pursuant to 8 U.S.C. "
            "Section 1367, the information contained in this petition is confidential "
            "and may not be disclosed to any person or entity, including the "
            "alleged abuser. Any unauthorized disclosure is a violation of "
            "federal law. This petition and all supporting documentation must "
            "be maintained in accordance with VAWA confidentiality provisions."
        ),
        "purpose_paragraph": (
            "Please accept this letter as the cover letter for the enclosed "
            "Form I-360, Petition for Amerasian, Widow(er), or Special Immigrant, "
            "filed as a self-petition under the Violence Against Women Act (VAWA) "
            "on behalf of the above-referenced self-petitioner, {client_name}. "
            "The self-petitioner has been subjected to battery and/or extreme "
            "cruelty by a U.S. citizen or lawful permanent resident spouse and "
            "seeks humanitarian protection under VAWA."
        ),
        "closing_paragraph": (
            "We respectfully remind the Service of the confidentiality provisions "
            "of 8 U.S.C. Section 1367 applicable to this filing. Should you "
            "require any additional information or documentation, please do not "
            "hesitate to contact our office. We respectfully request that all "
            "correspondence be directed to the undersigned attorney of record. "
            "Thank you for your attention to this matter."
        ),
    },
    "U-Visa (I-918)": {
        "case_type": "U-Visa (I-918)",
        "form_numbers": ["I-918", "I-918 Supplement B"],
        "filing_offices": [
            "USCIS Vermont Service Center",
            "Other",
        ],
        "standard_enclosed_docs": [
            "Form I-918, Petition for U Nonimmigrant Status",
            "Form I-918 Supplement B, U Nonimmigrant Status Certification "
            "(signed by certifying law enforcement agency)",
            "Personal declaration of the petitioner",
            "Evidence of qualifying criminal activity (police reports, court records, "
            "protective orders)",
            "Evidence of substantial physical or mental abuse suffered",
            "Evidence of helpfulness to law enforcement",
            "Form G-28, Notice of Entry of Appearance as Attorney",
            "Copies of identity and immigration documents",
            "Form I-192, Application for Advance Permission to Enter as Nonimmigrant "
            "(waiver of inadmissibility, if applicable)",
            "Certified English translations of foreign language documents",
        ],
        "required_fields": ["client_name", "filing_office"],
        "purpose_paragraph": (
            "Please accept this letter as the cover letter for the enclosed "
            "Form I-918, Petition for U Nonimmigrant Status, filed on behalf of "
            "the above-referenced petitioner, {client_name}. The petitioner is a "
            "victim of qualifying criminal activity who has suffered substantial "
            "physical or mental abuse as a result of such criminal activity and "
            "has been, is being, or is likely to be helpful to a federal, state, "
            "or local law enforcement agency in the investigation or prosecution "
            "of the qualifying criminal activity."
        ),
        "closing_paragraph": (
            "Should you require any additional information or documentation "
            "regarding this petition, please do not hesitate to contact our "
            "office. We respectfully request that all correspondence regarding "
            "this matter be directed to the undersigned attorney of record. "
            "Thank you for your time and attention to this matter."
        ),
    },
    "T-Visa (I-914)": {
        "case_type": "T-Visa (I-914)",
        "form_numbers": ["I-914"],
        "filing_offices": [
            "USCIS Vermont Service Center",
            "Other",
        ],
        "standard_enclosed_docs": [
            "Form I-914, Application for T Nonimmigrant Status",
            "Personal declaration of the applicant",
            "Evidence of trafficking (police reports, court records, news articles)",
            "Evidence of physical presence in the United States on account of trafficking",
            "Evidence of compliance with reasonable requests for assistance from "
            "law enforcement (or evidence of age under 18)",
            "Evidence that applicant would suffer extreme hardship involving unusual "
            "and severe harm upon removal",
            "Form I-914 Supplement B, Declaration of Law Enforcement Officer "
            "(if available)",
            "Form G-28, Notice of Entry of Appearance as Attorney",
            "Copies of identity and immigration documents",
            "Form I-192, Application for Advance Permission to Enter as Nonimmigrant "
            "(waiver of inadmissibility, if applicable)",
            "Certified English translations of foreign language documents",
        ],
        "required_fields": ["client_name", "filing_office"],
        "purpose_paragraph": (
            "Please accept this letter as the cover letter for the enclosed "
            "Form I-914, Application for T Nonimmigrant Status, filed on behalf of "
            "the above-referenced applicant, {client_name}. The applicant is a "
            "victim of a severe form of trafficking in persons who is physically "
            "present in the United States on account of such trafficking and has "
            "complied with reasonable requests for assistance in the investigation "
            "or prosecution of acts of trafficking."
        ),
        "closing_paragraph": (
            "Should you require any additional information or documentation "
            "regarding this application, please do not hesitate to contact our "
            "office. We respectfully request that all correspondence regarding "
            "this matter be directed to the undersigned attorney of record. "
            "Thank you for your time and attention to this matter."
        ),
    },
    "Removal Defense": {
        "case_type": "Removal Defense",
        "form_numbers": [],
        "filing_offices": [
            "Immigration Court",
            "Board of Immigration Appeals",
            "Other",
        ],
        "standard_enclosed_docs": [
            "Respondent's application for relief (as applicable)",
            "Respondent's personal declaration",
            "Supporting evidence and documentation",
            "Legal brief / memorandum of law in support of application",
            "Country condition reports (if applicable)",
            "Form EOIR-28, Notice of Entry of Appearance as Attorney",
            "Certificate of Service",
        ],
        "required_fields": ["client_name", "a_number", "filing_office"],
        "certificate_of_service": (
            "I hereby certify that on {date}, a copy of the foregoing cover letter "
            "and all enclosed documents was served upon the Office of the Chief "
            "Counsel, U.S. Immigration and Customs Enforcement, by [ ] hand "
            "delivery / [ ] first-class mail / [ ] electronic filing, at the "
            "following address:\n\n"
            "Office of the Chief Counsel\n"
            "U.S. Immigration and Customs Enforcement\n"
            "[Address]"
        ),
        "purpose_paragraph": (
            "Please accept this letter as the cover letter for the enclosed "
            "filing on behalf of the above-referenced respondent, {client_name}, "
            "in removal proceedings before the Immigration Court. The respondent "
            "respectfully submits the enclosed documents in support of the "
            "pending application for relief from removal."
        ),
        "closing_paragraph": (
            "The respondent respectfully requests that the Court consider the "
            "enclosed documentation in support of the application for relief. "
            "Should the Court require any additional information or documentation, "
            "please do not hesitate to contact the undersigned attorney of record. "
            "Thank you for the Court's time and attention to this matter."
        ),
    },
}

# ── Config-aware loading (JSON override with hardcoded fallback) ─────────────
FILING_OFFICES: dict[str, str] = get_config_value("cover-letters", "filing_offices", _DEFAULT_FILING_OFFICES)
TEMPLATES: dict[str, dict] = get_config_value("cover-letters", "templates", _DEFAULT_TEMPLATES)


def get_govt_cover_letter_templates() -> dict[str, dict]:
    """Load government cover letter templates from shared config.

    Reads from data/config/govt-cover-letter-templates.json (managed by
    the Templates tool on port 8510). Falls back to _DEFAULT_TEMPLATES
    if the config file doesn't exist yet.
    """
    config = load_config("govt-cover-letter-templates")
    if config is not None:
        return config
    return dict(_DEFAULT_TEMPLATES)

# Ordered list of case type names for UI selectors
CASE_TYPES: list[str] = list(TEMPLATES.keys())


# ---------------------------------------------------------------------------
# Template retrieval helpers
# ---------------------------------------------------------------------------

def get_template(case_type: str) -> dict | None:
    """Retrieve a template by case type name."""
    return TEMPLATES.get(case_type)


def get_filing_offices(case_type: str) -> list[str]:
    """Return the list of filing offices for a case type."""
    tpl = TEMPLATES.get(case_type)
    if tpl is None:
        return []
    return tpl.get("filing_offices", [])


def get_standard_docs(case_type: str) -> list[str]:
    """Return the standard enclosed documents for a case type."""
    tpl = TEMPLATES.get(case_type)
    if tpl is None:
        return []
    return list(tpl.get("standard_enclosed_docs", []))


def get_filing_office_address(office_name: str) -> str:
    """Look up a filing office address by name."""
    return FILING_OFFICES.get(office_name, office_name)


# ---------------------------------------------------------------------------
# Render a complete cover letter
# ---------------------------------------------------------------------------

def render_cover_letter(
    case_type: str,
    client_name: str,
    a_number: str,
    receipt_number: str,
    filing_office: str,
    enclosed_docs: list[dict[str, str]],
    attorney_name: str,
    bar_number: str,
    firm_name: str,
    firm_address: str,
    custom_purpose: str = "",
    custom_closing: str = "",
    recipient_address: str = "",
    salutation: str = "",
    custom_subject: str = "",
    custom_body: str = "",
    subject_block: str = "",
) -> str:
    """Render a complete cover letter as plain text.

    Args:
        case_type: The case type key (must match a TEMPLATES key).
        client_name: Full name of the client.
        a_number: Alien registration number.
        receipt_number: USCIS receipt number.
        filing_office: Name of the filing office (legacy fallback).
        enclosed_docs: List of dicts with 'name' and optional 'description'.
        attorney_name: Name of the attorney.
        bar_number: Attorney bar number.
        firm_name: Law firm name.
        firm_address: Firm mailing address.
        custom_purpose: Override for the purpose paragraph.
        custom_closing: Override for the closing paragraph.
        recipient_address: Full recipient address block (overrides filing_office).
        salutation: Custom salutation (default: "Dear Sir or Madam:").

    Returns:
        The full cover letter as a string.
    """
    tpl = TEMPLATES.get(case_type)
    if tpl is None:
        return f"[Error: Unknown case type '{case_type}']"

    today = date.today().strftime("%m/%d/%Y")

    # Determine address block: prefer recipient_address, fall back to filing_office
    if recipient_address:
        addr_block = recipient_address
    else:
        office_addr = get_filing_office_address(filing_office)
        addr_block = office_addr if office_addr else filing_office

    # Determine salutation
    sal = salutation if salutation else "Dear Sir or Madam:"

    lines: list[str] = []

    # Date
    lines.append(today)
    lines.append("")

    # Recipient address
    if addr_block:
        lines.append(addr_block)
    lines.append("")

    # RE block
    if subject_block and subject_block.strip():
        for sb_line in subject_block.strip().splitlines():
            lines.append(sb_line)
        lines.append("")
    elif custom_subject:
        lines.append(f"RE: {custom_subject}")
        lines.append(f"    Client: {client_name}")
        if a_number:
            lines.append(f"    A# {a_number}")
        if receipt_number:
            lines.append(f"    Receipt# {receipt_number}")
        lines.append(f"    {case_type}")
        lines.append("")
    else:
        lines.append(f"RE: {client_name}")
        if a_number:
            lines.append(f"    A# {a_number}")
        if receipt_number:
            lines.append(f"    Receipt# {receipt_number}")
        lines.append(f"    {case_type}")
        lines.append("")

    # Salutation
    lines.append(sal)
    lines.append("")

    # Confidentiality notice (VAWA)
    if "confidentiality_notice" in tpl:
        lines.append(tpl["confidentiality_notice"])
        lines.append("")

    if custom_body:
        # Template mode: body → enclosed docs → signature (no separate closing)
        lines.append(custom_body)
        lines.append("")

        # Enclosed documents
        if enclosed_docs:
            lines.append(
                "Enclosed please find the following documents in support of the "
                "above-referenced matter:"
            )
            lines.append("")
            for idx, doc in enumerate(enclosed_docs, start=1):
                name = doc.get("name", "")
                desc = doc.get("description", "")
                if desc:
                    lines.append(f"    {idx}. {name} -- {desc}")
                else:
                    lines.append(f"    {idx}. {name}")
            lines.append("")
    else:
        # Default mode: purpose → enclosed docs → closing
        purpose = custom_purpose or tpl.get("purpose_paragraph", "")
        if purpose:
            lines.append(purpose.format(client_name=client_name))
        lines.append("")

        # Enclosed documents
        lines.append(
            "Enclosed please find the following documents in support of the "
            "above-referenced matter:"
        )
        lines.append("")
        for idx, doc in enumerate(enclosed_docs, start=1):
            name = doc.get("name", "")
            desc = doc.get("description", "")
            if desc:
                lines.append(f"    {idx}. {name} -- {desc}")
            else:
                lines.append(f"    {idx}. {name}")
        lines.append("")

        # Closing paragraph
        closing = custom_closing or tpl.get("closing_paragraph", "")
        if closing:
            lines.append(closing)
        lines.append("")

    # Signature block
    lines.append("Respectfully submitted,")
    lines.append("")
    lines.append("____________________________")
    if attorney_name:
        lines.append(attorney_name)
    if bar_number:
        lines.append(f"Bar No. {bar_number}")
    if firm_name:
        lines.append(firm_name)
    if firm_address:
        for addr_line in firm_address.strip().splitlines():
            lines.append(addr_line)

    # Certificate of service (Removal Defense)
    if "certificate_of_service" in tpl:
        lines.append("")
        lines.append("")
        lines.append("CERTIFICATE OF SERVICE")
        lines.append("")
        lines.append(tpl["certificate_of_service"].format(date=today))

    return "\n".join(lines)


def render_eoir_submission(
    attorney_name: str,
    bar_number: str,
    firm_name: str,
    firm_address: str,
    firm_phone: str = "",
    firm_fax: str = "",
    firm_email: str = "",
    court_location: str = "",
    court_address: str = "",
    applicant_name: str = "",
    a_number: str = "",
    case_type: str = "",
    beneficiaries: list[dict] | None = None,
    submission_type: str = "",
    document_list: list[dict[str, str]] | None = None,
    dhs_address: str = "",
    service_method: str = "first-class mail",
    served_by_name: str = "",
    served_by_bar: str = "",
) -> str:
    """Render an EOIR submission cover page as plain text.

    Returns the same kind of plain-text string as render_cover_letter()
    so it works with _build_docx() and _build_cover_letter_pdf().
    """
    today = date.today().strftime("%m/%d/%Y")
    lines: list[str] = []

    # ── Attorney header ──────────────────────────────────────────────────────
    if attorney_name:
        lines.append(attorney_name)
    if bar_number:
        lines.append(f"Bar No. {bar_number}")
    if firm_name:
        lines.append(firm_name)
    if firm_address:
        for addr_line in firm_address.strip().splitlines():
            lines.append(addr_line)
    contact_parts: list[str] = []
    if firm_phone:
        contact_parts.append(f"Tel: {firm_phone}")
    if firm_fax:
        contact_parts.append(f"Fax: {firm_fax}")
    if contact_parts:
        lines.append(" | ".join(contact_parts))
    if firm_email:
        lines.append(f"Email: {firm_email}")
    lines.append("")

    # ── Court header ─────────────────────────────────────────────────────────
    lines.append("UNITED STATES DEPARTMENT OF JUSTICE")
    lines.append("EXECUTIVE OFFICE FOR IMMIGRATION REVIEW")
    lines.append("IMMIGRATION COURT")
    if court_location:
        lines.append(court_location)
    if court_address:
        for addr_line in court_address.strip().splitlines():
            lines.append(addr_line)
    lines.append("")

    # ── Parties ──────────────────────────────────────────────────────────────
    lines.append("IN THE MATTERS OF:")
    lines.append("")
    if applicant_name:
        a_num_str = f"A# {a_number}" if a_number else ""
        lines.append(f"{applicant_name:<40s}{a_num_str}")
        if case_type:
            lines.append(f"{'':<40s}{case_type}")
    if beneficiaries:
        for ben in beneficiaries:
            ben_name = ben.get("Name", "")
            ben_anum = ben.get("A_Number", "")
            ben_type = ben.get("Type", "")
            a_str = f"A# {ben_anum}" if ben_anum else ""
            if ben_type:
                lines.append(f"{ben_name:<40s}{a_str:<24s}{ben_type}")
            else:
                lines.append(f"{ben_name:<40s}{a_str}")
    lines.append("")

    # ── Submission header ────────────────────────────────────────────────────
    lines.append("RESPONDENT'S SUBMISSION")
    lines.append("")
    if submission_type:
        lines.append(submission_type)
        lines.append("")
    lines.append(today)
    lines.append("")

    # ── Document list ────────────────────────────────────────────────────────
    lines.append(
        "The following documents are respectfully submitted to the Immigration Court"
    )
    lines.append("on behalf of the above-named respondent:")
    lines.append("")
    if document_list:
        for idx, doc in enumerate(document_list, start=1):
            name = doc.get("name", "")
            desc = doc.get("description", "")
            if desc:
                lines.append(f"    {idx}. {name} -- {desc}")
            else:
                lines.append(f"    {idx}. {name}")
    else:
        lines.append("    [No documents listed]")
    lines.append("")

    # ── Signature ────────────────────────────────────────────────────────────
    lines.append("Respectfully submitted,")
    lines.append("")
    lines.append("____________________________")
    if attorney_name:
        lines.append(attorney_name)
    if firm_name:
        lines.append(firm_name)
    lines.append("Counsel for Respondent")

    # ── Certificate of service ───────────────────────────────────────────────
    lines.append("")
    lines.append("")
    lines.append("CERTIFICATE OF SERVICE")
    lines.append("")
    lines.append(
        f"I hereby certify that on {today}, a copy of the foregoing submission and all"
    )
    lines.append(
        "enclosed documents was served upon the Office of the Chief Counsel,"
    )
    lines.append(
        f"Department of Homeland Security, by {service_method}, at the following address:"
    )
    lines.append("")
    if dhs_address:
        for addr_line in dhs_address.strip().splitlines():
            lines.append(addr_line)
    else:
        lines.append("[DHS Address]")
    lines.append("")
    lines.append("____________________________")
    _cert_name = served_by_name or attorney_name
    if _cert_name:
        lines.append(_cert_name)
    if served_by_bar:
        lines.append(served_by_bar)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# EOIR Cover Page — template engine
# ---------------------------------------------------------------------------

DEFAULT_EOIR_COVER_TEMPLATE = """\
{attorney_name}
{bar_number}
{firm_name}
{firm_address}
{contact_line}
{email_line}

UNITED STATES DEPARTMENT OF JUSTICE
EXECUTIVE OFFICE FOR IMMIGRATION REVIEW
IMMIGRATION COURT
{court_location}
{court_address}

IN THE MATTERS OF:

{party_block}

RESPONDENT'S SUBMISSION
{submission_line_1}
{submission_sub_line}

{submission_type}

{date}

The following documents are respectfully submitted to the Immigration Court
on behalf of the above-named respondent:

{document_list}

Respectfully submitted,

____________________________
{attorney_name}
{firm_name}
Counsel for Respondent


CERTIFICATE OF SERVICE

I hereby certify that on {date}, a copy of the foregoing submission and all
enclosed documents was served upon the Office of the Chief Counsel,
Department of Homeland Security, by {service_method}, at the following address:

{dhs_address}

____________________________
{served_by_name}
{served_by_bar}
"""


def _compute_contact_line(phone: str, fax: str) -> str:
    """Build 'Tel: X | Fax: Y' string, omitting blanks."""
    parts: list[str] = []
    if phone:
        parts.append(f"Tel: {phone}")
    if fax:
        parts.append(f"Fax: {fax}")
    return " | ".join(parts)


def _compute_email_line(email: str) -> str:
    """Build 'Email: X' or empty string."""
    return f"Email: {email}" if email else ""


def _compute_party_block(
    applicant: str,
    a_number: str,
    case_type: str,
    beneficiaries: list[dict] | None,
) -> str:
    """Column-formatted applicant line + each beneficiary."""
    lines: list[str] = []
    if applicant:
        a_str = f"A# {a_number}" if a_number else ""
        lines.append(f"{applicant:<40s}{a_str}")
        if case_type:
            lines.append(f"{'':<40s}{case_type}")
    if beneficiaries:
        for ben in beneficiaries:
            ben_name = ben.get("Name", "")
            ben_anum = ben.get("A_Number", "")
            ben_type = ben.get("Type", "")
            a_str = f"A# {ben_anum}" if ben_anum else ""
            if ben_type:
                lines.append(f"{ben_name:<40s}{a_str:<24s}{ben_type}")
            else:
                lines.append(f"{ben_name:<40s}{a_str}")
    return "\n".join(lines)


def _compute_document_list(docs: list[dict[str, str]] | None) -> str:
    """Numbered indented list of enclosed documents."""
    if not docs:
        return "    [No documents listed]"
    lines: list[str] = []
    for idx, doc in enumerate(docs, start=1):
        name = doc.get("name", "")
        desc = doc.get("description", "")
        if desc:
            lines.append(f"    {idx}. {name} -- {desc}")
        else:
            lines.append(f"    {idx}. {name}")
    return "\n".join(lines)


def _clean_blank_lines(text: str) -> str:
    """Collapse 3+ consecutive blank lines to 2."""
    import re
    return re.sub(r"\n{4,}", "\n\n\n", text)


def render_eoir_from_template(
    attorney_name: str,
    bar_number: str,
    firm_name: str,
    firm_address: str,
    firm_phone: str = "",
    firm_fax: str = "",
    firm_email: str = "",
    court_location: str = "",
    court_address: str = "",
    applicant_name: str = "",
    a_number: str = "",
    case_type: str = "",
    beneficiaries: list[dict] | None = None,
    submission_type: str = "",
    submission_line_1: str = "",
    submission_sub_line: str = "",
    document_list: list[dict[str, str]] | None = None,
    dhs_address: str = "",
    service_method: str = "first-class mail",
    served_by_name: str = "",
    served_by_bar: str = "",
    hearing_time: str = "",
    judge_name: str = "",
    next_date_type: str = "",
    next_govt_date: str = "",
    filing_method: str = "",
    template_override: str | None = None,
) -> str:
    """Render EOIR cover page from a template with {variable} placeholders.

    Uses template_override if provided, otherwise DEFAULT_EOIR_COVER_TEMPLATE.
    """
    template = template_override if template_override else DEFAULT_EOIR_COVER_TEMPLATE
    today = date.today().strftime("%m/%d/%Y")

    # Build computed values
    contact_line = _compute_contact_line(firm_phone, firm_fax)
    email_line = _compute_email_line(firm_email)
    party_block = _compute_party_block(applicant_name, a_number, case_type, beneficiaries)
    doc_list_text = _compute_document_list(document_list)

    # Format multi-line firm_address
    addr_text = "\n".join(firm_address.strip().splitlines()) if firm_address else ""

    # Format multi-line court_address
    court_addr_text = "\n".join(court_address.strip().splitlines()) if court_address else ""

    # Format multi-line dhs_address
    dhs_addr_text = ""
    if dhs_address:
        dhs_addr_text = "\n".join(dhs_address.strip().splitlines())
    else:
        dhs_addr_text = "[DHS Address]"

    # Bar number formatting
    bar_text = f"Bar No. {bar_number}" if bar_number else ""

    replacements = {
        "{attorney_name}": attorney_name or "",
        "{bar_number}": bar_text,
        "{firm_name}": firm_name or "",
        "{firm_address}": addr_text,
        "{firm_phone}": firm_phone or "",
        "{firm_fax}": firm_fax or "",
        "{firm_email}": firm_email or "",
        "{contact_line}": contact_line,
        "{email_line}": email_line,
        "{court_location}": court_location or "",
        "{court_address}": court_addr_text,
        "{applicant_name}": applicant_name or "",
        "{a_number}": a_number or "",
        "{case_type}": case_type or "",
        "{party_block}": party_block,
        "{submission_type}": submission_type or "",
        "{submission_line_1}": submission_line_1 or "",
        "{submission_sub_line}": submission_sub_line or "",
        "{date}": today,
        "{document_list}": doc_list_text,
        "{dhs_address}": dhs_addr_text,
        "{service_method}": service_method or "first-class mail",
        "{served_by_name}": served_by_name or "",
        "{served_by_bar}": served_by_bar or "",
        "{hearing_time}": hearing_time or "",
        "{judge_name}": judge_name or "",
        "{next_date_type}": next_date_type or "",
        "{next_govt_date}": next_govt_date or "",
        "{filing_method}": filing_method or "",
    }

    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)

    return _clean_blank_lines(result)


# ---------------------------------------------------------------------------
# Split rendered EOIR text into named blocks for the interactive canvas
# ---------------------------------------------------------------------------

_EOIR_BLOCK_MARKERS = [
    ("court_caption", "UNITED STATES DEPARTMENT OF JUSTICE", "Court Caption"),
    ("party_table", "IN THE MATTERS OF:", "Respondent/Derivative Table"),
    ("submission_body", "RESPONDENT'S SUBMISSION", "Submission Description"),
    ("signature", "Respectfully submitted,", "Signature Block"),
    ("cert_of_service", "CERTIFICATE OF SERVICE", "Certificate of Service"),
]


def split_eoir_into_blocks(text: str) -> list[dict]:
    """Split rendered EOIR text into named, editable blocks.

    Returns list of ``{"id": str, "label": str, "content": str}``.
    """
    if not text:
        return []

    found: list[tuple[int, str, str]] = []
    for block_id, marker, label in _EOIR_BLOCK_MARKERS:
        idx = text.find(marker)
        if idx >= 0:
            found.append((idx, block_id, label))

    if not found:
        return [{"id": "full_document", "label": "Full Document", "content": text.strip()}]

    found.sort(key=lambda x: x[0])
    blocks: list[dict] = []

    # Attorney header = everything before first marker
    first_pos = found[0][0]
    header_text = text[:first_pos].strip()
    if header_text:
        blocks.append({"id": "attorney_header", "label": "Attorney/Firm Header", "content": header_text})

    for i, (pos, block_id, label) in enumerate(found):
        end = found[i + 1][0] if i + 1 < len(found) else len(text)
        blocks.append({"id": block_id, "label": label, "content": text[pos:end].strip()})

    return blocks
