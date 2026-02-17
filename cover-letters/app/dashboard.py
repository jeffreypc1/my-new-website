"""Cover Letter Generator — Streamlit dashboard.

Production-quality UI for generating immigration cover letters with
live preview, enclosed document management, draft persistence, and
Word/text export. Works entirely offline without the API server.
"""

from __future__ import annotations

import html as html_mod
import io
import sys
from datetime import date
from pathlib import Path

import streamlit as st
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from app.drafts import delete_draft, list_drafts, load_draft, new_draft_id, save_draft
from app.templates import (
    CASE_TYPES,
    TEMPLATES,
    get_filing_office_address,
    get_filing_offices,
    get_standard_docs,
    render_cover_letter,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.google_upload import upload_to_google_docs
from shared.client_banner import render_client_banner
from shared.tool_notes import render_tool_notes
try:
    from shared.draft_box import render_draft_box
except ImportError:
    render_draft_box = None
try:
    from shared.tool_help import render_tool_help
except ImportError:
    render_tool_help = None

# -- Page config --------------------------------------------------------------

st.set_page_config(
    page_title="Cover Letter Generator — O'Brien Immigration Law",
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

/* Header */
.cl-header {
    color: #1a2744;
    font-size: 1.8rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin-bottom: 0;
}
.cl-sub {
    color: #5a6a85;
    font-size: 0.95rem;
    margin-bottom: 0.5rem;
}

/* Section labels */
.section-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: #5a6a85;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 4px;
    margin-top: 12px;
}

/* Document checklist item */
.doc-item {
    font-size: 0.88rem;
    padding: 4px 0;
    color: #1a2744;
}

/* Preview panel (letter style) */
.preview-panel {
    font-family: 'Times New Roman', Times, serif;
    font-size: 0.85rem;
    line-height: 1.7;
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 28px 32px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    max-height: 75vh;
    overflow-y: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
}
.preview-panel .letter-date {
    margin-bottom: 12px;
}
.preview-panel .letter-addr {
    margin-bottom: 12px;
    line-height: 1.5;
}
.preview-panel .letter-re {
    margin-bottom: 12px;
    line-height: 1.5;
}
.preview-panel .letter-re strong {
    font-weight: bold;
}
.preview-panel .letter-body {
    margin-bottom: 10px;
    text-align: justify;
}
.preview-panel .letter-docs {
    margin: 10px 0 10px 20px;
    line-height: 1.6;
}
.preview-panel .letter-sig {
    margin-top: 20px;
    line-height: 1.8;
}
.preview-panel .letter-cert {
    margin-top: 28px;
    padding-top: 16px;
    border-top: 1px solid #ddd;
}
.preview-panel .conf-notice {
    background: #fff8f0;
    border: 1px solid #f0d0a0;
    border-radius: 4px;
    padding: 10px 14px;
    margin-bottom: 12px;
    font-size: 0.82rem;
    color: #8b4513;
    font-style: italic;
}

/* Draft badge */
.draft-badge {
    display: inline-block;
    padding: 3px 10px;
    font-size: 0.7rem;
    font-weight: 600;
    background: #e8f0fe;
    color: #1a73e8;
    border-radius: 12px;
    margin-bottom: 8px;
}

/* Saved confirmation */
.saved-toast {
    font-size: 0.8rem;
    color: #2e7d32;
    font-weight: 600;
}

/* Custom doc add row */
.add-doc-row {
    display: flex;
    gap: 8px;
    align-items: flex-end;
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
    <div class="nav-title">Cover Letter Generator<span class="nav-firm">&mdash; O'Brien Immigration Law</span></div>
    <div class="nav-spacer"></div>
</div>
""",
    unsafe_allow_html=True,
)

render_client_banner()
if render_tool_help:
    render_tool_help("cover-letters")

# -- Session state defaults ---------------------------------------------------

_DEFAULTS: dict = {
    "draft_id": None,
    "last_saved_msg": "",
    "enclosed_docs": [],
    "custom_docs": [],
    "doc_descriptions": {},
    "prev_case_type": None,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.draft_id is None:
    st.session_state.draft_id = new_draft_id()


# -- Helpers ------------------------------------------------------------------

def _build_enclosed_docs_list() -> list[dict[str, str]]:
    """Collect the currently selected enclosed documents with descriptions."""
    docs: list[dict[str, str]] = []
    # Standard docs that are checked
    for doc_name in st.session_state.get("enclosed_docs", []):
        desc = st.session_state.get("doc_descriptions", {}).get(doc_name, "")
        docs.append({"name": doc_name, "description": desc})
    # Custom docs
    for doc_name in st.session_state.get("custom_docs", []):
        desc = st.session_state.get("doc_descriptions", {}).get(doc_name, "")
        docs.append({"name": doc_name, "description": desc})
    return docs


def _do_save(case_type: str) -> None:
    """Save the current state as a draft."""
    client = {
        "name": st.session_state.get("inp_client_name", ""),
        "a_number": st.session_state.get("inp_a_number", ""),
        "receipt_number": st.session_state.get("inp_receipt_number", ""),
    }
    attorney = {
        "name": st.session_state.get("inp_attorney_name", ""),
        "bar_number": st.session_state.get("inp_bar_number", ""),
        "firm_name": st.session_state.get("inp_firm_name", "O'Brien Immigration Law"),
        "firm_address": st.session_state.get("inp_firm_address", ""),
    }
    filing_office = st.session_state.get("inp_filing_office", "")
    enclosed = _build_enclosed_docs_list()
    save_draft(
        st.session_state.draft_id,
        case_type,
        client,
        attorney,
        filing_office,
        enclosed,
    )
    name = client["name"] or "draft"
    st.session_state.last_saved_msg = f"Saved -- {name}"


def _do_load(draft_id: str) -> None:
    """Load a draft into session state."""
    draft = load_draft(draft_id)
    if not draft:
        return
    st.session_state.draft_id = draft["id"]
    st.session_state.inp_case_type = draft.get("case_type", CASE_TYPES[0])

    c = draft.get("client", {})
    st.session_state.inp_client_name = c.get("name", "")
    st.session_state.inp_a_number = c.get("a_number", "")
    st.session_state.inp_receipt_number = c.get("receipt_number", "")

    a = draft.get("attorney", {})
    st.session_state.inp_attorney_name = a.get("name", "")
    st.session_state.inp_bar_number = a.get("bar_number", "")
    st.session_state.inp_firm_name = a.get("firm_name", "O'Brien Immigration Law")
    st.session_state.inp_firm_address = a.get("firm_address", "")

    st.session_state.inp_filing_office = draft.get("filing_office", "")

    # Restore enclosed docs
    enclosed = draft.get("enclosed_docs", [])
    standard = get_standard_docs(draft.get("case_type", ""))
    standard_set = set(standard)
    checked = []
    custom = []
    descs: dict[str, str] = {}
    for doc in enclosed:
        name = doc.get("name", "")
        desc = doc.get("description", "")
        if name in standard_set:
            checked.append(name)
        else:
            custom.append(name)
        if desc:
            descs[name] = desc
    st.session_state.enclosed_docs = checked
    st.session_state.custom_docs = custom
    st.session_state.doc_descriptions = descs
    st.session_state.prev_case_type = draft.get("case_type", "")


def _do_new() -> None:
    """Start a fresh cover letter."""
    st.session_state.draft_id = new_draft_id()
    st.session_state.last_saved_msg = ""
    st.session_state.enclosed_docs = []
    st.session_state.custom_docs = []
    st.session_state.doc_descriptions = {}
    st.session_state.prev_case_type = None
    for k in (
        "inp_client_name", "inp_a_number", "inp_receipt_number",
        "inp_attorney_name", "inp_bar_number", "inp_firm_address",
        "inp_filing_office", "inp_case_type",
    ):
        if k in st.session_state:
            del st.session_state[k]
    if "inp_firm_name" in st.session_state:
        del st.session_state["inp_firm_name"]


def _build_preview_html(
    letter_text: str,
    case_type: str,
) -> str:
    """Convert the plain-text cover letter into styled HTML for the preview."""
    esc = html_mod.escape
    tpl = TEMPLATES.get(case_type, {})

    lines = letter_text.split("\n")
    parts: list[str] = []

    # If VAWA, show a confidentiality badge
    if "confidentiality_notice" in tpl:
        notice = tpl["confidentiality_notice"]
        parts.append(f'<div class="conf-notice">{esc(notice)}</div>')

    # Render the plain text directly -- it is already well structured
    for line in lines:
        escaped = esc(line)
        if line.startswith("RE: "):
            parts.append(f"<strong>{escaped}</strong>")
        elif line.startswith("    A# ") or line.startswith("    Receipt#") or (line.startswith("    ") and not line.startswith("    ") + "  "):
            parts.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{esc(line.strip())}")
        elif line == "CERTIFICATE OF SERVICE":
            parts.append(f'<div class="letter-cert"><strong>{escaped}</strong></div>')
        elif line.startswith("____"):
            parts.append(f"<br>{escaped}")
        else:
            parts.append(escaped)

    return "<br>".join(parts)


def _build_docx(letter_text: str, attorney_name: str, firm_name: str) -> bytes:
    """Build a Word document from the rendered cover letter text."""
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    def _run(para, txt, size=12, bold=False):
        r = para.add_run(txt)
        r.font.name = "Times New Roman"
        r.font.size = Pt(size)
        r.bold = bold
        return r

    lines = letter_text.split("\n")
    for line in lines:
        p = doc.add_paragraph()
        is_bold = line.startswith("RE:") or line == "CERTIFICATE OF SERVICE"
        _run(p, line, bold=is_bold)
        fmt = p.paragraph_format
        fmt.space_after = Pt(0)
        fmt.space_before = Pt(0)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# -- Sidebar ------------------------------------------------------------------

with st.sidebar:
    # Draft management
    st.markdown("#### Drafts")
    btn_cols = st.columns(2)
    with btn_cols[0]:
        if st.button("New", use_container_width=True):
            _do_new()
            st.rerun()
    with btn_cols[1]:
        save_clicked = st.button("Save", use_container_width=True, type="primary")

    saved_drafts = list_drafts()
    if saved_drafts:
        labels_map = {
            d["id"]: f"{d['client_name']} -- {d['case_type']}"
            for d in saved_drafts
        }
        draft_ids = list(labels_map.keys())
        selected_draft = st.selectbox(
            "Load a saved draft",
            options=[""] + draft_ids,
            format_func=lambda x: labels_map.get(x, "Select..."),
            label_visibility="collapsed",
        )
        load_cols = st.columns(2)
        with load_cols[0]:
            if selected_draft and st.button("Load", use_container_width=True):
                _do_load(selected_draft)
                st.rerun()
        with load_cols[1]:
            if selected_draft and st.button("Delete", use_container_width=True):
                delete_draft(selected_draft)
                st.rerun()

    if st.session_state.last_saved_msg:
        st.markdown(
            f'<div class="saved-toast">{html_mod.escape(st.session_state.last_saved_msg)}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # Case type
    case_type = st.selectbox(
        "Case Type",
        options=CASE_TYPES,
        key="inp_case_type",
    )

    # If case type changed, reset enclosed docs to the new defaults
    if st.session_state.prev_case_type != case_type:
        st.session_state.enclosed_docs = list(get_standard_docs(case_type))
        st.session_state.custom_docs = []
        st.session_state.doc_descriptions = {}
        st.session_state.prev_case_type = case_type

    st.divider()

    # Attorney info
    st.markdown("#### Attorney / Firm")
    attorney_name = st.text_input("Attorney Name", key="inp_attorney_name")
    bar_number = st.text_input("Bar Number", key="inp_bar_number")
    firm_name = st.text_input(
        "Firm Name",
        value="O'Brien Immigration Law",
        key="inp_firm_name",
    )
    firm_address = st.text_area(
        "Firm Address",
        key="inp_firm_address",
        height=80,
        placeholder="123 Main Street\nSuite 400\nCity, State ZIP",
    )

    st.divider()

    # Client info
    st.markdown("#### Client")
    client_name = st.text_input(
        "Client Name",
        key="inp_client_name",
        placeholder="e.g. Maria Garcia Lopez",
    )
    a_number = st.text_input(
        "A-Number",
        key="inp_a_number",
        placeholder="e.g. 123-456-789",
    )
    receipt_number = st.text_input(
        "Receipt Number",
        key="inp_receipt_number",
        placeholder="e.g. SRC-21-123-45678",
    )

    st.divider()

    # Filing office
    st.markdown("#### Filing Office")
    office_options = get_filing_offices(case_type)
    filing_office = st.selectbox(
        "Filing Office",
        options=office_options if office_options else ["Other"],
        key="inp_filing_office",
        label_visibility="collapsed",
    )

    render_tool_notes("cover-letters")



# -- Handle save (after sidebar renders) -------------------------------------

if save_clicked:
    _do_save(case_type)
    st.rerun()


# -- Main area ----------------------------------------------------------------

doc_col, preview_col = st.columns([3, 2], gap="large")

# -- Left column: Enclosed documents checklist --------------------------------

with doc_col:
    st.markdown('<div class="section-label">Enclosed Documents</div>', unsafe_allow_html=True)
    st.caption("Check the documents to include in this cover letter. Add descriptions for specificity.")

    standard_docs = get_standard_docs(case_type)

    # Build checked list from session state
    current_checked = list(st.session_state.get("enclosed_docs", []))
    descriptions = st.session_state.get("doc_descriptions", {})

    # Standard documents with checkboxes
    new_checked: list[str] = []
    new_descriptions: dict[str, str] = dict(descriptions)

    for doc_name in standard_docs:
        is_checked = doc_name in current_checked
        cols = st.columns([0.5, 5, 4])
        with cols[0]:
            checked = st.checkbox(
                doc_name,
                value=is_checked,
                key=f"chk_{hash(doc_name)}",
                label_visibility="collapsed",
            )
        with cols[1]:
            st.markdown(
                f'<div class="doc-item">{html_mod.escape(doc_name)}</div>',
                unsafe_allow_html=True,
            )
        with cols[2]:
            desc_val = descriptions.get(doc_name, "")
            desc = st.text_input(
                "Description",
                value=desc_val,
                key=f"desc_{hash(doc_name)}",
                label_visibility="collapsed",
                placeholder="Optional description...",
            )
            if desc:
                new_descriptions[doc_name] = desc
            elif doc_name in new_descriptions:
                new_descriptions.pop(doc_name, None)
        if checked:
            new_checked.append(doc_name)

    # Custom documents
    custom_docs = list(st.session_state.get("custom_docs", []))
    new_custom: list[str] = []
    for doc_name in custom_docs:
        cols = st.columns([0.5, 5, 3, 1])
        with cols[0]:
            st.checkbox(
                doc_name,
                value=True,
                key=f"chk_custom_{hash(doc_name)}",
                label_visibility="collapsed",
                disabled=True,
            )
        with cols[1]:
            st.markdown(
                f'<div class="doc-item">{html_mod.escape(doc_name)}</div>',
                unsafe_allow_html=True,
            )
        with cols[2]:
            desc_val = descriptions.get(doc_name, "")
            desc = st.text_input(
                "Description",
                value=desc_val,
                key=f"desc_custom_{hash(doc_name)}",
                label_visibility="collapsed",
                placeholder="Optional description...",
            )
            if desc:
                new_descriptions[doc_name] = desc
            elif doc_name in new_descriptions:
                new_descriptions.pop(doc_name, None)
        with cols[3]:
            if st.button("X", key=f"rm_{hash(doc_name)}", help="Remove custom document"):
                custom_docs.remove(doc_name)
                st.session_state.custom_docs = custom_docs
                new_descriptions.pop(doc_name, None)
                st.rerun()
        new_custom.append(doc_name)

    # Update session state
    st.session_state.enclosed_docs = new_checked
    st.session_state.custom_docs = new_custom
    st.session_state.doc_descriptions = new_descriptions

    # Add custom document
    st.markdown("---")
    add_cols = st.columns([5, 1])
    with add_cols[0]:
        new_doc_name = st.text_input(
            "Add a custom document",
            key="inp_new_doc",
            placeholder="e.g. Medical records from Dr. Smith",
            label_visibility="collapsed",
        )
    with add_cols[1]:
        if st.button("Add", use_container_width=True) and new_doc_name:
            st.session_state.custom_docs.append(new_doc_name)
            st.rerun()


# -- Right column: Live preview -----------------------------------------------

with preview_col:
    st.markdown('<div class="section-label">Cover Letter Preview</div>', unsafe_allow_html=True)
    if not client_name:
        st.info("Enter the client's name in the sidebar to see the live preview.")
    else:
        # Collect enclosed docs
        all_enclosed = _build_enclosed_docs_list()

        # Render the letter text
        letter_text = render_cover_letter(
            case_type=case_type,
            client_name=client_name,
            a_number=a_number,
            receipt_number=receipt_number,
            filing_office=filing_office,
            enclosed_docs=all_enclosed,
            attorney_name=attorney_name,
            bar_number=bar_number,
            firm_name=firm_name,
            firm_address=firm_address,
        )

        # Build and render preview HTML
        preview_html = _build_preview_html(letter_text, case_type)
        st.markdown(
            f'<div class="preview-panel">{preview_html}</div>',
            unsafe_allow_html=True,
        )

        # Export controls
        st.markdown("---")
        st.markdown('<div class="section-label">Export</div>', unsafe_allow_html=True)

        exp_cols = st.columns(2)
        with exp_cols[0]:
            st.download_button(
                "Download .txt",
                data=letter_text,
                file_name=f"Cover_Letter_{client_name.replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with exp_cols[1]:
            docx_bytes = _build_docx(letter_text, attorney_name, firm_name)
            st.download_button(
                "Download .docx",
                data=docx_bytes,
                file_name=f"Cover_Letter_{client_name.replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
            if st.button("Upload to Google Docs", use_container_width=True):
                with st.spinner("Uploading to Google Docs..."):
                    try:
                        url = upload_to_google_docs(docx_bytes, f"Cover Letter - {client_name}")
                        st.session_state.google_doc_url = url
                    except Exception as e:
                        st.error(f"Upload failed: {e}")
            if st.session_state.get("google_doc_url"):
                st.markdown(f"[Open Google Doc]({st.session_state.google_doc_url})")

    # Draft Box (always visible)
    # Draft Box (always visible — uses whatever data is on the page)
    if render_draft_box is not None:
        _draft_content = ""
        if client_name:
            _all_enc = _build_enclosed_docs_list()
            _draft_content = render_cover_letter(
                case_type=case_type, client_name=client_name,
                a_number=a_number, receipt_number=receipt_number,
                filing_office=filing_office, enclosed_docs=_all_enc,
                attorney_name=attorney_name, bar_number=bar_number,
                firm_name=firm_name, firm_address=firm_address,
            )
        render_draft_box("cover-letters", {
            "document_type": "cover letter",
            "client_name": client_name,
            "case_id": st.session_state.get("draft_id", ""),
            "content": _draft_content,
        })
