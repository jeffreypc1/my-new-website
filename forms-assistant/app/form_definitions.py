"""Form field definitions for the Forms Assistant tool.

Provides structured metadata for USCIS immigration forms including field
definitions, section layouts, validation rules, and filing requirements.

Part of the O'Brien Immigration Law tool suite.
"""

from dataclasses import dataclass, field


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

SUPPORTED_FORMS: dict[str, dict] = {
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
}


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
            field_type="phone",
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
# Validation stubs
# ---------------------------------------------------------------------------

def validate_field(field_def: FormField, value: str) -> list[str]:
    """Validate a single form field value against its definition.

    Args:
        field_def: The FormField definition with validation rules.
        value: The user-provided value for the field.

    Returns:
        List of validation error messages. Empty list means valid.

    TODO: Implement pattern matching validation (regex).
    TODO: Implement date format validation.
    TODO: Implement required field checking.
    TODO: Implement field-type-specific validation (phone, email, etc.).
    """
    errors: list[str] = []

    if field_def.required and not value.strip():
        errors.append(f"{field_def.name} is required.")

    # TODO: Check validation_rules patterns
    # TODO: Validate date formats
    # TODO: Validate select fields against allowed options

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

    TODO: Implement full field-by-field validation.
    TODO: Cross-reference field dependencies (e.g. spouse fields only
          required if marital_status is "Married").
    """
    form_meta = SUPPORTED_FORMS.get(form_id)
    if not form_meta:
        return {"error": f"Unknown form: {form_id}"}

    # Use I-589 fields if available; otherwise return basic info
    if form_id == "I-589":
        all_fields = [f for section_fields in I589_FIELDS.values() for f in section_fields]
    else:
        # TODO: Add detailed field definitions for other forms
        return {
            "total_fields": 0,
            "completed_fields": 0,
            "required_missing": [],
            "completion_pct": 0,
            "errors": ["Detailed field definitions not yet available for this form."],
        }

    total = len(all_fields)
    completed = sum(1 for f in all_fields if data.get(f.name, "").strip())
    required_missing = [
        f.name for f in all_fields
        if f.required and not data.get(f.name, "").strip()
    ]
    pct = round((completed / total) * 100) if total > 0 else 0

    return {
        "total_fields": total,
        "completed_fields": completed,
        "required_missing": required_missing,
        "completion_pct": pct,
        "errors": [],
    }
