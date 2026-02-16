"""Brief Builder -- Streamlit dashboard.

Production-quality UI for drafting immigration law briefs with section-based
editing, legal boilerplate insertion, live preview, draft persistence, and
Word/text export. Works entirely offline without the API server.

Part of the O'Brien Immigration Law tool suite.
"""

from __future__ import annotations

import html as html_mod
import io
from datetime import date

import streamlit as st
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from app.drafts import delete_draft, list_drafts, load_draft, new_draft_id, save_draft
from app.sections import BRIEF_TYPES, load_sections

# -- Page config --------------------------------------------------------------

st.set_page_config(
    page_title="Brief Builder -- O'Brien Immigration Law",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -- CSS ----------------------------------------------------------------------

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Hide Streamlit chrome */
#MainMenu, header[data-testid="stHeader"], footer,
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

/* Boilerplate block */
.boilerplate-block {
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 0.84rem;
    line-height: 1.55;
    margin-bottom: 8px;
    color: #78630d;
}

/* Preview panel (legal brief style) */
.preview-panel {
    font-family: 'Times New Roman', Times, serif;
    font-size: 0.88rem;
    line-height: 1.8;
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 28px 32px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    max-height: 75vh;
    overflow-y: auto;
}
.preview-panel .brief-title {
    text-align: center;
    font-weight: bold;
    font-size: 1.05rem;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.preview-panel .brief-caption {
    text-align: center;
    font-size: 0.85rem;
    margin-bottom: 16px;
    line-height: 1.5;
}
.preview-panel .brief-heading {
    font-weight: bold;
    margin-top: 16px;
    margin-bottom: 4px;
}
.preview-panel .brief-subheading {
    font-weight: bold;
    font-style: italic;
    margin-top: 10px;
    margin-bottom: 4px;
    padding-left: 16px;
}
.preview-panel .brief-body {
    text-align: justify;
    margin-bottom: 8px;
    text-indent: 32px;
}
.preview-panel .brief-sig {
    margin-top: 28px;
    line-height: 2;
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
</style>
""",
    unsafe_allow_html=True,
)

# -- Navigation bar -----------------------------------------------------------

st.markdown(
    """
<div class="nav-bar">
    <a href="http://localhost:8502" class="nav-back">&#8592; Staff Dashboard</a>
    <div class="nav-title">Brief Builder<span class="nav-firm">&mdash; O'Brien Immigration Law</span></div>
    <div class="nav-spacer"></div>
</div>
""",
    unsafe_allow_html=True,
)

# -- Session state defaults ---------------------------------------------------

_DEFAULTS: dict = {
    "draft_id": None,
    "last_saved_msg": "",
    "prev_brief_type": None,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.draft_id is None:
    st.session_state.draft_id = new_draft_id()

# Roman numeral helper
_ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
           "XI", "XII", "XIII", "XIV", "XV"]


# -- Helpers ------------------------------------------------------------------

def _content_key(section_key: str, sub_key: str | None = None) -> str:
    """Build a session-state key for a content text_area."""
    if sub_key:
        return f"content_{section_key}_{sub_key}"
    return f"content_{section_key}"


def _collect_section_content(brief_type: str) -> dict[str, str]:
    """Gather all section text_area values from session state."""
    sections = load_sections(brief_type)
    content: dict[str, str] = {}
    for section in sections:
        subs = section.get("subsections", [])
        if subs:
            for sub in subs:
                ck = _content_key(section["key"], sub["key"])
                content[ck] = st.session_state.get(ck, "")
        else:
            ck = _content_key(section["key"])
            content[ck] = st.session_state.get(ck, "")
    return content


def _clear_all_content_keys() -> None:
    """Remove all content_* keys from session state."""
    to_delete = [k for k in st.session_state if k.startswith("content_")]
    for k in to_delete:
        del st.session_state[k]


def _do_save(brief_type: str) -> None:
    """Save the current state as a draft."""
    case_info = {
        "client_name": st.session_state.get("inp_client_name", ""),
        "a_number": st.session_state.get("inp_a_number", ""),
        "court_or_office": st.session_state.get("inp_court_or_office", ""),
        "ij_name": st.session_state.get("inp_ij_name", ""),
        "hearing_date": st.session_state.get("inp_hearing_date", ""),
    }
    section_content = _collect_section_content(brief_type)
    save_draft(st.session_state.draft_id, brief_type, case_info, section_content)
    name = case_info["client_name"] or "draft"
    st.session_state.last_saved_msg = f"Saved -- {name}"


def _do_load(draft_id: str) -> None:
    """Load a draft into session state."""
    draft = load_draft(draft_id)
    if not draft:
        return
    _clear_all_content_keys()
    st.session_state.draft_id = draft["id"]
    st.session_state.inp_brief_type = draft.get("brief_type", list(BRIEF_TYPES.keys())[0])
    ci = draft.get("case_info", {})
    st.session_state.inp_client_name = ci.get("client_name", "")
    st.session_state.inp_a_number = ci.get("a_number", "")
    st.session_state.inp_court_or_office = ci.get("court_or_office", "")
    st.session_state.inp_ij_name = ci.get("ij_name", "")
    st.session_state.inp_hearing_date = ci.get("hearing_date", "")
    st.session_state.prev_brief_type = draft.get("brief_type", "")
    for ck, val in draft.get("section_content", {}).items():
        st.session_state[ck] = val


def _do_new() -> None:
    """Start a fresh brief."""
    _clear_all_content_keys()
    st.session_state.draft_id = new_draft_id()
    st.session_state.last_saved_msg = ""
    st.session_state.prev_brief_type = None
    for k in (
        "inp_client_name", "inp_a_number", "inp_court_or_office",
        "inp_ij_name", "inp_hearing_date", "inp_brief_type",
    ):
        if k in st.session_state:
            del st.session_state[k]


def _build_preview_html(
    brief_type: str,
    case_info: dict,
    sections_content: dict[str, str],
) -> str:
    """Render the brief as styled HTML for the live preview panel."""
    esc = html_mod.escape
    parts: list[str] = []

    # Title
    title_map = {
        "Asylum Merits Brief": "RESPONDENT'S BRIEF IN SUPPORT OF APPLICATION FOR ASYLUM",
        "Motion to Reopen": "MOTION TO REOPEN PROCEEDINGS",
        "Appeal Brief": "RESPONDENT'S BRIEF ON APPEAL",
        "Bond Brief": "RESPONDENT'S BRIEF IN SUPPORT OF BOND REDETERMINATION",
        "Cancellation of Removal": "RESPONDENT'S BRIEF IN SUPPORT OF APPLICATION FOR CANCELLATION OF REMOVAL",
    }
    parts.append(f'<div class="brief-title">{esc(title_map.get(brief_type, brief_type.upper()))}</div>')

    # Caption
    caption_lines = []
    client = case_info.get("client_name", "")
    a_num = case_info.get("a_number", "")
    court = case_info.get("court_or_office", "")
    ij = case_info.get("ij_name", "")
    hearing = case_info.get("hearing_date", "")
    if client:
        caption_lines.append(f"IN THE MATTER OF: {esc(client.upper())}")
    if a_num:
        caption_lines.append(f"A-Number: {esc(a_num)}")
    if court:
        caption_lines.append(f"Before the {esc(court)}")
    if ij:
        caption_lines.append(f"Immigration Judge {esc(ij)}")
    if hearing:
        caption_lines.append(f"Hearing Date: {esc(hearing)}")
    if caption_lines:
        parts.append(f'<div class="brief-caption">{"<br>".join(caption_lines)}</div>')

    # Sections
    sections = load_sections(brief_type)
    for idx, section in enumerate(sections):
        roman = _ROMAN[idx] if idx < len(_ROMAN) else str(idx + 1)
        heading = section["heading"]
        subs = section.get("subsections", [])

        parts.append(f'<div class="brief-heading">{roman}. {esc(heading)}</div>')

        if subs:
            for sub_idx, sub in enumerate(subs):
                sub_letter = chr(ord("A") + sub_idx)
                parts.append(f'<div class="brief-subheading">{sub_letter}. {esc(sub["heading"])}</div>')
                ck = _content_key(section["key"], sub["key"])
                body = sections_content.get(ck, "").strip()
                if body:
                    for para in body.split("\n\n"):
                        para = para.strip()
                        if para:
                            parts.append(f'<div class="brief-body">{esc(para)}</div>')
        else:
            ck = _content_key(section["key"])
            body = sections_content.get(ck, "").strip()
            if body:
                for para in body.split("\n\n"):
                    para = para.strip()
                    if para:
                        parts.append(f'<div class="brief-body">{esc(para)}</div>')

    # Signature block
    parts.append(
        '<div class="brief-sig">'
        "Respectfully submitted,<br><br>"
        "____________________________<br>"
        "Attorney for Respondent<br>"
        f"Date: {date.today().strftime('%B %d, %Y')}"
        "</div>"
    )

    return "\n".join(parts)


def _build_plain_text(
    brief_type: str,
    case_info: dict,
    sections_content: dict[str, str],
) -> str:
    """Render the brief as plain text for .txt export."""
    lines: list[str] = []

    title_map = {
        "Asylum Merits Brief": "RESPONDENT'S BRIEF IN SUPPORT OF APPLICATION FOR ASYLUM",
        "Motion to Reopen": "MOTION TO REOPEN PROCEEDINGS",
        "Appeal Brief": "RESPONDENT'S BRIEF ON APPEAL",
        "Bond Brief": "RESPONDENT'S BRIEF IN SUPPORT OF BOND REDETERMINATION",
        "Cancellation of Removal": "RESPONDENT'S BRIEF IN SUPPORT OF APPLICATION FOR CANCELLATION OF REMOVAL",
    }
    lines.append(title_map.get(brief_type, brief_type.upper()))
    lines.append("")

    # Caption
    client = case_info.get("client_name", "")
    a_num = case_info.get("a_number", "")
    court = case_info.get("court_or_office", "")
    ij = case_info.get("ij_name", "")
    hearing = case_info.get("hearing_date", "")
    if client:
        lines.append(f"IN THE MATTER OF: {client.upper()}")
    if a_num:
        lines.append(f"A-Number: {a_num}")
    if court:
        lines.append(f"Before the {court}")
    if ij:
        lines.append(f"Immigration Judge {ij}")
    if hearing:
        lines.append(f"Hearing Date: {hearing}")
    lines.append("")
    lines.append("=" * 60)
    lines.append("")

    # Sections
    sections = load_sections(brief_type)
    for idx, section in enumerate(sections):
        roman = _ROMAN[idx] if idx < len(_ROMAN) else str(idx + 1)
        heading = section["heading"]
        subs = section.get("subsections", [])

        lines.append(f"{roman}. {heading}")
        lines.append("")

        if subs:
            for sub_idx, sub in enumerate(subs):
                sub_letter = chr(ord("A") + sub_idx)
                lines.append(f"    {sub_letter}. {sub['heading']}")
                lines.append("")
                ck = _content_key(section["key"], sub["key"])
                body = sections_content.get(ck, "").strip()
                if body:
                    lines.append(f"    {body}")
                    lines.append("")
        else:
            ck = _content_key(section["key"])
            body = sections_content.get(ck, "").strip()
            if body:
                lines.append(body)
                lines.append("")

    # Signature
    lines.append("")
    lines.append("Respectfully submitted,")
    lines.append("")
    lines.append("____________________________")
    lines.append("Attorney for Respondent")
    lines.append(f"Date: {date.today().strftime('%B %d, %Y')}")

    return "\n".join(lines)


def _build_docx(
    brief_type: str,
    case_info: dict,
    sections_content: dict[str, str],
) -> bytes:
    """Build a properly formatted legal brief Word document."""
    doc = Document()

    # Page layout: 1-inch margins
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    def _run(para, text, size=12, bold=False, italic=False):
        r = para.add_run(text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(size)
        r.bold = bold
        r.italic = italic
        return r

    # Title
    title_map = {
        "Asylum Merits Brief": "RESPONDENT'S BRIEF IN SUPPORT OF APPLICATION FOR ASYLUM",
        "Motion to Reopen": "MOTION TO REOPEN PROCEEDINGS",
        "Appeal Brief": "RESPONDENT'S BRIEF ON APPEAL",
        "Bond Brief": "RESPONDENT'S BRIEF IN SUPPORT OF BOND REDETERMINATION",
        "Cancellation of Removal": "RESPONDENT'S BRIEF IN SUPPORT OF APPLICATION FOR CANCELLATION OF REMOVAL",
    }
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _run(p, title_map.get(brief_type, brief_type.upper()), size=14, bold=True)

    # Caption block
    client = case_info.get("client_name", "")
    a_num = case_info.get("a_number", "")
    court = case_info.get("court_or_office", "")
    ij = case_info.get("ij_name", "")
    hearing = case_info.get("hearing_date", "")

    caption_lines = []
    if client:
        caption_lines.append(f"IN THE MATTER OF: {client.upper()}")
    if a_num:
        caption_lines.append(f"A-Number: {a_num}")
    if court:
        caption_lines.append(f"Before the {court}")
    if ij:
        caption_lines.append(f"Immigration Judge {ij}")
    if hearing:
        caption_lines.append(f"Hearing Date: {hearing}")

    if caption_lines:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(p, "\n".join(caption_lines), size=11)
        p.paragraph_format.space_after = Pt(12)

    # Spacer
    doc.add_paragraph()

    # Sections
    sections = load_sections(brief_type)
    for idx, section in enumerate(sections):
        roman = _ROMAN[idx] if idx < len(_ROMAN) else str(idx + 1)
        heading = section["heading"]
        subs = section.get("subsections", [])

        # Section heading
        p = doc.add_paragraph()
        _run(p, f"{roman}. {heading}", bold=True)
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)

        if subs:
            for sub_idx, sub in enumerate(subs):
                sub_letter = chr(ord("A") + sub_idx)

                # Subsection heading
                p = doc.add_paragraph()
                _run(p, f"    {sub_letter}. {sub['heading']}", bold=True, italic=True)
                p.paragraph_format.space_before = Pt(6)
                p.paragraph_format.space_after = Pt(4)

                # Body text
                ck = _content_key(section["key"], sub["key"])
                body = sections_content.get(ck, "").strip()
                if body:
                    for para_text in body.split("\n\n"):
                        para_text = para_text.strip()
                        if para_text:
                            p = doc.add_paragraph()
                            _run(p, para_text)
                            p.paragraph_format.line_spacing = 2.0
                            p.paragraph_format.space_after = Pt(0)
        else:
            ck = _content_key(section["key"])
            body = sections_content.get(ck, "").strip()
            if body:
                for para_text in body.split("\n\n"):
                    para_text = para_text.strip()
                    if para_text:
                        p = doc.add_paragraph()
                        _run(p, para_text)
                        p.paragraph_format.line_spacing = 2.0
                        p.paragraph_format.space_after = Pt(0)

    # Signature block
    doc.add_paragraph()
    doc.add_paragraph()
    p = doc.add_paragraph()
    _run(p, "Respectfully submitted,")
    doc.add_paragraph()
    doc.add_paragraph()
    p = doc.add_paragraph()
    _run(p, "____________________________")
    p = doc.add_paragraph()
    _run(p, "Attorney for Respondent")
    p = doc.add_paragraph()
    _run(p, f"Date: {date.today().strftime('%B %d, %Y')}")

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
            d["id"]: f"{d['client_name']} -- {d['brief_type']}"
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

    # Brief type
    brief_type = st.selectbox(
        "Brief Type",
        options=list(BRIEF_TYPES.keys()),
        key="inp_brief_type",
    )

    # If brief type changed, clear section content for fresh start
    if st.session_state.prev_brief_type is not None and st.session_state.prev_brief_type != brief_type:
        _clear_all_content_keys()
    st.session_state.prev_brief_type = brief_type

    st.divider()

    # Case information
    st.markdown("#### Case Information")
    client_name = st.text_input(
        "Client Name",
        key="inp_client_name",
        placeholder="e.g. Maria Garcia-Lopez",
    )
    a_number = st.text_input(
        "A-Number",
        key="inp_a_number",
        placeholder="e.g. A 012-345-678",
    )
    court_or_office = st.text_input(
        "Court / Office",
        key="inp_court_or_office",
        placeholder="e.g. San Francisco Immigration Court",
    )
    ij_name = st.text_input(
        "Immigration Judge",
        key="inp_ij_name",
        placeholder="e.g. Hon. Jane Smith",
    )
    hearing_date = st.text_input(
        "Hearing Date",
        key="inp_hearing_date",
        placeholder="e.g. March 15, 2026",
    )


# -- Handle save (after sidebar renders) --------------------------------------

if save_clicked:
    _do_save(brief_type)
    st.rerun()


# -- Main area ----------------------------------------------------------------

sections = load_sections(brief_type)

edit_col, preview_col = st.columns([3, 2], gap="large")

# -- Left column: Section editing ---------------------------------------------

with edit_col:
    st.markdown('<div class="section-label">Brief Sections</div>', unsafe_allow_html=True)
    st.caption(f"Drafting: {brief_type}")

    for section in sections:
        section_key = section["key"]
        heading = section["heading"]
        subs = section.get("subsections", [])
        section_boilerplate = section.get("boilerplate", "")

        with st.expander(heading, expanded=False):

            # Section-level boilerplate
            if section_boilerplate:
                st.markdown(
                    f'<div class="boilerplate-block">'
                    f"<strong>Standard language:</strong><br>"
                    f"{html_mod.escape(section_boilerplate)}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                ck = _content_key(section_key)
                insert_key = f"insert_{section_key}"
                if st.button("Insert Boilerplate", key=insert_key):
                    st.session_state[ck] = section_boilerplate
                    st.rerun()

            if subs:
                for sub in subs:
                    sub_key = sub["key"]
                    sub_heading = sub["heading"]
                    sub_boilerplate = sub.get("boilerplate", "")

                    st.markdown(f"**{sub_heading}**")

                    if sub_boilerplate:
                        st.markdown(
                            f'<div class="boilerplate-block">'
                            f"<strong>Standard language:</strong><br>"
                            f"{html_mod.escape(sub_boilerplate)}"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                        ck = _content_key(section_key, sub_key)
                        insert_key = f"insert_{section_key}_{sub_key}"
                        if st.button("Insert Boilerplate", key=insert_key):
                            st.session_state[ck] = sub_boilerplate
                            st.rerun()

                    ck = _content_key(section_key, sub_key)
                    st.text_area(
                        f"Content for {sub_heading}",
                        height=150,
                        key=ck,
                        placeholder=f"Draft your {sub_heading.lower()} argument here...",
                        label_visibility="collapsed",
                    )
            else:
                # Single section without subsections
                ck = _content_key(section_key)
                height = 200 if section_key in ("statement_of_facts", "country_conditions") else 150
                st.text_area(
                    f"Content for {heading}",
                    height=height,
                    key=ck,
                    placeholder=f"Draft your {heading.lower()} here...",
                    label_visibility="collapsed",
                )

# -- Right column: Live preview + export --------------------------------------

with preview_col:
    st.markdown('<div class="section-label">Brief Preview</div>', unsafe_allow_html=True)

    # Gather current case info
    case_info = {
        "client_name": st.session_state.get("inp_client_name", ""),
        "a_number": st.session_state.get("inp_a_number", ""),
        "court_or_office": st.session_state.get("inp_court_or_office", ""),
        "ij_name": st.session_state.get("inp_ij_name", ""),
        "hearing_date": st.session_state.get("inp_hearing_date", ""),
    }

    # Gather section content
    sections_content = _collect_section_content(brief_type)

    # Check if there is any content at all
    has_content = any(v.strip() for v in sections_content.values())

    if not case_info["client_name"]:
        st.info("Enter the client's name in the sidebar to see the live preview.")
    else:
        preview_html = _build_preview_html(brief_type, case_info, sections_content)
        st.markdown(
            f'<div class="preview-panel">{preview_html}</div>',
            unsafe_allow_html=True,
        )

    # Export controls
    st.markdown("---")
    st.markdown('<div class="section-label">Export</div>', unsafe_allow_html=True)

    safe_name = (case_info["client_name"] or "Brief").replace(" ", "_")

    exp_cols = st.columns(2)
    with exp_cols[0]:
        if has_content and case_info["client_name"]:
            plain_text = _build_plain_text(brief_type, case_info, sections_content)
            st.download_button(
                "Download .txt",
                data=plain_text,
                file_name=f"{brief_type.replace(' ', '_')}_{safe_name}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        else:
            st.button("Download .txt", disabled=True, use_container_width=True)

    with exp_cols[1]:
        if has_content and case_info["client_name"]:
            docx_bytes = _build_docx(brief_type, case_info, sections_content)
            st.download_button(
                "Download .docx",
                data=docx_bytes,
                file_name=f"{brief_type.replace(' ', '_')}_{safe_name}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        else:
            st.button("Download .docx", disabled=True, use_container_width=True)
