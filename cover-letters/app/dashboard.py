"""Streamlit dashboard for the Cover Letter Generator.

Part of the O'Brien Immigration Law tool suite. Provides a UI for selecting
cover letter templates, entering case details, previewing the generated
letter, and exporting to Word / Google Docs.

Flow:
1. User selects a case type and template from the sidebar.
2. User fills in case details in the main form (client name, A-number, etc.).
3. User adds enclosed documents to the document list.
4. Clicking "Generate Preview" renders the cover letter from the template.
5. The preview area shows the formatted letter.
6. Clicking "Export to Word" generates a .docx file for download.
"""

import streamlit as st
import requests

API_BASE = "http://localhost:8000"

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Cover Letter Generator",
    page_icon=None,
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

if "preview_text" not in st.session_state:
    st.session_state.preview_text = ""
if "enclosed_docs" not in st.session_state:
    st.session_state.enclosed_docs = []
if "generated_sections" not in st.session_state:
    st.session_state.generated_sections = []

# ---------------------------------------------------------------------------
# Case types supported by the tool
# ---------------------------------------------------------------------------

CASE_TYPES = [
    "Asylum",
    "Family-Based",
    "Employment-Based",
    "VAWA",
    "U-Visa",
    "T-Visa",
    "Removal Defense",
]

# ---------------------------------------------------------------------------
# Sidebar: template and case type selection
# ---------------------------------------------------------------------------

st.sidebar.header("Cover Letter Settings")

case_type = st.sidebar.selectbox(
    "Case Type",
    options=CASE_TYPES,
    index=0,
    help="Select the immigration case type for the cover letter.",
)

# Fetch available templates from the API, filtered by case type
# TODO: Handle API connection errors gracefully
templates: list[dict] = []
try:
    resp = requests.get(
        f"{API_BASE}/api/templates",
        params={"case_type": case_type},
        timeout=10,
    )
    resp.raise_for_status()
    templates = resp.json()
except Exception:
    st.sidebar.warning(
        "Could not connect to API. Is the backend running on port 8000?"
    )

template_names = [t.get("name", t.get("id", "Unknown")) for t in templates]
selected_template_idx = st.sidebar.selectbox(
    "Template",
    options=range(len(template_names)) if template_names else [0],
    format_func=lambda i: template_names[i] if template_names else "No templates available",
    help="Choose a cover letter template for this case type.",
)

selected_template_id = (
    templates[selected_template_idx]["id"] if templates else None
)

# ---------------------------------------------------------------------------
# Sidebar: firm / attorney info
# TODO: Load defaults from .env or settings file
# ---------------------------------------------------------------------------

st.sidebar.markdown("---")
st.sidebar.header("Attorney Info")
attorney_name = st.sidebar.text_input("Attorney Name", value="")
bar_number = st.sidebar.text_input("Bar Number", value="")
firm_name = st.sidebar.text_input("Firm Name", value="O'Brien Immigration Law")

# ---------------------------------------------------------------------------
# Main area: header
# ---------------------------------------------------------------------------

st.markdown("## Cover Letter Generator")
st.markdown(
    "Generate formatted cover letters for USCIS and immigration court filings."
)

# ---------------------------------------------------------------------------
# Main area: case details form
# ---------------------------------------------------------------------------

st.markdown("### Case Details")

col_left, col_right = st.columns(2)

with col_left:
    client_name = st.text_input(
        "Client Name",
        placeholder="e.g. Maria Garcia Lopez",
    )
    a_number = st.text_input(
        "A-Number",
        placeholder="e.g. A-123-456-789",
        help="Alien Registration Number",
    )
    receipt_number = st.text_input(
        "Receipt Number",
        placeholder="e.g. SRC-21-123-45678",
        help="USCIS receipt number, if available",
    )

with col_right:
    filing_office = st.text_input(
        "Filing Office / Service Center",
        placeholder="e.g. Nebraska Service Center",
        help="USCIS service center, field office, or immigration court",
    )
    # TODO: Add date fields (filing date, priority date) as needed
    # TODO: Add petitioner / beneficiary fields for family-based cases

# ---------------------------------------------------------------------------
# Main area: enclosed documents list
# ---------------------------------------------------------------------------

st.markdown("### Enclosed Documents")
st.caption(
    "List all forms and supporting documents being submitted with this filing."
)

# Input for adding a new document to the list
new_doc = st.text_input(
    "Add document",
    placeholder="e.g. Form I-589, Application for Asylum",
    key="new_doc_input",
)
if st.button("Add Document") and new_doc:
    st.session_state.enclosed_docs.append(new_doc)
    # TODO: Clear the input field after adding

# Display the current document list with remove buttons
if st.session_state.enclosed_docs:
    for i, doc in enumerate(st.session_state.enclosed_docs):
        doc_col, rm_col = st.columns([6, 1])
        with doc_col:
            st.text(f"{i + 1}. {doc}")
        with rm_col:
            if st.button("Remove", key=f"rm_doc_{i}"):
                st.session_state.enclosed_docs.pop(i)
                st.rerun()
else:
    st.info("No documents added yet. Add enclosed forms and evidence above.")

# ---------------------------------------------------------------------------
# Main area: generate preview
# ---------------------------------------------------------------------------

st.markdown("---")

if st.button("Generate Preview", type="primary", disabled=not selected_template_id):
    # TODO: Call the /api/generate endpoint with the form data
    # and display the rendered cover letter in the preview area.
    if not client_name:
        st.warning("Please enter a client name.")
    else:
        try:
            resp = requests.post(
                f"{API_BASE}/api/generate",
                json={
                    "template_id": selected_template_id,
                    "case_data": {
                        "case_type": case_type,
                        "client_name": client_name,
                        "a_number": a_number,
                        "receipt_number": receipt_number,
                        "filing_office": filing_office,
                        "enclosed_documents": st.session_state.enclosed_docs,
                    },
                },
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()
            st.session_state.preview_text = result.get("rendered_text", "")
            st.session_state.generated_sections = result.get("sections", [])
            if result.get("warnings"):
                for w in result["warnings"]:
                    st.warning(w)
        except Exception as e:
            st.error(f"Generation failed: {e}")

# ---------------------------------------------------------------------------
# Main area: preview display
# ---------------------------------------------------------------------------

st.markdown("### Preview")

if st.session_state.preview_text:
    # Show the rendered cover letter in an editable text area so the user
    # can make manual adjustments before exporting.
    edited_text = st.text_area(
        "Cover Letter Preview",
        value=st.session_state.preview_text,
        height=400,
        label_visibility="collapsed",
    )

    # --- Export controls ---
    export_col_left, export_col_right = st.columns(2)

    with export_col_left:
        # Plain text download
        st.download_button(
            "Download as Text",
            data=edited_text,
            file_name=f"cover_letter_{client_name or 'draft'}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with export_col_right:
        # DOCX export via API
        # TODO: Implement the actual DOCX export call to /api/export/docx
        if st.button("Export to Word", use_container_width=True):
            st.info(
                "Word export is not yet implemented. "
                "The exported .docx will include firm letterhead and "
                "proper formatting."
            )
            # TODO: POST to /api/export/docx, receive file bytes, offer download
else:
    st.caption(
        "Fill in the case details above and click 'Generate Preview' "
        "to see the cover letter."
    )
