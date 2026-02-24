"""PDF AcroForm field extraction and filling via PyMuPDF.

Extracts fillable widget fields from USCIS PDF forms and fills them
with user-provided values. All pymupdf imports are lazy.
"""

from __future__ import annotations

import re


# -- Role definitions ---------------------------------------------------------

ROLE_GROUPS: dict[str, list[tuple[str, str]]] = {
    "Preparer": [
        ("preparer_name", "Preparer Name"),
        ("preparer_firm", "Preparer Firm"),
        ("preparer_address", "Preparer Address"),
        ("preparer_phone", "Preparer Phone"),
        ("preparer_email", "Preparer Email"),
        ("preparer_bar_number", "Preparer Bar Number"),
    ],
    "Attorney": [
        ("attorney_name", "Attorney Name"),
        ("attorney_bar_number", "Attorney Bar Number"),
        ("attorney_firm", "Attorney Firm"),
        ("attorney_address", "Attorney Address"),
        ("attorney_phone", "Attorney Phone"),
        ("attorney_email", "Attorney Email"),
    ],
}

ALL_ROLES: list[str] = ["none"] + [
    role for group in ROLE_GROUPS.values() for role, _ in group
]

# Salesforce Contact fields available for direct mapping on form fields
SF_FIELD_LABELS: dict[str, str] = {
    "FirstName": "First Name",
    "LastName": "Last Name",
    "A_Number__c": "A-Number",
    "Birthdate": "Date of Birth",
    "Gender__c": "Gender",
    "Country__c": "Country",
    "Pronoun__c": "Pronoun",
    "Email": "Email",
    "MobilePhone": "Mobile Phone",
    "Phone": "Phone",
    "MailingStreet": "Mailing Street",
    "MailingCity": "Mailing City",
    "MailingState": "Mailing State",
    "MailingPostalCode": "Mailing ZIP",
    "MailingCountry": "Mailing Country",
    "Immigration_Status__c": "Immigration Status",
    "Immigration_Court__c": "Immigration Court",
    "Legal_Case_Type__c": "Legal Case Type",
    "Client_Status__c": "Client Status",
    "Date_of_Most_Recent_US_Entry__c": "Last Entry Date",
    "Status_of_Last_Arrival__c": "Status of Last Arrival",
    "Place_of_Last_Arrival__c": "Place of Last Arrival",
    "Date_of_First_Entry_to_US__c": "First Entry Date",
    "Best_Language__c": "Best Language",
    "Marital_status__c": "Marital Status",
    "Spouse_Name__c": "Spouse Name",
    "Mother_s_First_Name__c": "Mother's First Name",
    "Mother_s_Last_Name__c": "Mother's Last Name",
    "Father_s_First_Name__c": "Father's First Name",
    "Father_s_Last_Name__c": "Father's Last Name",
    "City_of_Birth__c": "City of Birth",
    "CaseNumber__c": "Case Number",
    "Client_Case_Strategy__c": "Case Strategy",
    "Nexus__c": "Nexus",
    "PSG__c": "Particular Social Group",
    "Box_Folder_Id__c": "Box Folder ID",
}


# -- Auto-suggest roles -------------------------------------------------------

def _extract_part_number(raw_name: str) -> int | None:
    """Extract USCIS Part number from raw PDF field name (e.g., Pt1 -> 1)."""
    m = re.search(r"Pt(\d+)", raw_name)
    return int(m.group(1)) if m else None


def auto_suggest_roles(fields: list[dict]) -> list[dict]:
    """Auto-suggest role and sf_field mappings for extracted PDF fields.

    Uses keyword matching on display_label and positional hints from
    the raw pdf_field_name (Part numbers, page position) to guess
    which data source should fill each field.

    For applicant/client fields, sets ``sf_field`` to the Salesforce API
    name directly.  For preparer/attorney fields, sets ``role``.
    Returns the same list (mutated).
    """
    if not fields:
        return fields

    # Determine total pages for late-page heuristic
    max_page = max(f.get("page_number", 0) for f in fields)

    for field in fields:
        label = field.get("display_label", "").lower()
        raw = field.get("pdf_field_name", "")
        page = field.get("page_number", 0)
        part = _extract_part_number(raw)

        # Skip if already tagged
        if field.get("role", "none") != "none":
            continue
        if field.get("sf_field", ""):
            continue

        # -- Determine context: applicant vs preparer/attorney --
        # USCIS forms: Part 1-4 = applicant, higher parts = preparer/attorney
        is_applicant_context = True
        is_preparer_context = False
        is_attorney_context = False

        raw_lower = raw.lower()
        if "preparer" in label or "preparer" in raw_lower:
            is_preparer_context = True
            is_applicant_context = False
        elif "attorney" in label or "attorney" in raw_lower or "representative" in raw_lower:
            is_attorney_context = True
            is_applicant_context = False
        elif part is not None and part >= 6:
            # Late parts are usually preparer/attorney
            is_applicant_context = False
            is_preparer_context = True
        elif page >= max_page and max_page > 2:
            # Last page often has preparer/attorney fields
            is_applicant_context = False

        # -- Match patterns --
        role = None       # for preparer/attorney
        sf_field = None   # for applicant -> Salesforce

        # Name fields
        if _matches(label, ["family name", "last name", "surname"]):
            if is_preparer_context:
                role = "preparer_name"
            elif is_attorney_context:
                role = "attorney_name"
            else:
                sf_field = "LastName"
        elif _matches(label, ["given name", "first name"]) and "middle" not in label:
            if is_preparer_context:
                role = "preparer_name"
            elif is_attorney_context:
                role = "attorney_name"
            else:
                sf_field = "FirstName"
        elif _matches(label, ["middle name"]):
            pass  # no SF equivalent for middle name

        # Date of birth
        elif _matches(label, ["date of birth", "dob", "birth date"]):
            if is_applicant_context:
                sf_field = "Birthdate"

        # A-Number
        elif ("alien" in label and "number" in label) or \
             _matches(label, ["a number", "a-number"]):
            if is_applicant_context:
                sf_field = "A_Number__c"

        # SSN — no SF equivalent
        elif _matches(label, ["ssn", "social security"]):
            pass

        # Gender
        elif _matches(label, ["gender", "sex"]) and "marital" not in label:
            if is_applicant_context:
                sf_field = "Gender__c"

        # Marital status
        elif "marital" in label:
            if is_applicant_context:
                sf_field = "Marital_status__c"

        # Country of nationality
        elif "country" in label and ("nationality" in label or "citizenship" in label):
            if is_applicant_context:
                sf_field = "Country__c"

        # Country of birth
        elif "country" in label and "birth" in label:
            if is_applicant_context:
                sf_field = "Country__c"

        # City/place of birth
        elif ("city" in label and "birth" in label) or "place of birth" in label:
            if is_applicant_context:
                sf_field = "City_of_Birth__c"

        # Street / address
        elif _matches(label, ["street", "address"]):
            if is_preparer_context:
                role = "preparer_address"
            elif is_attorney_context:
                role = "attorney_address"
            elif is_applicant_context:
                sf_field = "MailingStreet"

        # City (non-birth)
        elif "city" in label and "birth" not in label:
            if is_applicant_context:
                sf_field = "MailingCity"

        # State / province
        elif _matches(label, ["state", "province"]) and "united states" not in label:
            if is_applicant_context:
                sf_field = "MailingState"

        # ZIP / postal
        elif _matches(label, ["zip", "postal"]):
            if is_applicant_context:
                sf_field = "MailingPostalCode"

        # Phone
        elif _matches(label, ["daytime phone", "phone", "telephone"]) and "mobile" not in label and "cell" not in label:
            if is_preparer_context:
                role = "preparer_phone"
            elif is_attorney_context:
                role = "attorney_phone"
            elif is_applicant_context:
                sf_field = "Phone"

        # Mobile
        elif _matches(label, ["mobile", "cell"]):
            if is_applicant_context:
                sf_field = "MobilePhone"

        # Email
        elif "email" in label or "e-mail" in label:
            if is_preparer_context:
                role = "preparer_email"
            elif is_attorney_context:
                role = "attorney_email"
            elif is_applicant_context:
                sf_field = "Email"

        # Bar number (preparer or attorney context)
        elif _matches(label, ["bar number", "uscis account", "attorney id"]):
            if is_attorney_context:
                role = "attorney_bar_number"
            elif is_preparer_context:
                role = "preparer_bar_number"

        # Firm / organization
        elif _matches(label, ["firm", "organization", "company"]):
            if is_preparer_context:
                role = "preparer_firm"
            elif is_attorney_context:
                role = "attorney_firm"

        # Preparer/attorney "print name" (full name field)
        elif "print name" in label or "full name" in label:
            if is_preparer_context:
                role = "preparer_name"
            elif is_attorney_context:
                role = "attorney_name"

        # Attorney-specific patterns
        elif _matches(label, ["attorney or representative", "attorney name"]):
            role = "attorney_name"

        # Language
        elif _matches(label, ["language"]) and is_applicant_context:
            sf_field = "Best_Language__c"

        if role:
            field["role"] = role
        if sf_field:
            field["sf_field"] = sf_field

    return fields


def _matches(text: str, patterns: list[str]) -> bool:
    """Check if any pattern appears in text."""
    return any(p in text for p in patterns)


# -- Field name parsing -------------------------------------------------------

def _parse_field_name(raw_name: str) -> str:
    """Heuristic: derive a human-readable label from a PDF field name.

    Examples:
        "form1[0].#subform[0].Pt1Line1a_FamilyName[0]" -> "Family Name"
        "Pt2Line3_MiddleName[0]"                       -> "Middle Name"
        "Line4a_StreetNumberAndName"                    -> "Street Number And Name"
        "USCISOnlineAcctNumber[0]"                      -> "USCIS Online Acct Number"
    """
    # Strip path prefix (everything before last dot-separated segment)
    name = raw_name.rsplit(".", 1)[-1]

    # Remove trailing array index like [0]
    name = re.sub(r"\[\d+\]$", "", name)

    # Remove leading PartN/LineN prefix like "Pt1Line1a_"
    name = re.sub(r"^Pt\d+Line\d+[a-z]?_?", "", name)
    name = re.sub(r"^Line\d+[a-z]?_?", "", name)

    # If nothing left after stripping, use original
    if not name.strip():
        name = re.sub(r"\[\d+\]$", "", raw_name.rsplit(".", 1)[-1])

    # Remove leading/trailing underscores
    name = name.strip("_")

    # Insert spaces before capitals: "FamilyName" -> "Family Name"
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    # Insert space between consecutive uppercase and lowercase: "USCISOnline" -> "USCIS Online"
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", name)

    # Replace underscores with spaces
    name = name.replace("_", " ")

    # Clean up multiple spaces
    name = re.sub(r"\s+", " ", name).strip()

    return name.title() if name else raw_name


# -- Extract fields -----------------------------------------------------------

def _extract_tooltip(doc, xref: int) -> str:
    """Extract the /TU (tooltip/alternate name) from a widget annotation."""
    try:
        obj_str = doc.xref_object(xref)
        # Try parenthesized string first — handle nested escaped parens
        tu_match = re.search(r"/TU\s*\(((?:[^()\\]|\\.)*)\)", obj_str)
        if tu_match:
            raw = tu_match.group(1)
            # Unescape PDF string escapes
            raw = raw.replace("\\(", "(").replace("\\)", ")").replace("\\\\", "\\")
            return raw.rstrip("\\")
        # Try hex string
        tu_hex = re.search(r"/TU\s*<([^>]*)>", obj_str)
        if tu_hex:
            raw = tu_hex.group(1)
            try:
                return bytes.fromhex(raw).decode("utf-16-be", errors="replace")
            except Exception:
                pass
    except Exception:
        pass
    return ""


def _parse_tooltip_to_label(tooltip: str, raw_name: str) -> tuple[str, str]:
    """Derive a human-readable label and section from a /TU tooltip string.

    Returns (display_label, section).
    Tooltip format: "Part. A. 1. Information About You. 5. Enter First Name."
    """
    if not tooltip:
        return _parse_field_name(raw_name), ""

    # Clean up escaped characters and trailing dots
    cleaned = tooltip.strip().rstrip(".")

    # Try to extract section: "Part. A. 1. Information About You"
    # Pattern: "Part[. ]X[. ]N[. ]Section Title[. ]N[. ]Field Description"
    section = ""
    label = cleaned

    # Match: "Part. A. 1. Section Title. N. Field description"
    # or: "Part A.I - Section Title. Field description"
    part_match = re.match(
        r"^Part\.?\s*([A-Z]+)\.?\s*(\d+)?\.?\s*([^.]+(?:\([^)]*\))?)\.\s*(.+)$",
        cleaned,
        re.IGNORECASE,
    )
    if part_match:
        part_letter = part_match.group(1).upper()
        part_num = part_match.group(2) or ""
        section_title = part_match.group(3).strip()
        remainder = part_match.group(4).strip()
        section = f"Part {part_letter}"
        if part_num:
            section += f".{part_num}"
        section += f" - {section_title}"

        # Remainder may start with a line number like "5. Enter First Name"
        line_match = re.match(r"^(\d+[a-z]?)\.?\s*(.+)$", remainder)
        if line_match:
            label = line_match.group(2).strip().rstrip(".")
        else:
            label = remainder.rstrip(".")
    else:
        # No section detected — use the whole tooltip as label
        label = cleaned

    # Clean up common prefixes like "Enter ", "Select "
    for prefix in ("Enter ", "Select "):
        if label.startswith(prefix) and len(label) > len(prefix) + 3:
            label = label[len(prefix):]

    # Title case if it's all lowercase or has weird casing
    if label == label.lower() or label == label.upper():
        label = label.title()

    return label, section


def extract_form_fields(pdf_bytes: bytes) -> list[dict]:
    """Extract all AcroForm widget fields from a PDF.

    Args:
        pdf_bytes: Raw bytes of the PDF file.

    Returns:
        List of field dicts with keys: pdf_field_name, display_label,
        field_type, page_number, rect, options, required, role, section,
        help_text, tooltip.
    """
    import pymupdf  # lazy import

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    fields: list[dict] = []
    seen_names: set[str] = set()

    for page_num in range(len(doc)):
        page = doc[page_num]
        widgets = page.widgets()
        if not widgets:
            continue
        for widget in widgets:
            fname = widget.field_name or ""
            if not fname or fname in seen_names:
                continue
            seen_names.add(fname)

            # Map widget field type
            wtype = widget.field_type
            if wtype == 0:      # text
                ftype = "text"
            elif wtype == 1:    # checkbox / button
                ftype = "checkbox"
            elif wtype == 2:    # list box
                ftype = "select"
            elif wtype == 3:    # combo box
                ftype = "combo"
            else:
                ftype = "text"

            # Get options for list/combo fields
            options = []
            if widget.choice_values:
                options = list(widget.choice_values)

            rect = list(widget.rect) if widget.rect else [0, 0, 0, 0]

            # Extract tooltip for better display names and sections
            tooltip = _extract_tooltip(doc, widget.xref)
            display_label, tooltip_section = _parse_tooltip_to_label(tooltip, fname)

            section = tooltip_section if tooltip_section else f"Page {page_num + 1}"

            fields.append({
                "pdf_field_name": fname,
                "display_label": display_label,
                "field_type": ftype,
                "page_number": page_num,
                "rect": rect,
                "options": options,
                "required": False,
                "role": "none",
                "sf_field": "",
                "section": section,
                "help_text": tooltip,
                "tooltip": tooltip,
            })

    doc.close()
    return fields


# -- Fill PDF -----------------------------------------------------------------

def fill_pdf_form(pdf_bytes: bytes, field_values: dict[str, str]) -> bytes:
    """Fill a PDF form's AcroForm fields and return completed PDF bytes.

    Args:
        pdf_bytes: Raw bytes of the blank PDF template.
        field_values: Mapping of pdf_field_name -> value to fill.

    Returns:
        Bytes of the filled PDF.
    """
    import pymupdf  # lazy import

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")

    for page in doc:
        widgets = page.widgets()
        if not widgets:
            continue
        for widget in widgets:
            fname = widget.field_name or ""
            if fname in field_values:
                val = field_values[fname]
                if widget.field_type == 1:  # checkbox
                    # Checkboxes: set to "Yes"/"Off" or the on-value
                    if val and str(val).lower() not in ("", "false", "no", "off", "0"):
                        widget.field_value = True
                    else:
                        widget.field_value = False
                else:
                    widget.field_value = str(val)
                widget.update()

    filled = doc.tobytes(deflate=True, garbage=3)
    doc.close()
    return filled


def extract_text_blocks(pdf_bytes: bytes) -> list[dict]:
    """Extract text blocks from a non-fillable PDF for overlay-based form filling.

    Returns list of dicts with: text, page_number, rect (bounding box), font_size.
    Useful for identifying where to overlay text on non-fillable PDFs.
    """
    import pymupdf

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    blocks = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text_dict = page.get_text("dict")
        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:  # text blocks only
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    bbox = span.get("bbox", [0, 0, 0, 0])
                    blocks.append({
                        "text": text,
                        "page_number": page_num,
                        "rect": list(bbox),
                        "font_size": span.get("size", 12),
                    })

    doc.close()
    return blocks


def overlay_text_on_pdf(pdf_bytes: bytes, overlays: list[dict]) -> bytes:
    """Overlay text onto a non-fillable PDF at specified positions.

    Args:
        pdf_bytes: Raw bytes of the PDF.
        overlays: List of dicts with: text, page_number, rect [x0, y0, x1, y1],
                  font_size (optional, default 10).

    Returns:
        Bytes of the modified PDF.
    """
    import pymupdf

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")

    for overlay in overlays:
        page_num = overlay.get("page_number", 0)
        if page_num >= len(doc):
            continue
        page = doc[page_num]
        rect = overlay.get("rect", [0, 0, 100, 20])
        text = overlay.get("text", "")
        font_size = overlay.get("font_size", 10)

        r = pymupdf.Rect(rect)
        page.insert_textbox(
            r, text,
            fontsize=font_size,
            fontname="helv",
            color=(0, 0, 0),
        )

    result = doc.tobytes(deflate=True, garbage=3)
    doc.close()
    return result
