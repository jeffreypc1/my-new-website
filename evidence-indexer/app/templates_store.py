"""Templates store — config loading/saving for all template types.

Manages four template categories:
- Email templates (shared with client banner email dialog)
- Client cover letter templates
- Government cover letter templates (shared with Cover Pages tool)
- EOIR templates
"""

from __future__ import annotations

import copy
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.config_store import load_config, save_config


# ---------------------------------------------------------------------------
# Email Templates (same config key as admin panel used)
# ---------------------------------------------------------------------------

_DEFAULT_EMAIL_TEMPLATES: list[dict] = [
    {
        "id": "blank",
        "name": "Blank",
        "subject": "",
        "body": "",
    },
    {
        "id": "appointment_reminder",
        "name": "Appointment Reminder",
        "subject": "Appointment Reminder — {first_name} {last_name}",
        "body": (
            "Dear {first_name},\n\n"
            "This is a reminder about your upcoming appointment with our office. "
            "Please bring all relevant documents, including your photo ID and any "
            "correspondence from USCIS or the immigration court.\n\n"
            "If you need to reschedule, please call our office as soon as possible.\n\n"
            "Thank you,\n"
            "O'Brien Immigration Law"
        ),
    },
    {
        "id": "document_request",
        "name": "Document Request",
        "subject": "Documents Needed — {first_name} {last_name} (#{customer_id})",
        "body": (
            "Dear {first_name},\n\n"
            "We are writing to request the following documents for your case:\n\n"
            "1. \n"
            "2. \n"
            "3. \n\n"
            "Please provide these documents at your earliest convenience. You may "
            "email scanned copies to our office or bring the originals to your next "
            "appointment.\n\n"
            "If you have any questions, please do not hesitate to contact us.\n\n"
            "Thank you,\n"
            "O'Brien Immigration Law"
        ),
    },
    {
        "id": "case_status_update",
        "name": "Case Status Update",
        "subject": "Case Update — {first_name} {last_name}",
        "body": (
            "Dear {first_name},\n\n"
            "We are writing to provide an update on your {case_type} case.\n\n"
            "[Update details here]\n\n"
            "Please do not hesitate to contact our office if you have any questions.\n\n"
            "Thank you,\n"
            "O'Brien Immigration Law"
        ),
    },
    {
        "id": "welcome_new_client",
        "name": "Welcome New Client",
        "subject": "Welcome to O'Brien Immigration Law — {first_name} {last_name}",
        "body": (
            "Dear {first_name},\n\n"
            "Welcome to O'Brien Immigration Law. We are pleased to represent you in "
            "your immigration matter.\n\n"
            "Your client number is #{customer_id}. Please reference this number in "
            "all communications with our office.\n\n"
            "We will be in touch soon to schedule your initial consultation and discuss "
            "next steps. In the meantime, please gather any documents related to your "
            "immigration history.\n\n"
            "Thank you for choosing our firm.\n\n"
            "Sincerely,\n"
            "O'Brien Immigration Law"
        ),
    },
]


def get_email_templates() -> list[dict]:
    """Load email templates from config, seeding defaults on first call."""
    templates = load_config("email-templates")
    if templates is not None:
        return templates
    save_email_templates(copy.deepcopy(_DEFAULT_EMAIL_TEMPLATES))
    return copy.deepcopy(_DEFAULT_EMAIL_TEMPLATES)


def save_email_templates(templates: list[dict]) -> None:
    """Persist email templates to config."""
    save_config("email-templates", templates)


# ---------------------------------------------------------------------------
# Client Cover Letter Templates
# ---------------------------------------------------------------------------

_DEFAULT_CLIENT_LETTER_TEMPLATES: list[dict] = [
    {
        "id": "document_request_letter",
        "name": "Document Request Letter",
        "subject": "Documents Needed for Your Case",
        "body": (
            "Dear {first_name} {last_name},\n\n"
            "Thank you for retaining O'Brien Immigration Law to represent you in your "
            "immigration matter. In order to move forward with your case, we need you to "
            "provide the following documents:\n\n"
            "1. [Document 1]\n"
            "2. [Document 2]\n"
            "3. [Document 3]\n\n"
            "Please provide these documents at your earliest convenience. You may bring "
            "originals to our office or email scanned copies.\n\n"
            "If you have any questions, please do not hesitate to contact us.\n\n"
            "Sincerely,\n"
            "O'Brien Immigration Law"
        ),
    },
    {
        "id": "appointment_confirmation",
        "name": "Appointment Confirmation",
        "subject": "Appointment Confirmation",
        "body": (
            "Dear {first_name} {last_name},\n\n"
            "This letter confirms your appointment at our office on [DATE] at [TIME].\n\n"
            "Please bring the following to your appointment:\n"
            "- A valid photo ID (passport, driver's license, or state ID)\n"
            "- Any documents or correspondence from USCIS or the immigration court\n"
            "- Any documents previously requested by our office\n\n"
            "If you need to reschedule, please contact our office at least 24 hours in advance.\n\n"
            "We look forward to seeing you.\n\n"
            "Sincerely,\n"
            "O'Brien Immigration Law"
        ),
    },
    {
        "id": "case_status_letter",
        "name": "Case Status Update",
        "subject": "Update on Your {case_type} Case",
        "body": (
            "Dear {first_name} {last_name},\n\n"
            "We are writing to provide you with an update on your {case_type} case "
            "(A# {a_number}).\n\n"
            "[Update details here]\n\n"
            "If you have any questions about this update or your case in general, "
            "please do not hesitate to contact our office.\n\n"
            "Sincerely,\n"
            "O'Brien Immigration Law"
        ),
    },
]


def get_client_letter_templates() -> list[dict]:
    """Load client cover letter templates from config, seeding defaults on first call."""
    templates = load_config("client-cover-letter-templates")
    if templates is not None:
        return templates
    save_client_letter_templates(copy.deepcopy(_DEFAULT_CLIENT_LETTER_TEMPLATES))
    return copy.deepcopy(_DEFAULT_CLIENT_LETTER_TEMPLATES)


def save_client_letter_templates(templates: list[dict]) -> None:
    """Persist client cover letter templates to config."""
    save_config("client-cover-letter-templates", templates)


# ---------------------------------------------------------------------------
# Government Cover Letter Templates (mirrors cover-letters/app/templates.py)
# ---------------------------------------------------------------------------

_DEFAULT_GOVT_LETTER_TEMPLATES: dict[str, dict] = {
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


def get_govt_letter_templates() -> dict[str, dict]:
    """Load government cover letter templates from config, seeding defaults on first call."""
    config = load_config("govt-cover-letter-templates")
    if config is not None:
        return config
    save_govt_letter_templates(copy.deepcopy(_DEFAULT_GOVT_LETTER_TEMPLATES))
    return copy.deepcopy(_DEFAULT_GOVT_LETTER_TEMPLATES)


def save_govt_letter_templates(templates: dict[str, dict]) -> None:
    """Persist government cover letter templates to config."""
    save_config("govt-cover-letter-templates", templates)


# ---------------------------------------------------------------------------
# EOIR Templates
# ---------------------------------------------------------------------------

_DEFAULT_EOIR_TEMPLATES: list[dict] = [
    {
        "id": "certificate_of_service",
        "name": "Certificate of Service",
        "category": "Certificate",
        "body": (
            "CERTIFICATE OF SERVICE\n\n"
            "I hereby certify that on {date}, a true and correct copy of the foregoing "
            "and all attached documents was served upon the Office of the Chief Counsel, "
            "U.S. Immigration and Customs Enforcement, by:\n\n"
            "[ ] Hand delivery\n"
            "[ ] First-class mail\n"
            "[ ] Electronic filing via EOIR Courts & Appeals System\n\n"
            "at the following address:\n\n"
            "Office of the Chief Counsel\n"
            "U.S. Immigration and Customs Enforcement\n"
            "[Address]\n\n"
            "____________________________\n"
            "[Attorney Name]\n"
            "[Bar Number]\n"
            "Counsel for Respondent"
        ),
    },
    {
        "id": "motion_coversheet",
        "name": "Motion Coversheet",
        "category": "Motion",
        "body": (
            "UNITED STATES DEPARTMENT OF JUSTICE\n"
            "EXECUTIVE OFFICE FOR IMMIGRATION REVIEW\n"
            "IMMIGRATION COURT\n"
            "[City, State]\n\n"
            "____________________________________\n"
            "In the Matter of:                   )\n"
            "                                    )\n"
            "{client_name}                       )  A# {a_number}\n"
            "                                    )\n"
            "     Respondent.                    )\n"
            "____________________________________)\n\n"
            "MOTION [TYPE]\n\n"
            "Respondent, {client_name}, by and through undersigned counsel, "
            "respectfully submits this Motion [type] and states as follows:\n\n"
            "[Motion content here]\n\n"
            "WHEREFORE, Respondent respectfully requests that this Honorable Court "
            "grant the foregoing Motion.\n\n"
            "Respectfully submitted,\n\n"
            "____________________________\n"
            "[Attorney Name]\n"
            "[Bar Number]\n"
            "Counsel for Respondent\n"
            "[Date]"
        ),
    },
    {
        "id": "notice_of_appearance",
        "name": "Notice of Entry of Appearance",
        "category": "Notice",
        "body": (
            "UNITED STATES DEPARTMENT OF JUSTICE\n"
            "EXECUTIVE OFFICE FOR IMMIGRATION REVIEW\n\n"
            "NOTICE OF ENTRY OF APPEARANCE AS ATTORNEY OR REPRESENTATIVE\n"
            "BEFORE THE IMMIGRATION COURT\n\n"
            "I hereby enter my appearance as attorney for the respondent in the "
            "above-captioned matter.\n\n"
            "Respondent: {client_name}\n"
            "A-Number: {a_number}\n\n"
            "Attorney: [Attorney Name]\n"
            "Firm: O'Brien Immigration Law\n"
            "Address: [Office Address]\n"
            "Phone: [Phone]\n"
            "Email: [Email]\n"
            "Bar Number: [Bar Number]\n\n"
            "This form is submitted in accordance with 8 C.F.R. Section 1003.17 "
            "and the EOIR Practice Manual."
        ),
    },
    {
        "id": "hearing_confirmation",
        "name": "Hearing Confirmation Request",
        "category": "Other",
        "body": (
            "Dear Immigration Court Clerk,\n\n"
            "I am writing to confirm the hearing scheduled for the above-referenced "
            "respondent, {client_name} (A# {a_number}).\n\n"
            "Hearing Date: [Date]\n"
            "Hearing Time: [Time]\n"
            "Hearing Type: [Individual / Master Calendar]\n\n"
            "Please confirm that the above hearing remains on the Court's calendar. "
            "If there have been any changes to the date, time, or location, please "
            "notify our office at your earliest convenience.\n\n"
            "Thank you for your assistance.\n\n"
            "Sincerely,\n"
            "[Attorney Name]\n"
            "O'Brien Immigration Law"
        ),
    },
]

EOIR_CATEGORIES: list[str] = ["Motion", "Notice", "Certificate", "Other"]


def get_eoir_templates() -> list[dict]:
    """Load EOIR templates from config, seeding defaults on first call."""
    templates = load_config("eoir-templates")
    if templates is not None:
        return templates
    save_eoir_templates(copy.deepcopy(_DEFAULT_EOIR_TEMPLATES))
    return copy.deepcopy(_DEFAULT_EOIR_TEMPLATES)


def save_eoir_templates(templates: list[dict]) -> None:
    """Persist EOIR templates to config."""
    save_config("eoir-templates", templates)
