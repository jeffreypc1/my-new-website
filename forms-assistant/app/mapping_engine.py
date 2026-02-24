"""4-tier auto-mapping pipeline for form fields to Salesforce Contact fields.

When a form is ingested, this module runs each field through a tiered
matching pipeline:

    Tier 1 - Exact match against SF field labels (confidence 1.0)
    Tier 2 - Synonym dictionary lookup (confidence 0.95)
    Tier 3 - History match from previously approved mappings (confidence 0.85)
    Tier 4 - Fuzzy match via SequenceMatcher (confidence = ratio * 0.8, min 0.56)

Fields with a role other than "none" (attorney/preparer fields) are skipped
since they are not SF-mapped.
"""

from __future__ import annotations

import difflib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow imports from the monorepo shared/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.schema import FieldMapping, FormFieldSchema, MappingSet

MAPPINGS_DIR = Path(__file__).resolve().parent.parent / "data" / "mappings"

# ---------------------------------------------------------------------------
# Synonym dictionary
# ---------------------------------------------------------------------------
# Maps common form field labels (lowercased) to Salesforce Contact API names.
# Absorbs the keyword matching logic from shared.pdf_form_extractor.auto_suggest_roles().

# Maps common form field labels (lowercased) to (SF API name, SF object).
SYNONYM_MAP: dict[str, tuple[str, str]] = {
    "family name": ("LastName", "Contact"),
    "last name": ("LastName", "Contact"),
    "surname": ("LastName", "Contact"),
    "given name": ("FirstName", "Contact"),
    "first name": ("FirstName", "Contact"),
    "date of birth": ("Birthdate", "Contact"),
    "dob": ("Birthdate", "Contact"),
    "birth date": ("Birthdate", "Contact"),
    "a number": ("A_Number__c", "Contact"),
    "a-number": ("A_Number__c", "Contact"),
    "alien registration number": ("A_Number__c", "Contact"),
    "gender": ("Gender__c", "Contact"),
    "sex": ("Gender__c", "Contact"),
    "marital status": ("Marital_status__c", "Contact"),
    "country of nationality": ("Country__c", "Contact"),
    "country of citizenship": ("Country__c", "Contact"),
    "country of birth": ("Country__c", "Contact"),
    "city of birth": ("City_of_Birth__c", "Contact"),
    "place of birth": ("City_of_Birth__c", "Contact"),
    "street": ("MailingStreet", "Contact"),
    "address": ("MailingStreet", "Contact"),
    "mailing address": ("MailingStreet", "Contact"),
    "city": ("MailingCity", "Contact"),
    "state": ("MailingState", "Contact"),
    "province": ("MailingState", "Contact"),
    "zip": ("MailingPostalCode", "Contact"),
    "zip code": ("MailingPostalCode", "Contact"),
    "postal code": ("MailingPostalCode", "Contact"),
    "phone": ("Phone", "Contact"),
    "telephone": ("Phone", "Contact"),
    "daytime phone": ("Phone", "Contact"),
    "mobile": ("MobilePhone", "Contact"),
    "cell phone": ("MobilePhone", "Contact"),
    "email": ("Email", "Contact"),
    "e-mail": ("Email", "Contact"),
    "email address": ("Email", "Contact"),
    "language": ("Best_Language__c", "Contact"),
    "case number": ("CaseNumber__c", "Contact"),
    "immigration status": ("Immigration_Status__c", "Contact"),
    "spouse name": ("Spouse_Name__c", "Contact"),
}


# ---------------------------------------------------------------------------
# SF field catalog helpers
# ---------------------------------------------------------------------------

def _get_sf_field_labels(object_name: str = "Contact") -> dict[str, str]:
    """Return a dict of {api_name: label} for fields on a Salesforce object.

    Tries the live Salesforce describe first.  If that fails (offline mode,
    missing credentials, etc.), falls back to the static ``SF_FIELD_LABELS``
    dict for Contact only.
    """
    try:
        from shared.salesforce_client import describe_object_fields

        raw = describe_object_fields(object_name)
        return {f["name"]: f["label"] for f in raw}
    except Exception:
        pass

    # Fallback: static dictionary from pdf_form_extractor (Contact only)
    if object_name == "Contact":
        try:
            from shared.pdf_form_extractor import SF_FIELD_LABELS

            return dict(SF_FIELD_LABELS)
        except Exception:
            pass

    return {}


def _get_all_sf_field_labels() -> dict[str, dict[str, str]]:
    """Return {object_name: {api_name: label}} for all form-relevant SF objects."""
    try:
        from shared.salesforce_client import FORM_SF_OBJECTS
    except ImportError:
        FORM_SF_OBJECTS = ["Contact"]

    result: dict[str, dict[str, str]] = {}
    for obj in FORM_SF_OBJECTS:
        result[obj] = _get_sf_field_labels(obj)
    return result


# ---------------------------------------------------------------------------
# History helpers
# ---------------------------------------------------------------------------

def _load_approved_history() -> dict[str, str]:
    """Build a lookup of previously approved mappings across all forms.

    Returns:
        dict mapping ``display_label`` (lowercased) to SF API field name,
        drawn from every approved ``FieldMapping`` found on disk.
    """
    history: dict[str, str] = {}

    if not MAPPINGS_DIR.exists():
        return history

    for path in MAPPINGS_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            ms = MappingSet.from_dict(data)
            for mapping in ms.mappings:
                if mapping.approved and mapping.sf_field:
                    # We need the display_label, which lives in the form schema
                    # not in the mapping itself.  The mapping stores field_id.
                    # We store label->sf_field using field_id as a proxy label
                    # but ideally we want the display_label.
                    # Store field_id lowered as key; the auto_map function will
                    # also check display_label against this.
                    history[mapping.field_id.lower()] = mapping.sf_field
        except Exception:
            continue

    return history


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def auto_map_fields(fields: list[FormFieldSchema], form_id: str) -> MappingSet:
    """Run the 4-tier auto-mapping pipeline on a list of form fields.

    Searches across Contact, Contact_Plus__c, and Contact_Plus_1__c
    (Contact first, then custom objects) and sets sf_object accordingly.

    Args:
        fields: The form's field schemas (from ingestion).
        form_id: Unique identifier of the form being mapped.

    Returns:
        A ``MappingSet`` containing one ``FieldMapping`` per eligible field.
    """
    all_sf_labels = _get_all_sf_field_labels()  # {obj: {api: label}}

    # Build per-object reverse lookups: label_lower -> (api_name, object_name)
    label_to_api: dict[str, tuple[str, str]] = {}
    # Flat list of (label, api_name, object_name) for fuzzy matching
    sf_label_triples: list[tuple[str, str, str]] = []

    # Process objects in priority order (Contact first)
    try:
        from shared.salesforce_client import FORM_SF_OBJECTS
    except ImportError:
        FORM_SF_OBJECTS = ["Contact"]

    for obj_name in FORM_SF_OBJECTS:
        obj_labels = all_sf_labels.get(obj_name, {})
        for api, label in obj_labels.items():
            lower = label.lower()
            # Only keep the first (highest-priority) object for each label
            if lower not in label_to_api:
                label_to_api[lower] = (api, obj_name)
            sf_label_triples.append((label, api, obj_name))

    # Tier 3 history
    history = _load_approved_history()

    mappings: list[FieldMapping] = []

    for fld in fields:
        # Skip attorney/preparer fields — they aren't SF-mapped
        if fld.role != "none":
            continue

        display_lower = fld.display_label.lower().strip()
        matched_sf = ""
        matched_obj = "Contact"
        method = ""
        confidence = 0.0

        # Tier 1: Exact match against SF field labels (case-insensitive)
        if display_lower in label_to_api:
            matched_sf, matched_obj = label_to_api[display_lower]
            method = "exact"
            confidence = 1.0

        # Tier 2: Synonym dictionary (now returns (field, object) tuples)
        if not matched_sf and display_lower in SYNONYM_MAP:
            matched_sf, matched_obj = SYNONYM_MAP[display_lower]
            method = "synonym"
            confidence = 0.95

        # Tier 3: History match (previously approved in another form)
        if not matched_sf:
            hist_val = history.get(display_lower) or history.get(fld.field_id.lower())
            if hist_val:
                matched_sf = hist_val
                matched_obj = "Contact"  # history doesn't track object yet
                method = "history"
                confidence = 0.85

        # Tier 4: Fuzzy match via SequenceMatcher (across all objects)
        if not matched_sf and sf_label_triples:
            best_ratio = 0.0
            best_api = ""
            best_obj = "Contact"
            for label, api, obj in sf_label_triples:
                ratio = difflib.SequenceMatcher(
                    None, display_lower, label.lower()
                ).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_api = api
                    best_obj = obj
            # Only accept if ratio >= 0.7; final confidence = ratio * 0.8
            if best_ratio >= 0.7:
                matched_sf = best_api
                matched_obj = best_obj
                method = "fuzzy"
                confidence = round(best_ratio * 0.8, 4)

        mappings.append(
            FieldMapping(
                form_id=form_id,
                field_id=fld.field_id,
                sf_object=matched_obj,
                sf_field=matched_sf,
                match_method=method,
                confidence=confidence,
                approved=False,
                approved_by="",
                approved_at="",
            )
        )

    return MappingSet(
        form_id=form_id,
        mappings=mappings,
        last_auto_mapped=datetime.now(timezone.utc).isoformat(),
        version=1,
    )
