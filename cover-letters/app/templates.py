"""Cover letter template engine for the Cover Letter Generator.

Templates define the standard sections and boilerplate language for
immigration cover letters. A typical USCIS cover letter includes:

- Date and addressee (filing office / service center)
- RE: line identifying the client (name, A-number, receipt number)
- Purpose of filing (what benefit is being sought)
- List of enclosed forms and supporting documents
- Brief summary or argument (case-type dependent)
- Attorney information and signature block
- Certificate of service (if applicable)

Each case type has its own standard sections and required fields.
Templates are stored as structured dicts and rendered by substituting
case data into placeholder variables.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Standard sections for each case type
# ---------------------------------------------------------------------------

COVER_LETTER_TYPES: dict[str, dict] = {
    "Asylum": {
        "name": "Asylum Cover Letter",
        "description": "Cover letter for affirmative or defensive asylum applications (I-589).",
        "sections": [
            "date_and_addressee",
            "re_line",
            "purpose_of_filing",
            "enclosed_forms",          # I-589, supporting declarations, etc.
            "enclosed_evidence",       # Country conditions, personal evidence
            "legal_basis_summary",     # Brief reference to INA 208
            "attorney_signature",
        ],
        "required_fields": ["client_name", "a_number", "filing_office"],
    },
    "Family-Based": {
        "name": "Family-Based Petition Cover Letter",
        "description": "Cover letter for family-based immigrant petitions (I-130, I-485).",
        "sections": [
            "date_and_addressee",
            "re_line",
            "purpose_of_filing",
            "petitioner_beneficiary_info",
            "enclosed_forms",
            "enclosed_evidence",
            "attorney_signature",
        ],
        "required_fields": ["client_name", "filing_office"],
    },
    "Employment-Based": {
        "name": "Employment-Based Petition Cover Letter",
        "description": "Cover letter for employment-based petitions (I-140, I-485).",
        "sections": [
            "date_and_addressee",
            "re_line",
            "purpose_of_filing",
            "enclosed_forms",
            "enclosed_evidence",
            "attorney_signature",
        ],
        "required_fields": ["client_name", "filing_office"],
    },
    "VAWA": {
        "name": "VAWA Self-Petition Cover Letter",
        "description": "Cover letter for Violence Against Women Act self-petitions (I-360).",
        "sections": [
            "date_and_addressee",
            "re_line",
            "purpose_of_filing",
            "confidentiality_notice",  # VAWA confidentiality provisions
            "enclosed_forms",
            "enclosed_evidence",
            "legal_basis_summary",
            "attorney_signature",
        ],
        "required_fields": ["client_name", "filing_office"],
    },
    "U-Visa": {
        "name": "U-Visa Cover Letter",
        "description": "Cover letter for U nonimmigrant status petitions (I-918).",
        "sections": [
            "date_and_addressee",
            "re_line",
            "purpose_of_filing",
            "certification_reference",  # Law enforcement certification (I-918B)
            "enclosed_forms",
            "enclosed_evidence",
            "attorney_signature",
        ],
        "required_fields": ["client_name", "filing_office"],
    },
    "T-Visa": {
        "name": "T-Visa Cover Letter",
        "description": "Cover letter for T nonimmigrant status applications (I-914).",
        "sections": [
            "date_and_addressee",
            "re_line",
            "purpose_of_filing",
            "certification_reference",
            "enclosed_forms",
            "enclosed_evidence",
            "attorney_signature",
        ],
        "required_fields": ["client_name", "filing_office"],
    },
    "Removal Defense": {
        "name": "Removal Defense Cover Letter",
        "description": "Cover letter for filings with immigration court in removal proceedings.",
        "sections": [
            "date_and_addressee",
            "re_line",
            "case_posture",            # Current status of removal proceedings
            "purpose_of_filing",
            "enclosed_forms",
            "enclosed_evidence",
            "certificate_of_service",  # Required for court filings
            "attorney_signature",
        ],
        "required_fields": ["client_name", "a_number", "filing_office"],
    },
}


# ---------------------------------------------------------------------------
# Template loading and retrieval
# ---------------------------------------------------------------------------

def load_templates() -> list[dict]:
    """Load all available cover letter templates.

    Returns a list of template metadata dicts, one per case type defined
    in COVER_LETTER_TYPES. Each dict includes: id, name, case_type,
    description, and sections.

    TODO: Support loading custom templates from a JSON file or database
          so attorneys can create and save their own variants.
    TODO: Support firm-specific boilerplate loaded from Box or local storage.
    """
    templates: list[dict] = []
    for case_type, config in COVER_LETTER_TYPES.items():
        templates.append({
            "id": case_type.lower().replace("-", "_").replace(" ", "_"),
            "name": config["name"],
            "case_type": case_type,
            "description": config["description"],
            "sections": config["sections"],
        })
    return templates


def get_template(template_id: str) -> dict | None:
    """Retrieve a single template by its ID.

    Returns the full template dict or None if not found.

    TODO: Add support for versioned templates.
    """
    templates = load_templates()
    for t in templates:
        if t["id"] == template_id:
            return t
    return None


def render_template(template_id: str, case_data: dict) -> dict:
    """Render a cover letter by merging a template with case data.

    Produces the full cover letter text by iterating through each section
    defined in the template and substituting case data values into
    placeholder variables.

    Args:
        template_id: The template to render.
        case_data: Dict of case fields (client_name, a_number, etc.).

    Returns:
        Dict with keys:
        - text: The full rendered letter as a string.
        - sections: List of dicts with 'heading' and 'body' for each section.
        - warnings: List of warning messages (e.g. missing required fields).

    TODO: Implement actual rendering logic:
        - Build date/addressee block from filing_office
        - Build RE: line from client_name, a_number, receipt_number
        - Enumerate enclosed_documents as a numbered list
        - Insert case-type-specific boilerplate language
        - Add attorney signature block
    TODO: Support Jinja2 or similar templating for custom templates.
    """
    template = get_template(template_id)
    warnings: list[str] = []

    if template is None:
        return {
            "text": "",
            "sections": [],
            "warnings": [f"Template '{template_id}' not found."],
        }

    # Check for missing required fields
    config = COVER_LETTER_TYPES.get(template.get("case_type", ""), {})
    required = config.get("required_fields", [])
    for field in required:
        if not case_data.get(field):
            warnings.append(f"Missing required field: {field}")

    # TODO: Replace this stub with actual section-by-section rendering
    sections: list[dict] = []
    lines: list[str] = []

    for section_key in template.get("sections", []):
        heading = section_key.replace("_", " ").title()
        body = f"[{heading} content will be generated here]"
        sections.append({"heading": heading, "body": body})
        lines.append(f"--- {heading} ---")
        lines.append(body)
        lines.append("")

    rendered_text = "\n".join(lines)

    return {
        "text": rendered_text,
        "sections": sections,
        "warnings": warnings,
    }
