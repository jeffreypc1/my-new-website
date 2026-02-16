"""Streamlit dashboard for the Brief Builder tool.

Provides a UI for selecting brief types, entering case information,
drafting section content with legal boilerplate, inserting citations,
and exporting to Word format.

Part of the O'Brien Immigration Law tool suite.
"""

import requests
import streamlit as st

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Brief Builder",
    page_icon=None,
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS (matching Country Reports tool style)
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main-header {
        color: #1a2744;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0;
    }
    .sub-header {
        color: #5a6a85;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .section-note {
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 8px 12px;
        font-size: 0.85rem;
        color: #5a6a85;
        margin-bottom: 8px;
    }
    .boilerplate-block {
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-radius: 4px;
        padding: 10px 12px;
        font-size: 0.85rem;
        line-height: 1.5;
        margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="main-header">Brief Builder</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">Draft and assemble immigration law briefs '
    'with standard legal frameworks and citations</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "section_content" not in st.session_state:
    st.session_state.section_content = {}
if "citations" not in st.session_state:
    st.session_state.citations = []

# ---------------------------------------------------------------------------
# Sidebar: Brief type selector and case info
# ---------------------------------------------------------------------------

BRIEF_TYPE_OPTIONS = [
    "Asylum Merits Brief",
    "Motion to Reopen",
    "Appeal Brief",
    "Bond Brief",
    "Cancellation of Removal",
]

st.sidebar.header("Brief Configuration")

brief_type = st.sidebar.selectbox(
    "Brief Type",
    options=BRIEF_TYPE_OPTIONS,
    index=0,
    help="Select the type of brief to draft",
)

st.sidebar.markdown("---")
st.sidebar.header("Case Information")

client_name = st.sidebar.text_input(
    "Client Name",
    placeholder="e.g. Maria Garcia-Lopez",
)

a_number = st.sidebar.text_input(
    "A-Number",
    placeholder="e.g. A 012-345-678",
    help="Alien Registration Number",
)

court_or_office = st.sidebar.text_input(
    "Court / Office",
    placeholder="e.g. San Francisco Immigration Court",
    help="Immigration Court or USCIS office",
)

# TODO: Add IJ name field
# TODO: Add hearing date field
# TODO: Add opposing counsel / trial attorney field

st.sidebar.markdown("---")
st.sidebar.header("Tools")

# TODO: Add citation search/insertion tool in sidebar
# TODO: Add link to Country Reports tool for country conditions research

st.sidebar.caption(
    "Part of the O'Brien Immigration Law tool suite. "
    "Use the Country Reports tool to research country conditions."
)

# ---------------------------------------------------------------------------
# Load sections for the selected brief type
# ---------------------------------------------------------------------------

# Try to load from API; fall back to local import if API is unavailable
sections: list[dict] = []
try:
    resp = requests.get(
        f"{API_BASE}/api/sections/{brief_type}",
        timeout=5,
    )
    resp.raise_for_status()
    sections = resp.json()
except Exception:
    # Fall back to local sections module when API is not running
    from app.sections import load_sections
    try:
        sections = load_sections(brief_type)
    except ValueError:
        sections = []

# ---------------------------------------------------------------------------
# Main area: Brief sections
# ---------------------------------------------------------------------------

if not sections:
    st.warning(f"No sections defined for brief type: {brief_type}")
else:
    st.markdown(f"### {brief_type}")

    if client_name or a_number:
        caption_parts = []
        if client_name:
            caption_parts.append(f"In the Matter of: **{client_name}**")
        if a_number:
            caption_parts.append(f"A-Number: **{a_number}**")
        if court_or_office:
            caption_parts.append(f"Court: **{court_or_office}**")
        st.caption(" | ".join(caption_parts))

    for section in sections:
        section_key = section["key"]
        heading = section["heading"]
        subsections = section.get("subsections", [])
        boilerplate = section.get("boilerplate", "")

        with st.expander(heading, expanded=True):

            # Special note for country conditions section
            if section_key == "country_conditions":
                st.markdown(
                    '<div class="section-note">'
                    "This section integrates with the Country Reports tool. "
                    "Use the Country Reports Assembler to search and compile "
                    "country condition evidence, then import excerpts here."
                    "</div>",
                    unsafe_allow_html=True,
                )

            # Show boilerplate if available at the section level
            if boilerplate:
                st.markdown(
                    f'<div class="boilerplate-block">'
                    f"<strong>Standard language:</strong><br>{boilerplate}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            # Subsections
            if subsections:
                for sub in subsections:
                    sub_key = sub["key"]
                    sub_heading = sub["heading"]
                    sub_boilerplate = sub.get("boilerplate", "")

                    st.markdown(f"**{sub_heading}**")

                    if sub_boilerplate:
                        st.markdown(
                            f'<div class="boilerplate-block">'
                            f"<strong>Standard language:</strong><br>{sub_boilerplate}"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

                    content_key = f"content_{section_key}_{sub_key}"
                    st.text_area(
                        f"Content for {sub_heading}",
                        height=150,
                        key=content_key,
                        placeholder=f"Draft your {sub_heading.lower()} argument here...",
                        label_visibility="collapsed",
                    )

                    # TODO: Add citation insertion button per subsection
                    # TODO: Add "Insert boilerplate" button that pre-fills the text area

            else:
                # Single section without subsections
                content_key = f"content_{section_key}"
                st.text_area(
                    f"Content for {heading}",
                    height=200 if section_key == "statement_of_facts" else 150,
                    key=content_key,
                    placeholder=f"Draft your {heading.lower()} here...",
                    label_visibility="collapsed",
                )

            # Citation insertion placeholder
            st.caption("Citations: use [Ctrl+Shift+C] to insert a citation (coming soon)")
            # TODO: Implement citation search modal
            # TODO: Support Bluebook and immigration-specific citation formats
            # TODO: Allow drag-and-drop from Country Reports search results

# ---------------------------------------------------------------------------
# Export controls
# ---------------------------------------------------------------------------

st.markdown("---")

export_col_left, export_col_right = st.columns(2)

with export_col_left:
    if st.button("Export to Word (.docx)", use_container_width=True, type="primary"):
        # TODO: Gather all section content from session state
        # TODO: Build the ExportDocxRequest payload
        # TODO: POST to /api/export/docx and offer download

        # Collect section content
        section_payloads = []
        for section in sections:
            section_key = section["key"]
            heading = section["heading"]
            subsections = section.get("subsections", [])

            if subsections:
                for sub in subsections:
                    sub_key = sub["key"]
                    content_key = f"content_{section_key}_{sub_key}"
                    body = st.session_state.get(content_key, "")
                    if body.strip():
                        section_payloads.append({
                            "section_key": sub_key,
                            "heading": sub["heading"],
                            "body": body,
                            "citations": [],
                        })
            else:
                content_key = f"content_{section_key}"
                body = st.session_state.get(content_key, "")
                if body.strip():
                    section_payloads.append({
                        "section_key": section_key,
                        "heading": heading,
                        "body": body,
                        "citations": [],
                    })

        if not section_payloads:
            st.warning("No content to export. Draft at least one section first.")
        else:
            try:
                export_resp = requests.post(
                    f"{API_BASE}/api/export/docx",
                    json={
                        "brief_type": brief_type,
                        "case_info": {
                            "client_name": client_name,
                            "a_number": a_number,
                            "court_or_office": court_or_office,
                        },
                        "sections": section_payloads,
                    },
                    timeout=30,
                )
                export_resp.raise_for_status()
                filename = f"{brief_type.replace(' ', '_')}.docx"
                st.download_button(
                    "Download .docx",
                    data=export_resp.content,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            except Exception as e:
                st.error(f"Export failed: {e}")

with export_col_right:
    # TODO: Add Google Docs export (matching Country Reports tool pattern)
    st.button(
        "Export to Google Docs (coming soon)",
        use_container_width=True,
        disabled=True,
    )
