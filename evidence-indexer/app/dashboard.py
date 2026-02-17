"""Evidence Indexer -- Streamlit dashboard.

Full evidence management UI for organizing, indexing, and exporting exhibit
packages for immigration court filings. Works entirely with local JSON
persistence (no API server required).

Part of the O'Brien Immigration Law tool suite.
"""

from __future__ import annotations

import html as html_mod
import io
import sys
from datetime import date
from pathlib import Path
from typing import Any

import streamlit as st

from app.evidence import (
    DOCUMENT_CATEGORIES,
    EvidenceItem,
    _docs_to_items,
    add_document,
    delete_case,
    generate_index_docx,
    list_cases,
    load_case,
    new_case_id,
    remove_document,
    save_case,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.google_upload import upload_to_google_docs
from shared.client_banner import render_client_banner
from shared.tool_notes import render_tool_notes

# -- Page config --------------------------------------------------------------

st.set_page_config(
    page_title="Evidence Indexer -- O'Brien Immigration Law",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -- CSS ----------------------------------------------------------------------

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Hide Streamlit chrome */
#MainMenu, footer,
div[data-testid="stToolbar"] { display: none !important; }

.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Navigation bar */
.nav-bar {
    display: flex;
    align-items: center;
    padding: 10px 4px;
    margin: -1rem 0 1.2rem 0;
    border-bottom: 1px solid rgba(0,0,0,0.07);
}
.nav-back {
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 500;
    color: #0066CC;
    text-decoration: none;
    min-width: 150px;
}
.nav-back:hover { color: #004499; text-decoration: underline; }
.nav-title {
    flex: 1;
    text-align: center;
    font-family: 'Inter', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: #1a2744;
    letter-spacing: -0.02em;
}
.nav-firm {
    font-weight: 400;
    color: #86868b;
    font-size: 0.85rem;
    margin-left: 8px;
}
.nav-spacer { min-width: 150px; }

/* Exhibit badge */
.exhibit-badge {
    display: inline-block;
    background: #2b5797;
    color: #ffffff;
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 700;
    white-space: nowrap;
}

/* Category tag */
.category-tag {
    display: inline-block;
    background: #e2e8f0;
    color: #334155;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
}

/* Document title */
.doc-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #1a2744;
    line-height: 1.3;
}

/* Document meta */
.doc-meta {
    font-size: 0.82rem;
    color: #5a6a85;
}

/* Preview panel */
.preview-panel {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 18px 22px;
}
.preview-panel h4 {
    margin: 0 0 12px 0;
    font-size: 0.95rem;
    font-weight: 700;
    color: #1a2744;
}
.preview-panel table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}
.preview-panel th {
    background: #e2e8f0;
    color: #334155;
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.preview-panel td {
    padding: 7px 10px;
    border-bottom: 1px solid #e2e8f0;
    color: #334155;
}
.preview-panel tr:last-child td {
    border-bottom: none;
}

/* Saved toast */
.saved-toast {
    background: #dcfce7;
    color: #166534;
    padding: 8px 14px;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 600;
    margin-bottom: 12px;
}

/* Section label */
.section-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: #5a6a85;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 6px;
}

/* Add document row */
.add-doc-row {
    background: #f0f4fa;
    border: 1px dashed #c5d0e0;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 16px;
}

/* Exhibit row */
.exhibit-row {
    display: flex;
    align-items: center;
    padding: 10px 14px;
    border-radius: 8px;
    margin-bottom: 6px;
    border: 1px solid #e2e8f0;
    background: #fff;
    gap: 12px;
}
.exhibit-row:hover {
    border-color: #c5d0e0;
    background: #fafbfc;
}

/* Header row for exhibit table */
.exhibit-header {
    padding: 6px 14px;
    margin-bottom: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #5a6a85;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 50px 20px;
    color: #5a6a85;
}
.empty-state-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #1a2744;
    margin-bottom: 6px;
}
.empty-state-desc {
    font-size: 0.88rem;
}

/* Case card in sidebar saved cases list */
.case-option {
    font-size: 0.85rem;
}
</style>
""",
    unsafe_allow_html=True,
)

# -- Navigation bar -----------------------------------------------------------

st.markdown(
    """
<div class="nav-bar">
    <a href="http://localhost:8502" class="nav-back">&#8592; Staff Dashboard</a>
    <div class="nav-title">Evidence Indexer<span class="nav-firm">&mdash; O'Brien Immigration Law</span></div>
    <div class="nav-spacer"></div>
</div>
""",
    unsafe_allow_html=True,
)

render_client_banner()

# -- Session state defaults ---------------------------------------------------

_DEFAULTS: dict[str, Any] = {
    "case_id": None,
    "last_saved_msg": "",
    "show_add_form": False,
    "documents": [],
    "client_name": "",
    "a_number": "",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# -- Helpers ------------------------------------------------------------------


def _esc(text: str) -> str:
    """HTML-escape a string."""
    return html_mod.escape(str(text))


def _do_save() -> None:
    """Save the current case with documents to disk."""
    if not st.session_state.case_id:
        return
    save_case(
        case_id=st.session_state.case_id,
        client_name=st.session_state.client_name,
        a_number=st.session_state.a_number,
        documents=st.session_state.documents,
    )
    st.session_state.last_saved_msg = f"Saved at {date.today().isoformat()}"


def _do_load(case_id: str) -> None:
    """Load a case into session state."""
    case_data = load_case(case_id)
    if case_data is None:
        return
    st.session_state.case_id = case_data.get("id", case_id)
    st.session_state.client_name = case_data.get("client_name", "")
    st.session_state.a_number = case_data.get("a_number", "")
    st.session_state.documents = case_data.get("documents", [])
    st.session_state.last_saved_msg = ""
    st.session_state.show_add_form = False


def _do_new() -> None:
    """Reset session state for a fresh case."""
    st.session_state.case_id = new_case_id()
    st.session_state.client_name = ""
    st.session_state.a_number = ""
    st.session_state.documents = []
    st.session_state.last_saved_msg = ""
    st.session_state.show_add_form = False


def _build_preview_html(documents: list[dict[str, Any]]) -> str:
    """Render the exhibit index as an HTML table for the preview panel."""
    if not documents:
        return (
            '<div class="preview-panel">'
            "<h4>Exhibit Index Preview</h4>"
            '<p style="color:#5a6a85;font-size:0.88rem;">'
            "Add documents to see the exhibit index here.</p>"
            "</div>"
        )

    rows = ""
    for doc in documents:
        letter = _esc(doc.get("exhibit_letter", ""))
        title = _esc(doc.get("title", ""))
        category = _esc(doc.get("category", ""))
        pages = doc.get("page_count", 0)
        pages_str = str(pages) if pages else "--"
        rows += (
            f"<tr>"
            f"<td><strong>Tab {letter}</strong></td>"
            f"<td>{title}</td>"
            f"<td>{category}</td>"
            f"<td>{pages_str}</td>"
            f"</tr>"
        )

    return (
        '<div class="preview-panel">'
        "<h4>Exhibit Index Preview</h4>"
        "<table>"
        "<tr><th>Exhibit</th><th>Document Title</th><th>Category</th><th>Pages</th></tr>"
        f"{rows}"
        "</table>"
        "</div>"
    )


def _build_docx(client_name: str, documents: list[dict[str, Any]]) -> bytes:
    """Generate a .docx exhibit index from current documents."""
    items = _docs_to_items(documents)
    return generate_index_docx(items, case_name=client_name)


def _build_plain_text(documents: list[dict[str, Any]]) -> str:
    """Generate a plain-text exhibit index."""
    lines: list[str] = []
    lines.append("EXHIBIT INDEX")
    lines.append("=" * 60)

    if st.session_state.client_name:
        lines.append(f"In the Matter of: {st.session_state.client_name}")
    if st.session_state.a_number:
        lines.append(f"A-Number: {st.session_state.a_number}")
    lines.append("=" * 60)
    lines.append("")

    # Column header
    lines.append(f"{'Exhibit':<12} {'Document Title':<35} {'Category':<22} {'Pages':<6}")
    lines.append("-" * 76)

    for doc in documents:
        letter = f"Tab {doc.get('exhibit_letter', '')}"
        title = doc.get("title", "")
        category = doc.get("category", "")
        pages = str(doc.get("page_count", 0)) if doc.get("page_count") else ""
        # Truncate long titles
        if len(title) > 33:
            title = title[:30] + "..."
        if len(category) > 20:
            category = category[:17] + "..."
        lines.append(f"{letter:<12} {title:<35} {category:<22} {pages:<6}")

    lines.append("")
    lines.append(f"Total documents: {len(documents)}")
    total_pages = sum(d.get("page_count", 0) for d in documents)
    if total_pages:
        lines.append(f"Total pages: {total_pages}")
    lines.append("")
    lines.append(f"Generated: {date.today().strftime('%B %d, %Y')}")
    lines.append("O'Brien Immigration Law")
    return "\n".join(lines)


# -- Sidebar ------------------------------------------------------------------

# Track whether save was clicked (captured in sidebar, executed after sidebar)
_save_clicked = False
_load_case_id = None
_delete_case_id = None

with st.sidebar:
    # -- Cases section --
    st.markdown("#### Cases")

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("New", use_container_width=True, type="primary"):
            _do_new()
            st.rerun()
    with btn_col2:
        _save_clicked = st.button("Save", use_container_width=True)

    # Saved toast
    if st.session_state.last_saved_msg:
        st.markdown(
            f'<div class="saved-toast">{_esc(st.session_state.last_saved_msg)}</div>',
            unsafe_allow_html=True,
        )

    # Saved cases list
    saved_cases = list_cases()
    if saved_cases:
        case_options = {
            c["case_id"]: f"{c['client_name'] or 'Untitled'} ({c['document_count']} docs)"
            for c in saved_cases
        }
        selected_saved = st.selectbox(
            "Saved Cases",
            options=list(case_options.keys()),
            format_func=lambda x: case_options.get(x, x),
            index=None,
            placeholder="Select a case to load...",
        )

        load_del_col1, load_del_col2 = st.columns(2)
        with load_del_col1:
            if st.button("Load", use_container_width=True):
                if selected_saved:
                    _load_case_id = selected_saved
        with load_del_col2:
            if st.button("Delete", use_container_width=True):
                if selected_saved:
                    _delete_case_id = selected_saved

    st.divider()

    # -- Case info --
    st.markdown("#### Case Info")
    st.session_state.client_name = st.text_input(
        "Client Name",
        value=st.session_state.client_name,
        placeholder="e.g. Maria Garcia Lopez",
    )
    st.session_state.a_number = st.text_input(
        "A-Number",
        value=st.session_state.a_number,
        placeholder="e.g. 123-456-789",
    )

    st.divider()

    # -- Category filter --
    st.markdown("#### Filter by Category")
    selected_categories = st.multiselect(
        "Categories",
        options=DOCUMENT_CATEGORIES,
        default=[],
        label_visibility="collapsed",
        help="Leave empty to show all categories.",
    )

    st.divider()

    # -- Add Document button --
    if st.button("Add Document", use_container_width=True, type="primary"):
        if st.session_state.case_id:
            st.session_state.show_add_form = True
        else:
            st.warning("Create or load a case first.")

    render_tool_notes("evidence-indexer")


# -- Execute deferred sidebar actions (after sidebar renders) -----------------

if _save_clicked:
    if st.session_state.case_id:
        _do_save()
        st.rerun()

if _load_case_id:
    _do_load(_load_case_id)
    st.rerun()

if _delete_case_id:
    delete_case(_delete_case_id)
    # If we deleted the currently-loaded case, clear it
    if st.session_state.case_id == _delete_case_id:
        st.session_state.case_id = None
        st.session_state.client_name = ""
        st.session_state.a_number = ""
        st.session_state.documents = []
        st.session_state.last_saved_msg = ""
    st.rerun()

# -- Main area ----------------------------------------------------------------

if not st.session_state.case_id:
    st.markdown(
        '<div class="empty-state">'
        '<div class="empty-state-title">No case selected</div>'
        '<div class="empty-state-desc">'
        'Click "New" to start a new evidence package, or load a saved case from the sidebar.'
        "</div></div>",
        unsafe_allow_html=True,
    )
else:
    # Filter documents by category if filter is active
    all_documents = st.session_state.documents
    if selected_categories:
        display_documents = [
            d for d in all_documents
            if d.get("category") in selected_categories
        ]
    else:
        display_documents = all_documents

    # Two-column layout: left = exhibit list + add form, right = preview + export
    left_col, right_col = st.columns([3, 2], gap="large")

    with left_col:
        # -- Add document form --
        if st.session_state.show_add_form:
            st.markdown('<div class="add-doc-row">', unsafe_allow_html=True)
            st.markdown("**Add Document**")

            doc_title = st.text_input(
                "Document Title",
                placeholder="e.g. Applicant's Birth Certificate",
                key="add_doc_title",
            )
            doc_category = st.selectbox(
                "Category",
                options=DOCUMENT_CATEGORIES,
                key="add_doc_category",
            )
            doc_description = st.text_area(
                "Description",
                placeholder="Brief description of the document and its relevance.",
                height=80,
                key="add_doc_description",
            )

            add_col1, add_col2 = st.columns(2)
            with add_col1:
                doc_pages = st.number_input(
                    "Page Count",
                    min_value=0,
                    value=1,
                    key="add_doc_pages",
                )
            with add_col2:
                doc_box_url = st.text_input(
                    "Box URL (optional)",
                    placeholder="https://app.box.com/file/...",
                    key="add_doc_box_url",
                )

            submit_col, cancel_col = st.columns(2)
            with submit_col:
                if st.button("Add", type="primary", use_container_width=True):
                    if doc_title.strip():
                        from app.evidence import _exhibit_letter, _make_doc_id

                        new_doc: dict[str, Any] = {
                            "doc_id": _make_doc_id(),
                            "title": doc_title.strip(),
                            "category": doc_category,
                            "description": doc_description.strip(),
                            "page_count": int(doc_pages),
                            "box_url": doc_box_url.strip(),
                            "exhibit_letter": _exhibit_letter(len(st.session_state.documents)),
                            "date_added": date.today().isoformat(),
                        }
                        st.session_state.documents.append(new_doc)
                        st.session_state.show_add_form = False
                        st.rerun()
                    else:
                        st.warning("Document title is required.")
            with cancel_col:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.show_add_form = False
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        # -- Exhibit list --
        doc_count = len(display_documents)
        total_pages = sum(d.get("page_count", 0) for d in display_documents)
        st.markdown(
            f"**Exhibits** ({doc_count} document{'s' if doc_count != 1 else ''}"
            f"{f', {total_pages} pages' if total_pages else ''})"
        )

        if not display_documents:
            if selected_categories and all_documents:
                st.caption("No documents match the selected category filter.")
            else:
                st.caption(
                    "No documents yet. Click 'Add Document' in the sidebar to get started."
                )
        else:
            # Header row
            hdr_cols = st.columns([1.2, 3.5, 2, 1, 0.8])
            with hdr_cols[0]:
                st.markdown(
                    '<div class="exhibit-header">Exhibit</div>',
                    unsafe_allow_html=True,
                )
            with hdr_cols[1]:
                st.markdown(
                    '<div class="exhibit-header">Title</div>',
                    unsafe_allow_html=True,
                )
            with hdr_cols[2]:
                st.markdown(
                    '<div class="exhibit-header">Category</div>',
                    unsafe_allow_html=True,
                )
            with hdr_cols[3]:
                st.markdown(
                    '<div class="exhibit-header">Pages</div>',
                    unsafe_allow_html=True,
                )
            with hdr_cols[4]:
                st.markdown(
                    '<div class="exhibit-header"></div>',
                    unsafe_allow_html=True,
                )

            # Document rows
            for doc in display_documents:
                row_cols = st.columns([1.2, 3.5, 2, 1, 0.8])

                letter = doc.get("exhibit_letter", "")
                title = doc.get("title", "")
                category = doc.get("category", "")
                pages = doc.get("page_count", 0)
                doc_id = doc.get("doc_id", "")

                with row_cols[0]:
                    st.markdown(
                        f'<span class="exhibit-badge">Tab {_esc(letter)}</span>',
                        unsafe_allow_html=True,
                    )

                with row_cols[1]:
                    st.markdown(
                        f'<span class="doc-title">{_esc(title)}</span>',
                        unsafe_allow_html=True,
                    )
                    if doc.get("description"):
                        st.markdown(
                            f'<span class="doc-meta">{_esc(doc["description"][:80])}</span>',
                            unsafe_allow_html=True,
                        )

                with row_cols[2]:
                    st.markdown(
                        f'<span class="category-tag">{_esc(category)}</span>',
                        unsafe_allow_html=True,
                    )

                with row_cols[3]:
                    st.markdown(
                        f'<span class="doc-meta">{pages if pages else "--"}</span>',
                        unsafe_allow_html=True,
                    )

                with row_cols[4]:
                    if st.button("X", key=f"del_{doc_id}", help="Remove document"):
                        # Remove from session state list and reassign letters
                        st.session_state.documents = [
                            d for d in st.session_state.documents
                            if d.get("doc_id") != doc_id
                        ]
                        # Reassign exhibit letters
                        from app.evidence import _exhibit_letter as _el
                        for idx, d in enumerate(st.session_state.documents):
                            d["exhibit_letter"] = _el(idx)
                        st.rerun()

    with right_col:
        # -- Live preview panel --
        preview_html = _build_preview_html(display_documents)
        st.markdown(preview_html, unsafe_allow_html=True)

        st.markdown("")

        # -- ICPM compliance checklist --
        if all_documents:
            categories_present = {d.get("category") for d in all_documents}
            icpm_checks = []
            if "Application / Petition" in categories_present:
                icpm_checks.append(("Application / forms included", True))
            else:
                icpm_checks.append(("Application / forms included", False))
            if "Declaration / Affidavit" in categories_present:
                icpm_checks.append(("Personal declaration included", True))
            else:
                icpm_checks.append(("Personal declaration included", False))
            if "Identity Documents" in categories_present:
                icpm_checks.append(("Identity documents included", True))
            else:
                icpm_checks.append(("Identity documents included", False))

            # Check if any foreign-language docs likely need translation
            has_translation = "Translation & Certification" in categories_present
            icpm_checks.append(("Translation certifications", has_translation))

            has_witness_list = "Witness List" in categories_present
            icpm_checks.append(("Witness list (ICPM 4.18)", has_witness_list))

            check_html = '<div style="margin-top:12px;"><strong style="font-size:0.85rem;color:#1a2744;">ICPM Compliance</strong>'
            for label, ok in icpm_checks:
                icon = "&#9745;" if ok else "&#9744;"
                color = "#166534" if ok else "#92400e"
                check_html += f'<div style="font-size:0.82rem;color:{color};padding:2px 0;">{icon} {label}</div>'
            check_html += "</div>"
            st.markdown(check_html, unsafe_allow_html=True)

        st.markdown("")

        # -- Export buttons --
        if display_documents:
            st.markdown('<div class="section-label">Export</div>', unsafe_allow_html=True)

            exp_col1, exp_col2 = st.columns(2)

            with exp_col1:
                plain_text = _build_plain_text(all_documents)
                safe_name = (st.session_state.client_name or "evidence").replace(" ", "_")
                st.download_button(
                    "Download .txt",
                    data=plain_text,
                    file_name=f"Exhibit_Index_{safe_name}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

            with exp_col2:
                docx_bytes = _build_docx(st.session_state.client_name, all_documents)
                if docx_bytes:
                    st.download_button(
                        "Download .docx",
                        data=docx_bytes,
                        file_name=f"Exhibit_Index_{safe_name}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
                    if st.button("Upload to Google Docs", use_container_width=True):
                        with st.spinner("Uploading to Google Docs..."):
                            try:
                                url = upload_to_google_docs(docx_bytes, f"Exhibit Index - {st.session_state.client_name or 'Evidence'}")
                                st.session_state.google_doc_url = url
                            except Exception as e:
                                st.error(f"Upload failed: {e}")
                    if st.session_state.get("google_doc_url"):
                        st.markdown(f"[Open Google Doc]({st.session_state.google_doc_url})")
                else:
                    st.caption("Word export requires python-docx package.")

        # -- Summary stats --
        if all_documents:
            st.markdown("")
            st.markdown('<div class="section-label">Summary</div>', unsafe_allow_html=True)

            category_counts: dict[str, int] = {}
            for doc in all_documents:
                cat = doc.get("category", "Other")
                category_counts[cat] = category_counts.get(cat, 0) + 1

            summary_parts = []
            for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
                summary_parts.append(f"{cat}: {count}")

            st.caption(" | ".join(summary_parts))
