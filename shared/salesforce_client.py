"""Salesforce client for pulling client data by Customer ID.

Shared module used across all office dashboard tools. Uses
simple-salesforce with username/password auth via a single
service account.

Credentials are read from environment variables:
    SF_USERNAME, SF_PASSWORD, SF_SECURITY_TOKEN,
    SF_CONSUMER_KEY, SF_CONSUMER_SECRET
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# Load .env from the parent project directory (where SF credentials live)
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if _ENV_PATH.exists():
    from dotenv import load_dotenv

    load_dotenv(_ENV_PATH)


def _get_connection():
    """Create and return a Salesforce connection (lazy, cached)."""
    from simple_salesforce import Salesforce

    return Salesforce(
        username=os.environ["SF_USERNAME"],
        password=os.environ["SF_PASSWORD"],
        security_token=os.environ["SF_SECURITY_TOKEN"],
        consumer_key=os.environ["SF_CONSUMER_KEY"],
        consumer_secret=os.environ["SF_CONSUMER_SECRET"],
    )


# Cache the connection so we don't re-auth on every call
_sf = None


def _sf_conn():
    global _sf
    if _sf is None:
        _sf = _get_connection()
    return _sf


def reset_connection():
    """Force a fresh connection on next call (e.g. after token expiry)."""
    global _sf
    _sf = None


def describe_contact_fields() -> list[dict]:
    """Return all fields on the Contact object.

    Each dict has: name (API name), label (human-readable), type, length.
    Sorted alphabetically by label.
    """
    sf = _sf_conn()
    desc = sf.Contact.describe()
    fields = [
        {
            "name": f["name"],
            "label": f["label"],
            "type": f["type"],
            "length": f.get("length", 0),
        }
        for f in desc["fields"]
    ]
    fields.sort(key=lambda f: f["label"].lower())
    return fields


def get_client(customer_id: str, fields: list[str] | None = None) -> dict | None:
    """Fetch a single Contact by Customer_ID__c.

    Args:
        customer_id: The 4-5 digit client number.
        fields: List of Salesforce API field names to return.
                If None, returns a default set of common fields.

    Returns:
        A dict of field values, or None if no match found.
    """
    sf = _sf_conn()

    if fields is None:
        fields = DEFAULT_FIELDS

    field_list = ", ".join(fields)
    query = f"SELECT {field_list} FROM Contact WHERE Customer_ID__c = '{customer_id}' LIMIT 1"

    result = sf.query(query)
    records = result.get("records", [])
    if not records:
        return None

    record = records[0]
    # Strip Salesforce metadata
    return {k: v for k, v in record.items() if k != "attributes"}


def get_lc_tasks(contact_sf_id: str) -> list[dict]:
    """Fetch LC_Task__c records related to a Contact.

    Args:
        contact_sf_id: The Salesforce record Id of the Contact.

    Returns:
        List of dicts with 'Id', 'Name', and 'For__c' fields.
    """
    sf = _sf_conn()
    query = (
        f"SELECT Id, Name, For__c FROM LC_Task__c "
        f"WHERE Contact__c = '{contact_sf_id}' ORDER BY Name"
    )
    result = sf.query(query)
    records = result.get("records", [])
    return [
        {k: v for k, v in r.items() if k != "attributes"}
        for r in records
    ]


def create_lc_task(contact_sf_id: str, description: str) -> str:
    """Create a new LC_Task__c record linked to a Contact.

    Args:
        contact_sf_id: The Salesforce record Id of the Contact.
        description: The value for the For__c field.

    Returns:
        The new record's Salesforce Id.
    """
    sf = _sf_conn()
    result = sf.LC_Task__c.create({
        "Contact__c": contact_sf_id,
        "For__c": description,
    })
    return result["id"]


def update_lc_task(task_sf_id: str, description: str) -> None:
    """Update the For__c field on an existing LC_Task__c record."""
    sf = _sf_conn()
    sf.LC_Task__c.update(task_sf_id, {"For__c": description})


def delete_lc_task(task_sf_id: str) -> None:
    """Delete an LC_Task__c record from Salesforce."""
    sf = _sf_conn()
    sf.LC_Task__c.delete(task_sf_id)


def update_client(sf_id: str, updates: dict) -> None:
    """Push field updates back to Salesforce for a Contact.

    Args:
        sf_id: The Salesforce record Id (from get_client's "Id" field).
        updates: Dict of {API_field_name: new_value} to update.
    """
    sf = _sf_conn()
    sf.Contact.update(sf_id, updates)


def create_google_doc_record(
    name: str,
    google_doc_link: str,
    contact_id: str,
    legal_case_id: str | None = None,
) -> dict:
    """Create a Google_Doc__c record in Salesforce.

    Args:
        name: Document name.
        google_doc_link: URL of the Google Doc.
        contact_id: Salesforce Contact record Id.
        legal_case_id: Salesforce Legal Case record Id (optional).

    Returns:
        Dict with 'id' (record Id) and 'url' (Salesforce record URL).
    """
    sf = _sf_conn()
    data: dict = {
        "Name": name,
        "Google_Doc_Link__c": google_doc_link,
        "Contact__c": contact_id,
    }
    if legal_case_id:
        data["Legal_Case__c"] = legal_case_id
    result = sf.Google_Doc__c.create(data)
    record_id = result["id"]
    record_url = f"https://{sf.sf_instance}/{record_id}"
    return {"id": record_id, "url": record_url}


def upload_file_to_contact(
    contact_sf_id: str,
    file_bytes: bytes,
    file_name: str,
    file_extension: str = "docx",
    title: str = "",
) -> str:
    """Upload a file to a Salesforce Contact's Files (ContentVersion).

    Args:
        contact_sf_id: The Salesforce record Id of the Contact.
        file_bytes: Raw file content bytes.
        file_name: Base file name (without extension).
        file_extension: File extension (default "docx").
        title: Optional title for the file; defaults to file_name.

    Returns:
        The new ContentVersion record Id.
    """
    import base64

    sf = _sf_conn()
    result = sf.ContentVersion.create({
        "Title": title or file_name,
        "PathOnClient": f"{file_name}.{file_extension}",
        "VersionData": base64.b64encode(file_bytes).decode("utf-8"),
        "FirstPublishLocationId": contact_sf_id,
    })
    return result["id"]


def get_field_metadata(field_names: list[str] | None = None) -> dict:
    """Return metadata for Contact fields including picklist values.

    Returns a dict keyed by API name: {type, label, picklistValues, updateable}.
    Cached after first call.
    """
    global _field_meta_cache
    if _field_meta_cache is not None:
        if field_names:
            return {k: v for k, v in _field_meta_cache.items() if k in field_names}
        return _field_meta_cache

    sf = _sf_conn()
    desc = sf.Contact.describe()
    meta = {}
    for f in desc["fields"]:
        meta[f["name"]] = {
            "label": f["label"],
            "type": f["type"],
            "updateable": f.get("updateable", False),
            "picklistValues": [
                {"label": pv["label"], "value": pv["value"]}
                for pv in f.get("picklistValues", [])
                if pv.get("active", True)
            ],
        }
    _field_meta_cache = meta
    if field_names:
        return {k: v for k, v in meta.items() if k in field_names}
    return meta


_field_meta_cache = None


# ---------------------------------------------------------------------------
# Active client persistence (shared across all tools)
# ---------------------------------------------------------------------------

_ACTIVE_CLIENT_PATH = Path(__file__).resolve().parent.parent / "data" / "active_client.json"


def save_active_client(record: dict) -> None:
    """Save the active client record to a shared JSON file."""
    _ACTIVE_CLIENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _ACTIVE_CLIENT_PATH.write_text(json.dumps(record, indent=2, default=str))


def load_active_client() -> dict | None:
    """Load the active client from the shared JSON file."""
    if not _ACTIVE_CLIENT_PATH.exists():
        return None
    try:
        return json.loads(_ACTIVE_CLIENT_PATH.read_text())
    except Exception:
        return None


def clear_active_client() -> None:
    """Remove the active client file."""
    if _ACTIVE_CLIENT_PATH.exists():
        _ACTIVE_CLIENT_PATH.unlink()


# Default fields to pull (grouped by use case)
DEFAULT_FIELDS = [
    # Core identity
    "Id",
    "Customer_ID__c",
    "FirstName",
    "LastName",
    "Name",
    "A_Number__c",
    "Birthdate",
    "Gender__c",
    "Country__c",
    "Pronoun__c",
    # Contact info
    "Email",
    "MobilePhone",
    "Phone",
    "MailingStreet",
    "MailingCity",
    "MailingState",
    "MailingPostalCode",
    "MailingCountry",
    # Immigration-specific
    "Immigration_Status__c",
    "Immigration_Court__c",
    "Legal_Case_Type__c",
    "Client_Status__c",
    "Date_of_Most_Recent_US_Entry__c",
    "Status_of_Last_Arrival__c",
    "Place_of_Last_Arrival__c",
    "Date_of_First_Entry_to_US__c",
    "Best_Language__c",
    "Marital_status__c",
    # Family
    "Spouse_Name__c",
    "Mother_s_First_Name__c",
    "Mother_s_Last_Name__c",
    "Father_s_First_Name__c",
    "Father_s_Last_Name__c",
    "City_of_Birth__c",
    # Case info
    "CaseNumber__c",
    "Client_Case_Strategy__c",
    "Nexus__c",
    "PSG__c",
    "Box_Folder_ID__c",
]
