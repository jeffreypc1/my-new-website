"""Filing Assembler — Streamlit dashboard.

Production-quality UI for generating immigration filing cover pages with
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
from docx.shared import Inches, Pt

from app.drafts import delete_draft, list_drafts, load_draft, new_draft_id, save_draft
from app.templates import (
    CASE_TYPES,
    RECIPIENT_CATEGORIES,
    TEMPLATES,
    get_filing_office_address,
    get_filing_offices,
    get_recipient_addresses,
    render_cover_letter,
    render_eoir_submission,
    save_recipient_addresses,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.config_store import load_config
from shared.google_upload import copy_template_and_fill, upload_to_google_docs
from shared.client_banner import render_client_banner
from shared.tool_notes import render_tool_notes
try:
    from shared.draft_box import render_draft_box
except ImportError:
    render_draft_box = None
try:
    from shared.salesforce_client import upload_file_to_contact
except ImportError:
    upload_file_to_contact = None
try:
    from shared.salesforce_client import get_beneficiaries
except ImportError:
    get_beneficiaries = None
try:
    from shared.google_doc_creator import render_google_doc_button
except ImportError:
    render_google_doc_button = None
try:
    from shared.tool_help import render_tool_help
except ImportError:
    render_tool_help = None
try:
    from shared.feedback_button import render_feedback_button
except ImportError:
    render_feedback_button = None

# -- Page config --------------------------------------------------------------

st.set_page_config(
    page_title="Filing Assembler — O'Brien Immigration Law",
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

/* SF task row marked for deletion */
.sf-task-deleted {
    background: #fef2f2;
    border: 1px solid #fca5a5;
    border-radius: 6px;
    padding: 6px 10px;
    margin: 2px 0;
}
.sf-task-deleted .doc-item {
    text-decoration: line-through;
    color: #991b1b;
}

/* SF task row — normal */
.sf-task-row {
    padding: 4px 10px;
    margin: 2px 0;
    border-radius: 6px;
    border: 1px solid transparent;
}
.sf-task-row:hover {
    background: #f8fafc;
}

/* Pending changes badge */
.pending-badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    margin-left: 8px;
}
.pending-badge.edits {
    background: #fef3c7;
    color: #92400e;
}
.pending-badge.deletes {
    background: #fee2e2;
    color: #991b1b;
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

from shared.auth import require_auth, render_logout
require_auth()

# -- Navigation bar -----------------------------------------------------------

st.markdown(
    """
<div class="nav-bar">
    <a href="http://localhost:8502" class="nav-back">&#8592; Staff Dashboard</a>
    <div class="nav-title">Filing Assembler<span class="nav-firm">&mdash; O'Brien Immigration Law</span></div>
    <div class="nav-spacer"></div>
</div>
""",
    unsafe_allow_html=True,
)
render_logout()

render_client_banner()
if render_tool_help:
    render_tool_help("cover-letters")
if render_feedback_button:
    render_feedback_button("cover-letters")

# -- Session state defaults ---------------------------------------------------

_DEFAULTS: dict = {
    "draft_id": None,
    "last_saved_msg": "",
    "custom_docs": [],
    "sf_task_docs": [],
    "doc_descriptions": {},
    "sf_tasks_pending_delete": [],
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.draft_id is None:
    st.session_state.draft_id = new_draft_id()

# -- SF auto-fill for client fields -------------------------------------------
_sf_client = st.session_state.get("sf_client")
if _sf_client:
    _sf_cid = _sf_client.get("Id", "")
    _prev_cid = st.session_state.get("_sf_autofill_cid", "")
    if _sf_cid and _sf_cid != _prev_cid:
        # New client pulled — auto-fill fields
        _sf_name = _sf_client.get("Name", "")
        if _sf_name:
            st.session_state["inp_client_name"] = _sf_name
        _sf_anum = _sf_client.get("A_Number__c", "")
        if _sf_anum:
            st.session_state["inp_a_number"] = _sf_anum
        st.session_state["_sf_autofill_cid"] = _sf_cid


# -- Helpers ------------------------------------------------------------------

def _build_enclosed_docs_list() -> list[dict[str, str]]:
    """Collect the currently selected enclosed documents with descriptions."""
    docs: list[dict[str, str]] = []
    # SF tasks that are checked
    for doc_name in st.session_state.get("sf_task_docs", []):
        docs.append({"name": doc_name, "description": ""})
    # Custom docs
    for doc_name in st.session_state.get("custom_docs", []):
        desc = st.session_state.get("doc_descriptions", {}).get(doc_name, "")
        docs.append({"name": doc_name, "description": desc})
    return docs


def _substitute_placeholders(text: str) -> str:
    """Resolve {first_name}, {last_name}, {client_name}, {case_type}, {a_number} from session state."""
    client_name = st.session_state.get("inp_client_name", "")
    case_type = st.session_state.get("inp_case_type", "")
    a_number = st.session_state.get("inp_a_number", "")

    # Try SF client for first/last, fall back to splitting client_name
    _sf = st.session_state.get("sf_client")
    if _sf:
        first_name = _sf.get("FirstName", "")
        last_name = _sf.get("LastName", "")
    else:
        parts = client_name.rsplit(" ", 1)
        first_name = parts[0] if len(parts) > 1 else client_name
        last_name = parts[1] if len(parts) > 1 else ""

    return (
        text
        .replace("{first_name}", first_name)
        .replace("{last_name}", last_name)
        .replace("{client_name}", client_name)
        .replace("{case_type}", case_type)
        .replace("{a_number}", a_number)
    )


def _do_save(case_type: str) -> None:
    """Save the current state as a draft."""
    client = {
        "name": st.session_state.get("inp_client_name", ""),
        "a_number": st.session_state.get("inp_a_number", ""),
        "receipt_number": st.session_state.get("inp_receipt_number", ""),
    }
    # Resolve attorney from staff directory selection
    _staff_sel = st.session_state.get("inp_attorney_staff", "")
    _staff_list = load_config("staff-directory") or []
    _staff_match = next(
        (m for m in _staff_list
         if f"{m.get('first_name', '')} {m.get('last_name', '')}".strip() == _staff_sel),
        None,
    )
    _gs = load_config("global-settings") or {}
    attorney = {
        "name": _staff_sel,
        "bar_number": _staff_match.get("bar_number", "") if _staff_match else "",
        "firm_name": _gs.get("firm_name", "O'Brien Immigration Law"),
        "firm_address": _gs.get("firm_address", ""),
        "staff_id": _staff_match.get("id", "") if _staff_match else "",
    }
    filing_office = st.session_state.get("inp_filing_office", "")
    enclosed = _build_enclosed_docs_list()

    # Recipient info
    _rt = st.session_state.get("inp_recipient_type", "Government Agency")
    _rtype = "client" if _rt == "Client" else "agency"
    if _rtype == "agency":
        _all_addr = get_recipient_addresses()
        _sel_name = st.session_state.get("inp_recipient_name", "")
        _entry = next((a for a in _all_addr if a["name"] == _sel_name), None)
        _raddr = _entry["address"] if _entry else ""
        _rsal = _entry.get("salutation", "Dear Sir or Madam:") if _entry else "Dear Sir or Madam:"
    else:
        _raddr = st.session_state.get("inp_client_address", "")
        _rsal = st.session_state.get("inp_client_salutation", "Dear Sir or Madam:")

    _tmpl_sel = st.session_state.get("inp_template_selection", "Default (from Case Type)")
    _ltr_subject = st.session_state.get("inp_letter_subject", "")
    _ltr_body = st.session_state.get("inp_letter_body", "")

    # Backward-compat: also populate custom_purpose/custom_closing
    if _tmpl_sel == "Default (from Case Type)":
        _body_text = _ltr_body
        _split = _body_text.split("\n\n", 1)
        _cp = _split[0] if _split else ""
        _cc = _split[1] if len(_split) > 1 else ""
    else:
        _cp = ""
        _cc = ""

    save_draft(
        st.session_state.draft_id,
        case_type,
        client,
        attorney,
        filing_office,
        enclosed,
        recipient_type=_rtype,
        recipient_address=_raddr,
        salutation=_rsal,
        custom_purpose=_cp,
        custom_closing=_cc,
        template_selection=_tmpl_sel,
        letter_subject=_ltr_subject,
        letter_body=_ltr_body,
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
    # Restore attorney selection — try staff_id first, fall back to name match
    _staff_id = a.get("staff_id", "")
    _atty_name = a.get("name", "")
    if _staff_id or _atty_name:
        _staff_list = load_config("staff-directory") or []
        _match = None
        if _staff_id:
            _match = next((m for m in _staff_list if m.get("id") == _staff_id), None)
        if not _match and _atty_name:
            _match = next(
                (m for m in _staff_list
                 if f"{m.get('first_name', '')} {m.get('last_name', '')}".strip() == _atty_name),
                None,
            )
        if _match:
            st.session_state.inp_attorney_staff = (
                f"{_match.get('first_name', '')} {_match.get('last_name', '')}".strip()
            )
        else:
            st.session_state.inp_attorney_staff = ""
    else:
        st.session_state.inp_attorney_staff = ""

    st.session_state.inp_filing_office = draft.get("filing_office", "")

    # Restore recipient info
    _rtype = draft.get("recipient_type", "")
    _raddr = draft.get("recipient_address", "")
    _rsal = draft.get("salutation", "Dear Sir or Madam:")

    if _rtype == "client":
        st.session_state.inp_recipient_type = "Client"
        st.session_state.inp_client_address = _raddr
        st.session_state.inp_client_salutation = _rsal
    elif _rtype == "agency" and _raddr:
        st.session_state.inp_recipient_type = "Government Agency"
        # Try to find the matching address entry to set category + name
        _all_addr = get_recipient_addresses()
        _match = next((a for a in _all_addr if a["address"] == _raddr), None)
        if _match:
            st.session_state.inp_recipient_category = _match["category"]
            st.session_state.inp_recipient_name = _match["name"]
    elif not _rtype and draft.get("filing_office"):
        # Old draft: map filing_office to an address entry
        st.session_state.inp_recipient_type = "Government Agency"
        _all_addr = get_recipient_addresses()
        _match = next((a for a in _all_addr if a["name"] == draft["filing_office"]), None)
        if _match:
            st.session_state.inp_recipient_category = _match["category"]
            st.session_state.inp_recipient_name = _match["name"]

    # Restore enclosed docs
    enclosed = draft.get("enclosed_docs", [])
    custom = []
    descs: dict[str, str] = {}
    for doc in enclosed:
        name = doc.get("name", "")
        desc = doc.get("description", "")
        custom.append(name)
        if desc:
            descs[name] = desc
    st.session_state.custom_docs = custom
    st.session_state.doc_descriptions = descs

    # Restore template / letter body fields
    _loaded_case_type = draft.get("case_type", CASE_TYPES[0])
    _loaded_tmpl = draft.get("template_selection", "")

    if _loaded_tmpl:
        # New-format draft — restore directly
        # Guard: if saved template name not in current template list, fall back
        _cl_templates = load_config("client-cover-letter-templates") or []
        _cl_names = [t["name"] for t in _cl_templates]
        if _loaded_tmpl != "Default (from Case Type)" and _loaded_tmpl not in _cl_names:
            st.session_state.inp_template_selection = "Default (from Case Type)"
        else:
            st.session_state.inp_template_selection = _loaded_tmpl
        st.session_state.inp_letter_subject = draft.get("letter_subject", "")
        st.session_state.inp_letter_body = draft.get("letter_body", "")
    else:
        # Old-format draft — convert custom_purpose/custom_closing to merged body
        _loaded_purpose = draft.get("custom_purpose", "")
        _loaded_closing = draft.get("custom_closing", "")
        _tpl = TEMPLATES.get(_loaded_case_type, {})
        _purpose = _loaded_purpose or _tpl.get("purpose_paragraph", "")
        _closing = _loaded_closing or _tpl.get("closing_paragraph", "")
        _merged = (_purpose + "\n\n" + _closing).strip() if _purpose or _closing else ""
        st.session_state.inp_template_selection = "Default (from Case Type)"
        st.session_state.inp_letter_subject = ""
        st.session_state.inp_letter_body = _merged

    st.session_state["_prev_case_type"] = _loaded_case_type
    st.session_state["_prev_template_selection"] = st.session_state.get("inp_template_selection", "Default (from Case Type)")


def _do_new() -> None:
    """Start a fresh cover letter."""
    st.session_state.draft_id = new_draft_id()
    st.session_state.last_saved_msg = ""
    st.session_state.custom_docs = []
    st.session_state.sf_task_docs = []
    st.session_state.doc_descriptions = {}
    for k in (
        "inp_client_name", "inp_a_number", "inp_receipt_number",
        "inp_attorney_staff",
        "inp_filing_office", "inp_case_type",
        "inp_recipient_type", "inp_recipient_category", "inp_recipient_name",
        "inp_client_address", "inp_client_salutation",
        "inp_purpose_paragraph", "inp_closing_paragraph",
        "inp_template_selection", "inp_letter_subject", "inp_letter_body",
        "inp_export_file_name",
        "_sf_autofill_cid", "_prev_case_type", "_prev_template_selection",
        "_gdoc_result_gdoc_export_cl", "google_doc_url",
        # EOIR tab keys
        "inp_eoir_court_location", "inp_eoir_court_address",
        "inp_eoir_submission_type", "inp_eoir_dhs_address",
        "inp_eoir_service_method", "inp_eoir_legal_case_idx",
        "_eoir_beneficiaries", "_eoir_beneficiaries_case_id",
        "_eoir_autofill_case_id",
    ):
        if k in st.session_state:
            del st.session_state[k]


@st.dialog("Add New Address")
def _add_address_dialog():
    """Dialog for adding a new recipient address."""
    _new_name = st.text_input("Name", placeholder="e.g. USCIS Field Office - Boston")
    _new_category = st.selectbox("Category", options=RECIPIENT_CATEGORIES)
    _new_address = st.text_area(
        "Address",
        height=100,
        placeholder="Organization Name\nStreet Address\nCity, State ZIP",
    )
    _new_salutation = st.text_input("Salutation", value="Dear Sir or Madam:")

    if st.button("Save Address", type="primary", use_container_width=True):
        if not _new_name or not _new_address:
            st.error("Name and address are required.")
        else:
            _addresses = get_recipient_addresses()
            _new_id = _new_name.lower().replace(" ", "_").replace("(", "").replace(")", "")[:40]
            _addresses.append({
                "id": _new_id,
                "name": _new_name,
                "category": _new_category,
                "address": _new_address,
                "salutation": _new_salutation,
            })
            save_recipient_addresses(_addresses)
            st.session_state["_show_add_address"] = False
            st.rerun()


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

    for line in lines:
        escaped = esc(line)
        if line.startswith("RE: "):
            parts.append(f"<strong>{escaped}</strong>")
        elif line.startswith("    A# ") or line.startswith("    Receipt#") or (line.startswith("    ") and not line.startswith("    " + "  ")):
            parts.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{esc(line.strip())}")
        elif line == "CERTIFICATE OF SERVICE":
            parts.append(f'<div class="letter-cert"><strong>{escaped}</strong></div>')
        elif line.startswith("____"):
            parts.append(f"<br>{escaped}")
        else:
            parts.append(escaped)

    return "<br>".join(parts)


def _build_eoir_preview_html(text: str) -> str:
    """Convert EOIR submission plain text into styled HTML for the preview panel."""
    esc = html_mod.escape
    lines = text.split("\n")
    parts: list[str] = []

    # Centered headings
    _centered = {
        "UNITED STATES DEPARTMENT OF JUSTICE",
        "EXECUTIVE OFFICE FOR IMMIGRATION REVIEW",
        "IMMIGRATION COURT",
        "IN THE MATTERS OF:",
        "RESPONDENT'S SUBMISSION",
        "CERTIFICATE OF SERVICE",
    }

    for line in lines:
        stripped = line.strip()
        if stripped in _centered:
            if stripped == "CERTIFICATE OF SERVICE":
                parts.append(
                    f'<div class="letter-cert" style="text-align:center;">'
                    f"<strong>{esc(stripped)}</strong></div>"
                )
            else:
                parts.append(f'<div style="text-align:center;"><strong>{esc(stripped)}</strong></div>')
        elif line.startswith("    ") and len(line) > 4 and line.strip()[0:1].isdigit():
            # Numbered document list item
            parts.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{esc(stripped)}")
        elif line.startswith("____"):
            parts.append(f"<br>{esc(line)}")
        elif stripped.startswith("Bar No."):
            parts.append(esc(stripped))
        elif stripped.startswith("Tel:") or stripped.startswith("Fax:") or stripped.startswith("Email:"):
            parts.append(esc(stripped))
        else:
            parts.append(esc(line))

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


def _build_cover_letter_pdf(letter_text: str) -> bytes:
    """Build a PDF from the rendered cover letter text using fpdf2.

    Handles RE: lines (bold), indented lines (10mm indent),
    CERTIFICATE OF SERVICE (bold + spacing), underscores (spacing),
    and normal text (multi_cell wrapping). 1-inch margins, Times 12pt.
    """
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_margins(25.4, 25.4, 25.4)  # 1-inch margins — must precede add_page
    pdf.set_auto_page_break(auto=True, margin=25.4)
    pdf.add_page()
    pdf.set_font("Times", "", 12)

    # Explicit width avoids fpdf2 w=0 edge cases on page breaks
    _w = pdf.w - pdf.l_margin - pdf.r_margin
    _w_indent = _w - 10

    for line in letter_text.split("\n"):
        pdf.set_x(pdf.l_margin)
        if not line.strip():
            pdf.ln(6)
        elif line.startswith("RE: "):
            pdf.set_font("Times", "B", 12)
            pdf.multi_cell(_w, 6, line, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Times", "", 12)
        elif line == "CERTIFICATE OF SERVICE":
            pdf.ln(6)
            pdf.set_font("Times", "B", 12)
            pdf.multi_cell(_w, 6, line, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Times", "", 12)
            pdf.ln(3)
        elif line.startswith("____"):
            pdf.ln(6)
            pdf.multi_cell(_w, 6, line, new_x="LMARGIN", new_y="NEXT")
        elif line.startswith("    "):
            pdf.set_x(pdf.l_margin + 10)
            pdf.multi_cell(_w_indent, 6, line.strip(), new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.multi_cell(_w, 6, line, new_x="LMARGIN", new_y="NEXT")

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# -- Sidebar (drafts only) ---------------------------------------------------

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

    render_tool_notes("cover-letters")


# -- Add Address dialog trigger -----------------------------------------------
if st.session_state.get("_show_add_address"):
    _add_address_dialog()


# -- Main area ----------------------------------------------------------------

# Pre-compute attorney/firm info from session state so the preview (rendered
# inside the tab BEFORE the footer selectbox) uses the current values.
_staff_dir = load_config("staff-directory") or []
_staff_dir = [m for m in _staff_dir if m.get("visible", True)]
_gs_global = load_config("global-settings") or {}
_atty_sel_pre = st.session_state.get("inp_attorney_staff", "")
_matched_pre = next(
    (m for m in _staff_dir
     if f"{m.get('first_name', '')} {m.get('last_name', '')}".strip() == _atty_sel_pre),
    None,
)
attorney_name = _atty_sel_pre
bar_number = _matched_pre.get("bar_number", "") if _matched_pre else ""
firm_name = _gs_global.get("firm_name", "O'Brien Immigration Law")
firm_address = _gs_global.get("firm_address", "")

letter_text = ""

tab_cover, tab_eoir = st.tabs(["Cover Letter", "EOIR Submission"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: Cover Letter
# ═══════════════════════════════════════════════════════════════════════════════
with tab_cover:
    _cl_left, _cl_right = st.columns([3, 2], gap="large")

    with _cl_left:

        # ── Step 1: Case Type ────────────────────────────────────────────────
        st.markdown('<div class="section-label">Case Type</div>', unsafe_allow_html=True)
        case_type = st.selectbox(
            "Case Type",
            options=CASE_TYPES,
            key="inp_case_type",
            label_visibility="collapsed",
        )

        st.divider()

        # ── Step 2: Recipient ────────────────────────────────────────────────
        st.markdown('<div class="section-label">Recipient</div>', unsafe_allow_html=True)
        recipient_type = st.radio(
            "Recipient type",
            options=["Government Agency", "Client"],
            key="inp_recipient_type",
            horizontal=True,
            label_visibility="collapsed",
        )

        if recipient_type == "Government Agency":
            _all_addresses = get_recipient_addresses()

            _selected_category = st.selectbox(
                "Category",
                options=RECIPIENT_CATEGORIES,
                key="inp_recipient_category",
            )

            _filtered = [a for a in _all_addresses if a.get("category") == _selected_category]
            _addr_names = [a["name"] for a in _filtered]

            if _addr_names:
                _selected_name = st.selectbox(
                    "Address",
                    options=_addr_names,
                    key="inp_recipient_name",
                )
                _selected_entry = next((a for a in _filtered if a["name"] == _selected_name), None)
                if _selected_entry:
                    st.caption(_selected_entry["address"].replace("\n", "  \n"))
                    recipient_address = _selected_entry["address"]
                    salutation = _selected_entry.get("salutation", "Dear Sir or Madam:")
                else:
                    recipient_address = ""
                    salutation = "Dear Sir or Madam:"
            else:
                st.caption("No addresses in this category.")
                recipient_address = ""
                salutation = "Dear Sir or Madam:"

            if st.button("+ Add New Address", use_container_width=True):
                st.session_state["_show_add_address"] = True

            # Legacy fallback for filing_office (used by render_cover_letter if recipient_address empty)
            filing_office = ""

        else:
            # Client recipient
            _sf_client = st.session_state.get("sf_client")
            _default_addr = ""
            _default_sal = "Dear Sir or Madam:"
            if _sf_client:
                _parts = []
                _first = _sf_client.get("FirstName", "")
                _last = _sf_client.get("LastName", "")
                _full_name = f"{_first} {_last}".strip()
                if _full_name:
                    _parts.append(_full_name)
                _street = _sf_client.get("MailingStreet", "")
                if _street:
                    _parts.append(_street)
                _city = _sf_client.get("MailingCity", "")
                _state = _sf_client.get("MailingState", "")
                _zip = _sf_client.get("MailingPostalCode", "")
                _csz = ", ".join(filter(None, [_city, _state]))
                if _zip:
                    _csz = f"{_csz} {_zip}" if _csz else _zip
                if _csz:
                    _parts.append(_csz)
                _default_addr = "\n".join(_parts)
                if _first or _last:
                    _default_sal = f"Dear {_full_name}:"

            recipient_address = st.text_area(
                "Recipient Address",
                value=st.session_state.get("inp_client_address", _default_addr),
                key="inp_client_address",
                height=100,
                placeholder="Client name\nStreet address\nCity, State ZIP",
            )
            salutation = st.text_input(
                "Salutation",
                value=st.session_state.get("inp_client_salutation", _default_sal),
                key="inp_client_salutation",
            )
            filing_office = ""

        st.divider()

        # ── Step 3: Client / RE Block ────────────────────────────────────────
        st.markdown('<div class="section-label">Client</div>', unsafe_allow_html=True)
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

        # ── Step 4: Letter Body ──────────────────────────────────────────────
        st.markdown('<div class="section-label">Letter Body</div>', unsafe_allow_html=True)

        # Load client cover letter templates
        _cl_templates = load_config("client-cover-letter-templates") or []
        _cl_template_names = [t["name"] for t in _cl_templates]
        _template_options = ["Default (from Case Type)"] + _cl_template_names

        template_selection = st.selectbox(
            "Template",
            options=_template_options,
            key="inp_template_selection",
        )

        # ── Change detection for template + case type ──
        _prev_tmpl = st.session_state.get("_prev_template_selection")
        _prev_ct = st.session_state.get("_prev_case_type")
        _is_default = template_selection == "Default (from Case Type)"

        if _prev_tmpl is not None and _prev_tmpl != template_selection:
            # Template selection changed
            if _is_default:
                # Switched back to Default — populate from case type
                _ct_tpl = TEMPLATES.get(case_type, {})
                _purpose = _ct_tpl.get("purpose_paragraph", "")
                _closing = _ct_tpl.get("closing_paragraph", "")
                _merged = (_purpose + "\n\n" + _closing).strip()
                st.session_state["inp_letter_body"] = _merged
                st.session_state["inp_letter_subject"] = ""
            else:
                # Switched to a named template — populate from it
                _sel_tpl = next((t for t in _cl_templates if t["name"] == template_selection), None)
                if _sel_tpl:
                    st.session_state["inp_letter_subject"] = _sel_tpl.get("subject", "")
                    st.session_state["inp_letter_body"] = _sel_tpl.get("body", "")
        elif _is_default and _prev_ct is not None and _prev_ct != case_type:
            # Case type changed while in Default mode — repopulate body
            _ct_tpl = TEMPLATES.get(case_type, {})
            _purpose = _ct_tpl.get("purpose_paragraph", "")
            _closing = _ct_tpl.get("closing_paragraph", "")
            _merged = (_purpose + "\n\n" + _closing).strip()
            st.session_state["inp_letter_body"] = _merged
        elif _prev_tmpl is None:
            # First load — only set if not already in session state
            if "inp_letter_body" not in st.session_state:
                _ct_tpl = TEMPLATES.get(case_type, {})
                _purpose = _ct_tpl.get("purpose_paragraph", "")
                _closing = _ct_tpl.get("closing_paragraph", "")
                _merged = (_purpose + "\n\n" + _closing).strip()
                st.session_state["inp_letter_body"] = _merged

        st.session_state["_prev_template_selection"] = template_selection
        st.session_state["_prev_case_type"] = case_type

        # Subject field — only visible for non-Default templates
        if not _is_default:
            letter_subject = st.text_input(
                "Subject",
                key="inp_letter_subject",
                placeholder="e.g. Documents Needed for Your Case",
            )
        else:
            letter_subject = ""

        # Body field
        letter_body = st.text_area(
            "Body",
            key="inp_letter_body",
            height=250,
            help="Use {client_name}, {first_name}, {last_name}, {case_type}, {a_number} as placeholders.",
        )

        st.divider()

        # ── Step 5: Enclosed Documents ───────────────────────────────────────
        st.markdown('<div class="section-label">Enclosed Documents</div>', unsafe_allow_html=True)
        st.caption("Check the documents to include in this cover letter. Add descriptions for specificity.")

        # -- Salesforce Tasks (LC_Task__c) ------------------------------------
        _active_client = st.session_state.get("sf_client")
        _sf_contact_id = _active_client.get("Id", "") if _active_client else ""
        _sf_tasks: list[dict] = []

        if _sf_contact_id:
            try:
                from shared.salesforce_client import get_lc_tasks
                _sf_tasks = get_lc_tasks(_sf_contact_id)
            except Exception:
                _sf_tasks = []

        if _sf_tasks or _sf_contact_id:
            st.markdown('<div class="section-label" style="margin-top:4px;">Salesforce Tasks</div>', unsafe_allow_html=True)

        _pending_deletes: list[str] = list(st.session_state.get("sf_tasks_pending_delete", []))

        if _sf_tasks:
            _current_sf_checked = list(st.session_state.get("sf_task_docs", []))
            _new_sf_checked: list[str] = []
            _has_edits = False

            for _task in _sf_tasks:
                _task_id = _task.get("Id", "")
                _task_label = _task.get("For__c") or _task.get("Name") or "Untitled task"
                _is_pending_delete = _task_id in _pending_deletes
                _edit_key = f"_sf_task_edit_{_task_id}"

                if _is_pending_delete:
                    st.markdown(
                        f'<div class="sf-task-deleted">'
                        f'<div class="doc-item">{html_mod.escape(_task_label)}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    _undo_cols = st.columns([8, 1])
                    with _undo_cols[1]:
                        if st.button("Undo", key=f"_btn_undo_sft_{_task_id}", use_container_width=True):
                            _pending_deletes.remove(_task_id)
                            st.session_state.sf_tasks_pending_delete = _pending_deletes
                            st.rerun()
                else:
                    _edited_label = st.session_state.get(_edit_key, _task_label)
                    _was_checked = _edited_label in _current_sf_checked or _task_label in _current_sf_checked
                    _tc = st.columns([0.5, 8, 0.5])
                    with _tc[0]:
                        _tc_checked = st.checkbox(
                            _task_label,
                            value=_was_checked,
                            key=f"chk_sft_{_task_id}",
                            label_visibility="collapsed",
                        )
                    with _tc[1]:
                        _edited_val = st.text_input(
                            "Edit document name",
                            value=_edited_label,
                            key=_edit_key,
                            label_visibility="collapsed",
                        )
                    with _tc[2]:
                        if st.button("X", key=f"_btn_del_sft_{_task_id}", help="Mark for deletion"):
                            _pending_deletes.append(_task_id)
                            st.session_state.sf_tasks_pending_delete = _pending_deletes
                            st.rerun()

                    if _edited_val.strip() != _task_label:
                        _has_edits = True
                    if _tc_checked and _edited_val.strip():
                        _new_sf_checked.append(_edited_val.strip())

            st.session_state.sf_task_docs = _new_sf_checked

            # ── Save Changes button ──
            _has_changes = _has_edits or len(_pending_deletes) > 0
            if _has_changes:
                _badge_parts: list[str] = []
                _edit_count = sum(
                    1 for _t in _sf_tasks
                    if _t.get("Id", "") not in _pending_deletes
                    and st.session_state.get(f"_sf_task_edit_{_t.get('Id', '')}", "").strip()
                       != (_t.get("For__c") or _t.get("Name") or "Untitled task")
                    and st.session_state.get(f"_sf_task_edit_{_t.get('Id', '')}", "") != ""
                )
                if _edit_count:
                    _badge_parts.append(f'<span class="pending-badge edits">{_edit_count} edit{"s" if _edit_count != 1 else ""}</span>')
                if _pending_deletes:
                    _del_count = len(_pending_deletes)
                    _badge_parts.append(f'<span class="pending-badge deletes">{_del_count} deletion{"s" if _del_count != 1 else ""}</span>')
                st.markdown(f'{"".join(_badge_parts)}', unsafe_allow_html=True)

                if st.button("Save Changes to Salesforce", type="primary", use_container_width=True, key="_btn_save_all_sf"):
                    _save_errors: list[str] = []
                    try:
                        from shared.salesforce_client import update_lc_task, delete_lc_task

                        for _t in _sf_tasks:
                            _tid = _t.get("Id", "")
                            if _tid in _pending_deletes:
                                continue
                            _orig = _t.get("For__c") or _t.get("Name") or "Untitled task"
                            _new_val = st.session_state.get(f"_sf_task_edit_{_tid}", "").strip()
                            if _new_val and _new_val != _orig:
                                try:
                                    update_lc_task(_tid, _new_val)
                                except Exception as e:
                                    _save_errors.append(f"Edit '{_new_val}': {e}")

                        for _tid in _pending_deletes:
                            try:
                                delete_lc_task(_tid)
                            except Exception as e:
                                _save_errors.append(f"Delete {_tid}: {e}")

                        st.session_state.sf_tasks_pending_delete = []
                        for _t in _sf_tasks:
                            _ek = f"_sf_task_edit_{_t.get('Id', '')}"
                            if _ek in st.session_state:
                                del st.session_state[_ek]

                        if _save_errors:
                            st.warning(f"Saved with {len(_save_errors)} error(s): {'; '.join(_save_errors)}")
                        else:
                            st.success("Changes saved to Salesforce.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Save failed: {e}")

        elif _sf_contact_id:
            st.caption("No tasks found for this client.")

        from shared.document_adder import render_document_adder
        render_document_adder("cover-letters")

        descriptions = st.session_state.get("doc_descriptions", {})
        new_descriptions: dict[str, str] = dict(descriptions)

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

        st.session_state.custom_docs = new_custom
        st.session_state.doc_descriptions = new_descriptions

    # ── Cover Letter Preview (right column) ──────────────────────────────────
    with _cl_right:
        st.markdown('<div class="section-label">Cover Letter Preview</div>', unsafe_allow_html=True)
        if not client_name:
            st.info("Enter the client's name to see the live preview.")
        else:
            all_enclosed = _build_enclosed_docs_list()

            _is_default_mode = template_selection == "Default (from Case Type)"

            if _is_default_mode:
                # Default: split body on first \n\n → purpose / closing
                _body_text = letter_body or ""
                _split = _body_text.split("\n\n", 1)
                _raw_purpose = _split[0] if _split else ""
                _raw_closing = _split[1] if len(_split) > 1 else ""

                _purpose_rendered = _substitute_placeholders(_raw_purpose)
                _purpose_safe = _purpose_rendered.replace("{", "{{").replace("}", "}}") if _purpose_rendered else ""
                _closing_rendered = _substitute_placeholders(_raw_closing)
                _closing_safe = _closing_rendered.replace("{", "{{").replace("}", "}}") if _closing_rendered else ""

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
                    custom_purpose=_purpose_safe,
                    custom_closing=_closing_safe,
                    recipient_address=recipient_address,
                    salutation=salutation,
                )
            else:
                # Template mode: subject + body → enclosed docs → signature
                _subj_rendered = _substitute_placeholders(letter_subject or "")
                _body_rendered = _substitute_placeholders(letter_body or "")
                # Escape remaining braces
                _body_safe = _body_rendered.replace("{", "{{").replace("}", "}}") if _body_rendered else ""

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
                    recipient_address=recipient_address,
                    salutation=salutation,
                    custom_subject=_subj_rendered,
                    custom_body=_body_safe,
                )

            preview_html = _build_preview_html(letter_text, case_type)
            st.markdown(
                f'<div class="preview-panel">{preview_html}</div>',
                unsafe_allow_html=True,
            )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: EOIR Submission
# ═══════════════════════════════════════════════════════════════════════════════
with tab_eoir:
    _eoir_left, _eoir_right = st.columns([3, 2], gap="large")

    # Resolve legal cases from active client
    _eoir_sf_client = st.session_state.get("sf_client")
    _eoir_legal_cases: list[dict] = []
    if _eoir_sf_client:
        _eoir_legal_cases = _eoir_sf_client.get("legal_cases", [])

    with _eoir_left:
        if not _eoir_sf_client:
            st.info("Pull a client to use the EOIR Submission tab.")
        elif not _eoir_legal_cases:
            st.warning("No legal cases found for this client.")
        else:
            # ── Legal Case Selector ──────────────────────────────────────
            st.markdown('<div class="section-label">Legal Case</div>', unsafe_allow_html=True)
            _lc_labels = []
            for _lc in _eoir_legal_cases:
                _lc_name = _lc.get("Name", "")
                _lc_type = _lc.get("Legal_Case_Type__c", "")
                _lc_labels.append(f"{_lc_name} — {_lc_type}" if _lc_type else _lc_name)

            # Default to the selected_legal_case from Client Info if available
            _preselected_lc = _eoir_sf_client.get("selected_legal_case")
            _default_lc_idx = 0
            if _preselected_lc:
                for _i, _lc in enumerate(_eoir_legal_cases):
                    if _lc.get("Id") == _preselected_lc.get("Id"):
                        _default_lc_idx = _i
                        break

            _eoir_lc_idx = st.selectbox(
                "Select Legal Case",
                options=range(len(_eoir_legal_cases)),
                index=st.session_state.get("inp_eoir_legal_case_idx", _default_lc_idx),
                format_func=lambda i: _lc_labels[i],
                key="inp_eoir_legal_case_idx",
                label_visibility="collapsed",
            )
            _eoir_case = _eoir_legal_cases[_eoir_lc_idx]
            _eoir_case_id = _eoir_case.get("Id", "")

            # ── Auto-fill from case fields on case change ────────────────
            _prev_autofill = st.session_state.get("_eoir_autofill_case_id", "")
            if _eoir_case_id and _eoir_case_id != _prev_autofill:
                st.session_state["inp_eoir_court_location"] = _eoir_case.get("Location_City__c", "") or ""
                st.session_state["inp_eoir_court_address"] = _eoir_case.get("Address_of_next_hearing__c", "") or ""
                st.session_state["inp_eoir_dhs_address"] = _eoir_case.get("DHS_Address__c", "") or ""
                st.session_state["_eoir_autofill_case_id"] = _eoir_case_id

            # ── Fetch beneficiaries (cached per case) ────────────────────
            _cached_ben_case = st.session_state.get("_eoir_beneficiaries_case_id", "")
            if _eoir_case_id != _cached_ben_case:
                if get_beneficiaries and _eoir_case_id:
                    try:
                        st.session_state["_eoir_beneficiaries"] = get_beneficiaries(_eoir_case_id)
                    except Exception:
                        st.session_state["_eoir_beneficiaries"] = []
                else:
                    st.session_state["_eoir_beneficiaries"] = []
                st.session_state["_eoir_beneficiaries_case_id"] = _eoir_case_id
            _eoir_beneficiaries: list[dict] = st.session_state.get("_eoir_beneficiaries", [])

            st.divider()

            # ── Court Information ────────────────────────────────────────
            st.markdown('<div class="section-label">Court Information</div>', unsafe_allow_html=True)
            _eoir_court_loc = st.text_input(
                "Court Location",
                key="inp_eoir_court_location",
                placeholder="e.g. SAN FRANCISCO CA",
            )
            _eoir_court_addr = st.text_area(
                "Court Address",
                key="inp_eoir_court_address",
                height=80,
                placeholder="Full court street address",
            )

            st.divider()

            # ── Parties ──────────────────────────────────────────────────
            st.markdown('<div class="section-label">Parties</div>', unsafe_allow_html=True)
            _eoir_applicant_name = _eoir_case.get("Primary_Applicant__r_Name", "") or _eoir_sf_client.get("Name", "")
            _eoir_a_number = _eoir_case.get("A_number_dashed__c", "") or _eoir_sf_client.get("A_Number__c", "")
            _eoir_case_type = _eoir_case.get("Legal_Case_Type__c", "")

            st.markdown(f"**Primary Applicant:** {_eoir_applicant_name}")
            if _eoir_a_number:
                st.markdown(f"**A#:** {_eoir_a_number}")
            if _eoir_case_type:
                st.markdown(f"**Case Type:** {_eoir_case_type}")

            if _eoir_beneficiaries:
                st.markdown("**Beneficiaries / Derivatives:**")
                for _ben in _eoir_beneficiaries:
                    _ben_line = _ben.get("Name", "")
                    if _ben.get("A_Number"):
                        _ben_line += f" — A# {_ben['A_Number']}"
                    if _ben.get("Type"):
                        _ben_line += f" ({_ben['Type']})"
                    st.caption(_ben_line)

            st.divider()

            # ── Submission Details ───────────────────────────────────────
            st.markdown('<div class="section-label">Submission Details</div>', unsafe_allow_html=True)
            _eoir_submission_type = st.text_area(
                "Submission Description",
                key="inp_eoir_submission_type",
                height=80,
                placeholder="e.g. Respondent's Pre-Hearing Brief and Supporting Evidence",
            )

            # Show enclosed documents summary (shared with Cover Letter tab)
            _eoir_enclosed = _build_enclosed_docs_list()
            if _eoir_enclosed:
                st.markdown(f"**Enclosed Documents** ({len(_eoir_enclosed)}):")
                for _idx, _doc in enumerate(_eoir_enclosed, start=1):
                    _doc_label = _doc.get("name", "")
                    _doc_desc = _doc.get("description", "")
                    if _doc_desc:
                        st.caption(f"{_idx}. {_doc_label} — {_doc_desc}")
                    else:
                        st.caption(f"{_idx}. {_doc_label}")
            else:
                st.caption("No enclosed documents. Add documents in the Cover Letter tab.")

            st.divider()

            # ── Certificate of Service ───────────────────────────────────
            st.markdown('<div class="section-label">Certificate of Service</div>', unsafe_allow_html=True)
            _eoir_dhs_addr = st.text_area(
                "DHS / OCC Address",
                key="inp_eoir_dhs_address",
                height=80,
                placeholder="Office of the Chief Counsel address",
            )
            _eoir_service_method = st.selectbox(
                "Service Method",
                options=["first-class mail", "hand delivery", "electronic filing (ECAS)"],
                key="inp_eoir_service_method",
            )

            # ── Render EOIR text ─────────────────────────────────────────
            if _eoir_submission_type.strip():
                letter_text = render_eoir_submission(
                    attorney_name=attorney_name,
                    bar_number=bar_number,
                    firm_name=firm_name,
                    firm_address=firm_address,
                    firm_phone=_gs_global.get("firm_phone", ""),
                    firm_fax=_gs_global.get("firm_fax", ""),
                    firm_email=_gs_global.get("firm_email", ""),
                    court_location=_eoir_court_loc,
                    court_address=_eoir_court_addr,
                    applicant_name=_eoir_applicant_name,
                    a_number=_eoir_a_number,
                    case_type=_eoir_case_type,
                    beneficiaries=_eoir_beneficiaries,
                    submission_type=_eoir_submission_type.strip(),
                    document_list=_eoir_enclosed,
                    dhs_address=_eoir_dhs_addr,
                    service_method=_eoir_service_method,
                )

    # ── EOIR Preview (right column) ──────────────────────────────────────
    with _eoir_right:
        st.markdown('<div class="section-label">EOIR Submission Preview</div>', unsafe_allow_html=True)
        if letter_text and "EXECUTIVE OFFICE FOR IMMIGRATION REVIEW" in letter_text:
            _eoir_preview_html = _build_eoir_preview_html(letter_text)
            st.markdown(
                f'<div class="preview-panel">{_eoir_preview_html}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="preview-panel" style="min-height:200px;display:flex;align-items:center;'
                'justify-content:center;color:#94a3b8;font-style:italic;">'
                'Fill in the submission description to see a preview.'
                '</div>',
                unsafe_allow_html=True,
            )

# ═══════════════════════════════════════════════════════════════════════════════
# PERSISTENT FOOTER — Attorney / Signature + Export
# ═══════════════════════════════════════════════════════════════════════════════
st.divider()
_footer_left, _footer_right = st.columns([3, 2], gap="large")

with _footer_left:
    # ── Attorney / Signature Block ───────────────────────────────────────────
    st.markdown('<div class="section-label">Attorney / Signature</div>', unsafe_allow_html=True)
    _staff_names = [
        f"{m.get('first_name', '')} {m.get('last_name', '')}".strip()
        for m in _staff_dir
    ]
    _staff_options = [""] + _staff_names
    _cur_sel = st.session_state.get("inp_attorney_staff", "")
    _sel_idx = _staff_options.index(_cur_sel) if _cur_sel in _staff_options else 0
    _selected_staff = st.selectbox(
        "Attorney",
        options=_staff_options,
        index=_sel_idx,
        format_func=lambda x: x if x else "Select attorney...",
        key="inp_attorney_staff",
    )
    # Update attorney_name and bar_number to match widget value
    _matched = next(
        (m for m in _staff_dir
         if f"{m.get('first_name', '')} {m.get('last_name', '')}".strip() == _selected_staff),
        None,
    )
    attorney_name = _selected_staff
    bar_number = _matched.get("bar_number", "") if _matched else ""
    if bar_number:
        st.caption(f"Bar #: {bar_number}")
    firm_name = _gs_global.get("firm_name", "O'Brien Immigration Law")
    firm_address = _gs_global.get("firm_address", "")
    st.caption(f"{firm_name}")
    if firm_address:
        st.caption(firm_address.replace("\n", "  \n"))

with _footer_right:
    if letter_text:
        st.markdown("---")
        st.markdown('<div class="section-label">Export</div>', unsafe_allow_html=True)

        # File name input — smart default, no explicit value (Streamlit pitfall)
        _is_eoir_content = "EXECUTIVE OFFICE FOR IMMIGRATION REVIEW" in letter_text
        _doc_type_label = "EOIR Submission" if _is_eoir_content else "Cover Letter"
        _eoir_applicant = st.session_state.get("inp_eoir_court_location", "")
        _file_name_client = client_name
        # For EOIR, use the applicant name from the case if available
        if _is_eoir_content and _eoir_sf_client:
            _eoir_case_for_name = _eoir_legal_cases[st.session_state.get("inp_eoir_legal_case_idx", 0)] if _eoir_legal_cases else {}
            _eoir_app_name = _eoir_case_for_name.get("Primary_Applicant__r_Name", "") or _eoir_sf_client.get("Name", "")
            if _eoir_app_name:
                _file_name_client = _eoir_app_name
        _default_file_name = f"{date.today().isoformat()} - {_file_name_client} - {_doc_type_label}"
        if "inp_export_file_name" not in st.session_state:
            st.session_state["inp_export_file_name"] = ""
        _export_input = st.text_input(
            "File name",
            key="inp_export_file_name",
            placeholder=_default_file_name,
            label_visibility="collapsed",
        )
        export_file_name = _export_input.strip() if _export_input.strip() else _default_file_name

        # Three-column download row
        exp_cols = st.columns(3)
        with exp_cols[0]:
            st.download_button(
                "Download .txt",
                data=letter_text,
                file_name=f"{export_file_name}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with exp_cols[1]:
            docx_bytes = _build_docx(letter_text, attorney_name, firm_name)
            st.download_button(
                "Download .docx",
                data=docx_bytes,
                file_name=f"{export_file_name}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        with exp_cols[2]:
            pdf_bytes = _build_cover_letter_pdf(letter_text)
            st.download_button(
                "Download .pdf",
                data=pdf_bytes,
                file_name=f"{export_file_name}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        # Export to Google Doc
        # Pick template based on context (Cover Letter vs EOIR)
        _gd_folder = _gs_global.get("google_drive_folder_id", "")
        if _is_eoir_content:
            _gd_template = _gs_global.get("eoir_template_id", "") or _gs_global.get("cover_letter_template_id", "")
        else:
            _gd_template = _gs_global.get("cover_letter_template_id", "")
        _sf_contact_id_export = (_sf_client.get("Id", "") if _sf_client else "")

        if _sf_contact_id_export and _gd_template and render_google_doc_button:
            # Full export: Google Doc + Salesforce Google_Doc__c record
            _selected_lc = _sf_client.get("selected_legal_case") if _sf_client else None
            _sf_legal_case_id = _selected_lc.get("Id") if _selected_lc else (
                _sf_client.get("Legal_Case__c") if _sf_client else None
            )
            render_google_doc_button(
                template_id=_gd_template,
                file_name=export_file_name,
                contact_id=_sf_contact_id_export,
                legal_case_id=_sf_legal_case_id,
                replacements={"{{CONTENT}}": letter_text},
                folder_id=_gd_folder,
                key="gdoc_export_cl",
            )
        else:
            # Fallback: Google Doc only (no Salesforce logging)
            if st.button("Upload to Google Docs", use_container_width=True):
                with st.spinner("Uploading to Google Docs..."):
                    try:
                        if _gd_template:
                            url = copy_template_and_fill(
                                template_id=_gd_template,
                                title=export_file_name,
                                replacements={"{{CONTENT}}": letter_text},
                                folder_id=_gd_folder,
                            )
                        else:
                            url = upload_to_google_docs(
                                docx_bytes, export_file_name, folder_id=_gd_folder
                            )
                        st.session_state.google_doc_url = url
                    except Exception as e:
                        st.error(f"Upload failed: {e}")
            if st.session_state.get("google_doc_url"):
                st.markdown(f"[Open Google Doc]({st.session_state.google_doc_url})")

        # Save to Salesforce (DOCX file upload to Contact Files)
        if _sf_contact_id_export and upload_file_to_contact:
            if st.button("Save to Salesforce", use_container_width=True):
                with st.spinner("Saving to Salesforce..."):
                    try:
                        upload_file_to_contact(
                            contact_sf_id=_sf_contact_id_export,
                            file_bytes=docx_bytes,
                            file_name=export_file_name,
                            file_extension="docx",
                            title=export_file_name,
                        )
                        st.success("Saved to Salesforce.")
                    except Exception as e:
                        st.error(f"Salesforce upload failed: {e}")

        if not _sf_contact_id_export:
            st.caption("Pull a client to enable Salesforce features.")


# -- Handle save (after all widgets render) -----------------------------------

if save_clicked:
    _do_save(case_type)
    st.rerun()

# -- Draft Box (below everything) --------------------------------------------
if render_draft_box is not None:
    _all_enc = _build_enclosed_docs_list()
    _draft_content = ""
    if client_name:
        _db_tmpl_sel = st.session_state.get("inp_template_selection", "Default (from Case Type)")
        _db_is_default = _db_tmpl_sel == "Default (from Case Type)"
        _db_body = st.session_state.get("inp_letter_body", "")
        _db_subject = st.session_state.get("inp_letter_subject", "")

        if _db_is_default:
            _db_split = _db_body.split("\n\n", 1)
            _db_purpose = _substitute_placeholders(_db_split[0] if _db_split else "")
            _db_closing = _substitute_placeholders(_db_split[1] if len(_db_split) > 1 else "")
            _db_purpose_safe = _db_purpose.replace("{", "{{").replace("}", "}}") if _db_purpose else ""
            _db_closing_safe = _db_closing.replace("{", "{{").replace("}", "}}") if _db_closing else ""
            _draft_content = render_cover_letter(
                case_type=case_type, client_name=client_name,
                a_number=a_number, receipt_number=receipt_number,
                filing_office=filing_office, enclosed_docs=_all_enc,
                attorney_name=attorney_name, bar_number=bar_number,
                firm_name=firm_name, firm_address=firm_address,
                custom_purpose=_db_purpose_safe,
                custom_closing=_db_closing_safe,
                recipient_address=recipient_address, salutation=salutation,
            )
        else:
            _db_subj_rendered = _substitute_placeholders(_db_subject)
            _db_body_rendered = _substitute_placeholders(_db_body)
            _db_body_safe = _db_body_rendered.replace("{", "{{").replace("}", "}}") if _db_body_rendered else ""
            _draft_content = render_cover_letter(
                case_type=case_type, client_name=client_name,
                a_number=a_number, receipt_number=receipt_number,
                filing_office=filing_office, enclosed_docs=_all_enc,
                attorney_name=attorney_name, bar_number=bar_number,
                firm_name=firm_name, firm_address=firm_address,
                recipient_address=recipient_address, salutation=salutation,
                custom_subject=_db_subj_rendered,
                custom_body=_db_body_safe,
            )
    render_draft_box("cover-letters", {
        "document_type": "cover letter",
        "client_name": client_name,
        "case_id": st.session_state.get("draft_id", ""),
        "content": _draft_content,
        "enclosed_docs": [doc["name"] for doc in _all_enc],
        "recipient_type": recipient_type,
        "recipient_address": recipient_address,
    })
