"""Email service — template merging and sending via Salesforce.

Resolves {field_name} placeholders against a client SF record,
then sends via SF REST API (emailSimple action) which auto-logs
the email on the Contact's Activity History.

Usage:
    from shared.email_service import merge_template, send_email
"""

from __future__ import annotations

import re

# Friendly placeholder names → SF API field names
_ALIAS_MAP = {
    "first_name": "FirstName",
    "last_name": "LastName",
    "name": "Name",
    "a_number": "A_Number__c",
    "country": "Country__c",
    "language": "Best_Language__c",
    "email": "Email",
    "phone": "Phone",
    "mobile": "MobilePhone",
    "dob": "Birthdate",
    "gender": "Gender__c",
    "marital_status": "Marital_status__c",
    "immigration_status": "Immigration_Status__c",
    "court": "Immigration_Court__c",
    "case_type": "Legal_Case_Type__c",
    "case_number": "CaseNumber__c",
    "client_status": "Client_Status__c",
    "city_of_birth": "City_of_Birth__c",
    "spouse": "Spouse_Name__c",
    "customer_id": "Customer_ID__c",
}


def merge_template(subject: str, body: str, client_record: dict) -> tuple[str, str]:
    """Replace {field_name} placeholders with values from the client record.

    Supports both friendly aliases (e.g. {first_name}) and raw SF API names
    (e.g. {FirstName}). Unresolved placeholders are left as-is so the user
    can fill them manually.

    Returns (merged_subject, merged_body).
    """

    def _replace(match: re.Match) -> str:
        key = match.group(1)
        # Try direct SF field name first
        val = client_record.get(key)
        if val:
            return str(val)
        # Try alias map
        sf_field = _ALIAS_MAP.get(key.lower())
        if sf_field:
            val = client_record.get(sf_field)
            if val:
                return str(val)
        # Leave unresolved
        return match.group(0)

    pattern = r"\{(\w+)\}"
    return re.sub(pattern, _replace, subject), re.sub(pattern, _replace, body)


def send_email(
    sf_connection,
    contact_id: str,
    to_email: str,
    subject: str,
    body: str,
    sender_name: str,
) -> dict:
    """Send an email via Salesforce emailSimple action.

    The email is automatically logged on the Contact record as an
    Activity (Task + EmailMessage).

    Args:
        sf_connection: simple_salesforce.Salesforce instance
        contact_id: SF Contact record ID (18-char)
        to_email: recipient email address
        subject: email subject line
        body: email body (plain text)
        sender_name: display name for the sender

    Returns:
        dict with "success" (bool) and "message" or "error" keys.
    """
    try:
        result = sf_connection.restful(
            "actions/standard/emailSimple",
            method="POST",
            json={
                "inputs": [
                    {
                        "emailBody": body,
                        "emailSubject": subject,
                        "emailAddresses": to_email,
                        "targetObjectId": contact_id,
                        "saveAsActivity": True,
                        "senderDisplayName": sender_name,
                    }
                ]
            },
        )
        # SF returns a list of action results
        if isinstance(result, list) and result:
            action_result = result[0]
            if action_result.get("isSuccess"):
                return {"success": True, "message": "Email sent and logged on contact."}
            else:
                errors = action_result.get("errors", [])
                error_msg = errors[0].get("message", "Unknown error") if errors else "Unknown error"
                return {"success": False, "error": error_msg}
        return {"success": True, "message": "Email sent."}
    except Exception as e:
        return {"success": False, "error": str(e)}
