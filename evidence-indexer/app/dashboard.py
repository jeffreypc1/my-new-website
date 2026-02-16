"""Streamlit dashboard for the Evidence Indexer tool.

Part of the O'Brien Immigration Law tool suite. Provides a UI for managing
evidence packages, organizing exhibits, and compiling exhibit bundles
for immigration court filings.

Flow:
1. Sidebar: select a case and filter by document category.
2. Main area: sortable exhibit list with columns (Letter, Title, Category, Pages, Date).
3. "Add Document" form to upload or reference files.
4. Auto-numbering (Tab A, Tab B, ...) with manual override.
5. "Compile Bundle" generates merged PDF with tab pages.
6. "Export Index" generates Word doc exhibit list.
"""

import streamlit as st
import requests

API_BASE = "http://localhost:8000"

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Evidence Indexer",
    page_icon=None,
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

if "selected_case_id" not in st.session_state:
    st.session_state.selected_case_id = ""
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False

# ---------------------------------------------------------------------------
# Custom CSS
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
    .exhibit-badge {
        display: inline-block;
        background: #2b5797;
        color: #ffffff;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 700;
    }
    .category-tag {
        display: inline-block;
        background: #e2e8f0;
        color: #334155;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
    }
    .doc-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #1a2744;
    }
    .doc-meta {
        font-size: 0.82rem;
        color: #5a6a85;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="main-header">Evidence Indexer</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">Organize, index, and compile evidence packages for immigration filings</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Fetch document categories from API
# ---------------------------------------------------------------------------

categories: list[str] = []
try:
    resp = requests.get(f"{API_BASE}/api/categories", timeout=10)
    resp.raise_for_status()
    categories = resp.json()
except Exception:
    categories = [
        "Identity Documents",
        "Country Conditions",
        "Medical/Psychological",
        "Expert Reports",
        "Declarations",
        "Photographs",
        "Government Documents",
        "Correspondence",
        "Other",
    ]

# ---------------------------------------------------------------------------
# Sidebar: case selector
# ---------------------------------------------------------------------------

st.sidebar.header("Case")

# Fetch cases from the API
case_list: list[dict] = []
try:
    resp = requests.get(f"{API_BASE}/api/cases", timeout=10)
    resp.raise_for_status()
    case_list = resp.json()
except Exception:
    st.sidebar.warning(
        "Could not connect to API. Is the backend running on port 8000?"
    )

case_ids = [c.get("case_id", "") for c in case_list]

# Allow creating a new case inline
new_case_id = st.sidebar.text_input(
    "Case ID",
    value=st.session_state.selected_case_id,
    placeholder="e.g. GARCIA-2026-001",
)
if new_case_id:
    st.session_state.selected_case_id = new_case_id

# ---------------------------------------------------------------------------
# Sidebar: category filter
# ---------------------------------------------------------------------------

st.sidebar.markdown("---")
st.sidebar.header("Filter")

selected_categories = st.sidebar.multiselect(
    "Document Categories",
    options=categories,
    default=[],
    help="Leave empty to show all categories.",
)

# ---------------------------------------------------------------------------
# Sidebar: action buttons
# ---------------------------------------------------------------------------

st.sidebar.markdown("---")

if st.sidebar.button("Add Document", use_container_width=True):
    st.session_state.show_add_form = True

if st.sidebar.button("Export Index (Word)", use_container_width=True):
    if st.session_state.selected_case_id:
        try:
            resp = requests.post(
                f"{API_BASE}/api/cases/{st.session_state.selected_case_id}/export/index",
                timeout=30,
            )
            if resp.status_code == 200:
                st.sidebar.download_button(
                    "Download Index",
                    data=resp.content,
                    file_name=f"exhibit_index_{st.session_state.selected_case_id}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            else:
                st.sidebar.error("Failed to generate index.")
        except Exception as e:
            st.sidebar.error(f"Export failed: {e}")
    else:
        st.sidebar.warning("Enter a Case ID first.")

if st.sidebar.button("Compile Bundle (PDF)", use_container_width=True):
    if st.session_state.selected_case_id:
        try:
            resp = requests.post(
                f"{API_BASE}/api/cases/{st.session_state.selected_case_id}/export/bundle",
                timeout=120,
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("status") == "not_implemented":
                st.sidebar.info(result.get("message", "Bundle compilation coming soon."))
            else:
                st.sidebar.success("Bundle compiled successfully!")
        except Exception as e:
            st.sidebar.error(f"Compilation failed: {e}")
    else:
        st.sidebar.warning("Enter a Case ID first.")

# ---------------------------------------------------------------------------
# Main area: add document form
# ---------------------------------------------------------------------------

if st.session_state.show_add_form:
    st.markdown("### Add Document")

    with st.form("add_doc_form"):
        doc_title = st.text_input(
            "Document Title",
            placeholder="e.g. Applicant's Birth Certificate",
        )
        doc_category = st.selectbox(
            "Category",
            options=categories,
        )
        doc_description = st.text_area(
            "Description",
            placeholder="Brief description of the document and its relevance.",
            height=80,
        )
        doc_pages = st.number_input(
            "Page Count",
            min_value=0,
            value=0,
            help="Number of pages in the document.",
        )
        doc_box_url = st.text_input(
            "Box URL (optional)",
            placeholder="https://app.box.com/file/...",
            help="Link to the document in Box, if uploaded.",
        )

        # TODO: Add file upload support
        # uploaded_file = st.file_uploader(
        #     "Upload PDF",
        #     type=["pdf"],
        #     help="Upload a PDF document to add to the evidence package.",
        # )

        col_submit, col_cancel = st.columns(2)
        with col_submit:
            submitted = st.form_submit_button("Add Document", type="primary")
        with col_cancel:
            cancelled = st.form_submit_button("Cancel")

        if submitted and doc_title and st.session_state.selected_case_id:
            try:
                resp = requests.post(
                    f"{API_BASE}/api/cases/{st.session_state.selected_case_id}/documents",
                    json={
                        "title": doc_title,
                        "category": doc_category,
                        "description": doc_description,
                        "page_count": doc_pages,
                        "box_url": doc_box_url,
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                st.session_state.show_add_form = False
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add document: {e}")
        elif submitted and not doc_title:
            st.warning("Document title is required.")
        elif submitted and not st.session_state.selected_case_id:
            st.warning("Enter a Case ID in the sidebar first.")

        if cancelled:
            st.session_state.show_add_form = False
            st.rerun()

# ---------------------------------------------------------------------------
# Main area: exhibit list
# ---------------------------------------------------------------------------

st.markdown("### Exhibits")

if st.session_state.selected_case_id:
    # Fetch documents for the selected case
    documents: list[dict] = []
    try:
        case_data = None
        for c in case_list:
            if c.get("case_id") == st.session_state.selected_case_id:
                case_data = c
                break
        # TODO: Fetch documents from a dedicated endpoint
        # For now, documents are managed in-memory via the API
    except Exception:
        pass

    # Display hint when no documents exist yet
    # TODO: Fetch actual documents from the API
    st.caption(
        "Documents will appear here after adding them via the 'Add Document' button. "
        "Each document is automatically assigned an exhibit letter (Tab A, Tab B, etc.)."
    )

    # Placeholder table header
    header_cols = st.columns([1, 4, 2, 1, 2])
    with header_cols[0]:
        st.markdown("**Exhibit**")
    with header_cols[1]:
        st.markdown("**Document Title**")
    with header_cols[2]:
        st.markdown("**Category**")
    with header_cols[3]:
        st.markdown("**Pages**")
    with header_cols[4]:
        st.markdown("**Date Added**")

    st.markdown("---")

    # TODO: Render actual documents from the API
    # Each row should include:
    # - Exhibit letter badge (Tab A, Tab B, ...)
    # - Document title (clickable to edit)
    # - Category tag
    # - Page count
    # - Date added
    # - Edit/delete buttons
    #
    # Example row rendering:
    # st.markdown(
    #     f'<span class="exhibit-badge">Tab {doc["exhibit_letter"]}</span>',
    #     unsafe_allow_html=True,
    # )

    st.caption(
        "Tip: Use the sidebar buttons to export the exhibit index as a Word document "
        "or compile all exhibits into a single PDF bundle with tab divider pages."
    )
else:
    st.info("Enter a Case ID in the sidebar to manage its evidence package.")
