"""Reusable Google Doc Creator component.

Copies a Google Docs template, logs metadata to the Salesforce Google_Doc__c
custom object, and renders a Streamlit button with success/error feedback.
"""

from __future__ import annotations

import streamlit as st


def render_google_doc_button(
    template_id: str,
    file_name: str,
    contact_id: str,
    legal_case_id: str | None = None,
    replacements: dict[str, str] | None = None,
    folder_id: str = "",
    button_label: str = "Export to Google Doc",
    key: str = "gdoc_export",
) -> dict | None:
    """Render a button that creates a Google Doc and logs it to Salesforce.

    Workflow:
        1. Copies the Google Docs template (template_id) into the target folder.
        2. Fills placeholders from the replacements dict via batchUpdate.
        3. Creates a Google_Doc__c record in Salesforce linking the new doc
           to the given Contact (and optionally Legal Case).
        4. Displays a success message with links to the Google Doc and SF record.

    Args:
        template_id: Google Docs template file ID to copy.
        file_name: Name for the new document.
        contact_id: Salesforce Contact record Id (required).
        legal_case_id: Salesforce Legal Case record Id (optional; left null if None).
        replacements: Placeholder → replacement text for the template.
        folder_id: Google Drive folder ID to place the copy in.
        button_label: Text displayed on the button.
        key: Streamlit widget key.

    Returns:
        Dict with doc_url, sf_record_id, sf_record_url on last success; else None.
    """
    from shared.google_upload import copy_template_and_fill
    from shared.salesforce_client import create_google_doc_record

    _result_key = f"_gdoc_result_{key}"

    if st.button(button_label, use_container_width=True, key=key):
        with st.spinner("Creating Google Doc..."):
            try:
                # Step 1: Copy template and fill placeholders
                doc_url = copy_template_and_fill(
                    template_id=template_id,
                    title=file_name,
                    replacements=replacements or {},
                    folder_id=folder_id,
                )

                # Step 2-3: Create Salesforce Google_Doc__c record
                sf_result = create_google_doc_record(
                    name=file_name,
                    google_doc_link=doc_url,
                    contact_id=contact_id,
                    legal_case_id=legal_case_id,
                )

                st.session_state[_result_key] = {
                    "doc_url": doc_url,
                    "sf_record_id": sf_result["id"],
                    "sf_record_url": sf_result["url"],
                    "name": file_name,
                }
            except Exception as e:
                st.error(f"Failed to create Google Doc: {e}")

    # Display persisted result
    result = st.session_state.get(_result_key)
    if result:
        st.success(
            f"Created **{result['name']}**  \n"
            f"[Open Google Doc]({result['doc_url']}) · "
            f"[View in Salesforce]({result['sf_record_url']})"
        )
    return result
