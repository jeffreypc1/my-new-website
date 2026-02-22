"""Templates — Streamlit dashboard for managing all template types.

Centralized template management for email templates, client cover letters,
government cover letters, and EOIR templates. Replaces the Evidence Indexer
dashboard (evidence.py and api.py remain in the directory untouched).

Part of the O'Brien Immigration Law tool suite.
"""

from __future__ import annotations

import copy
import html as html_mod
import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.client_banner import render_client_banner
from shared.tool_notes import render_tool_notes
import streamlit.components.v1 as st_components

from app.templates_store import (
    EOIR_CATEGORIES,
    get_client_letter_templates,
    get_email_templates,
    get_eoir_templates,
    get_govt_letter_templates,
    save_client_letter_templates,
    save_email_templates,
    save_eoir_templates,
    save_govt_letter_templates,
)
from app.brief_sections_store import (
    MERGE_FIELDS,
    get_boilerplate,
    get_brief_types,
    resolve_merge_fields,
    save_brief_config,
)

_brief_canvas_component = st_components.declare_component(
    "brief_sections_canvas",
    path=str(Path(__file__).resolve().parent / "brief_sections_canvas"),
)

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
    page_title="Templates -- O'Brien Immigration Law",
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
    <div class="nav-title">Templates<span class="nav-firm">&mdash; O'Brien Immigration Law</span></div>
    <div class="nav-spacer"></div>
</div>
""",
    unsafe_allow_html=True,
)
render_logout()

render_client_banner()
if render_tool_help:
    render_tool_help("evidence-indexer")
if render_feedback_button:
    render_feedback_button("evidence-indexer")


# -- Helpers ------------------------------------------------------------------


def _esc(text: str) -> str:
    """HTML-escape a string."""
    return html_mod.escape(str(text))


# -- Sidebar ------------------------------------------------------------------

with st.sidebar:
    st.markdown("#### Templates")
    st.caption(
        "Manage all template types — including email, cover letters, EOIR filings, "
        "and brief sections — from one place. Changes are saved to config "
        "and shared with other tools automatically."
    )
    render_tool_notes("evidence-indexer")


# -- Tabs ---------------------------------------------------------------------

tab_email, tab_client, tab_govt, tab_eoir, tab_brief = st.tabs([
    "Email Templates",
    "Client Cover Letters",
    "Government Cover Letters",
    "EOIR Templates",
    "Brief Sections",
])


# =============================================================================
# Tab 1: Email Templates
# =============================================================================

def _render_email_templates() -> None:
    st.caption(
        "Create and edit email templates. Use {field_name} placeholders that will "
        "be filled with client data when composing. Templates are available in the "
        "Email button on every tool."
    )

    templates = get_email_templates()

    # Merge field reference
    with st.expander("Available merge fields"):
        st.markdown(
            "| Placeholder | Description |\n"
            "|---|---|\n"
            "| `{first_name}` | Client first name |\n"
            "| `{last_name}` | Client last name |\n"
            "| `{name}` | Full name |\n"
            "| `{customer_id}` | Client number |\n"
            "| `{a_number}` | Alien registration number |\n"
            "| `{email}` | Client email |\n"
            "| `{phone}` | Phone number |\n"
            "| `{country}` | Country of origin |\n"
            "| `{language}` | Preferred language |\n"
            "| `{immigration_status}` | Immigration status |\n"
            "| `{case_type}` | Legal case type |\n"
            "| `{case_number}` | Case number |\n"
            "| `{court}` | Immigration court |\n"
            "| `{dob}` | Date of birth |\n"
            "| `{spouse}` | Spouse name |\n"
        )

    # Add new template
    with st.expander("Add New Template"):
        new_name = st.text_input("Template Name", key="_et_new_name", placeholder="e.g. Hearing Reminder")
        new_subject = st.text_input("Subject", key="_et_new_subject")
        new_body = st.text_area("Body", key="_et_new_body", height=150)
        if st.button("Add Template", type="primary", key="_et_add"):
            if not new_name.strip():
                st.warning("Template name is required.")
            else:
                templates.append({
                    "id": f"custom_{int(time.time() * 1000)}",
                    "name": new_name.strip(),
                    "subject": new_subject,
                    "body": new_body,
                })
                save_email_templates(templates)
                st.toast(f"Added template: {new_name.strip()}")
                st.rerun()

    # List / edit existing templates
    if not templates:
        st.info("No templates. Add one above.")
        return

    st.markdown(f"**{len(templates)} template{'s' if len(templates) != 1 else ''}**")

    templates_to_delete: list[int] = []

    for idx, tpl in enumerate(templates):
        with st.expander(tpl.get("name", f"Template {idx + 1}")):
            tpl["name"] = st.text_input("Name", value=tpl.get("name", ""), key=f"_et_name_{idx}")
            tpl["subject"] = st.text_input("Subject", value=tpl.get("subject", ""), key=f"_et_subj_{idx}")
            tpl["body"] = st.text_area("Body", value=tpl.get("body", ""), key=f"_et_body_{idx}", height=200)
            if st.button("Delete", key=f"_et_del_{idx}"):
                templates_to_delete.append(idx)

    if templates_to_delete:
        for idx in sorted(templates_to_delete, reverse=True):
            removed = templates.pop(idx)
            st.toast(f"Removed template: {removed.get('name', '')}")
        save_email_templates(templates)
        st.rerun()

    if st.button("Save Email Templates", type="primary", key="_et_save"):
        save_email_templates(templates)
        st.toast("Email templates saved!")


with tab_email:
    _render_email_templates()


# =============================================================================
# Tab 2: Client Cover Letter Templates
# =============================================================================

def _render_client_letter_templates() -> None:
    st.caption(
        "Templates for letters addressed to the client — appointment letters, "
        "status updates, document requests. Use {field_name} placeholders for "
        "merge fields."
    )

    templates = get_client_letter_templates()

    # Merge field reference
    with st.expander("Available merge fields"):
        st.markdown(
            "| Placeholder | Description |\n"
            "|---|---|\n"
            "| `{first_name}` | Client first name |\n"
            "| `{last_name}` | Client last name |\n"
            "| `{name}` | Full name |\n"
            "| `{customer_id}` | Client number |\n"
            "| `{a_number}` | Alien registration number |\n"
            "| `{case_type}` | Legal case type |\n"
            "| `{country}` | Country of origin |\n"
        )

    # Add new template
    with st.expander("Add New Template"):
        new_name = st.text_input("Template Name", key="_cl_new_name", placeholder="e.g. Retainer Agreement Cover")
        new_subject = st.text_input("Subject", key="_cl_new_subject")
        new_body = st.text_area("Body", key="_cl_new_body", height=200)
        if st.button("Add Template", type="primary", key="_cl_add"):
            if not new_name.strip():
                st.warning("Template name is required.")
            else:
                templates.append({
                    "id": f"client_{int(time.time() * 1000)}",
                    "name": new_name.strip(),
                    "subject": new_subject,
                    "body": new_body,
                })
                save_client_letter_templates(templates)
                st.toast(f"Added template: {new_name.strip()}")
                st.rerun()

    # List / edit existing templates
    if not templates:
        st.info("No templates. Add one above.")
        return

    st.markdown(f"**{len(templates)} template{'s' if len(templates) != 1 else ''}**")

    templates_to_delete: list[int] = []

    for idx, tpl in enumerate(templates):
        with st.expander(tpl.get("name", f"Template {idx + 1}")):
            tpl["name"] = st.text_input("Name", value=tpl.get("name", ""), key=f"_cl_name_{idx}")
            tpl["subject"] = st.text_input("Subject", value=tpl.get("subject", ""), key=f"_cl_subj_{idx}")
            tpl["body"] = st.text_area("Body", value=tpl.get("body", ""), key=f"_cl_body_{idx}", height=200)
            if st.button("Delete", key=f"_cl_del_{idx}"):
                templates_to_delete.append(idx)

    if templates_to_delete:
        for idx in sorted(templates_to_delete, reverse=True):
            removed = templates.pop(idx)
            st.toast(f"Removed template: {removed.get('name', '')}")
        save_client_letter_templates(templates)
        st.rerun()

    if st.button("Save Client Letter Templates", type="primary", key="_cl_save"):
        save_client_letter_templates(templates)
        st.toast("Client letter templates saved!")


with tab_client:
    _render_client_letter_templates()


# =============================================================================
# Tab 3: Government Cover Letter Templates
# =============================================================================

def _render_govt_letter_templates() -> None:
    st.caption(
        "Templates for government cover letters used by the Filing Assembler tool. "
        "Each case type has standard enclosed documents, purpose and closing paragraphs."
    )

    templates = get_govt_letter_templates()
    case_types = list(templates.keys())

    if not case_types:
        st.info("No government cover letter templates found.")
        return

    selected_case_type = st.selectbox(
        "Case Type",
        case_types,
        key="_govt_case_type",
    )

    tpl = templates[selected_case_type]

    st.markdown(f"**{selected_case_type}**")

    # Form numbers
    form_nums_str = st.text_input(
        "Form Numbers (comma-separated)",
        value=", ".join(tpl.get("form_numbers", [])),
        key="_govt_forms",
    )

    # Filing offices
    offices_str = st.text_area(
        "Filing Offices (one per line)",
        value="\n".join(tpl.get("filing_offices", [])),
        key="_govt_offices",
        height=120,
    )

    # Standard enclosed docs
    docs_str = st.text_area(
        "Standard Enclosed Documents (one per line)",
        value="\n".join(tpl.get("standard_enclosed_docs", [])),
        key="_govt_docs",
        height=200,
    )

    # Purpose paragraph
    purpose = st.text_area(
        "Purpose Paragraph",
        value=tpl.get("purpose_paragraph", ""),
        key="_govt_purpose",
        height=150,
    )

    # Closing paragraph
    closing = st.text_area(
        "Closing Paragraph",
        value=tpl.get("closing_paragraph", ""),
        key="_govt_closing",
        height=150,
    )

    if st.button("Save Government Templates", type="primary", key="_govt_save"):
        tpl["form_numbers"] = [f.strip() for f in form_nums_str.split(",") if f.strip()]
        tpl["filing_offices"] = [o.strip() for o in offices_str.strip().splitlines() if o.strip()]
        tpl["standard_enclosed_docs"] = [d.strip() for d in docs_str.strip().splitlines() if d.strip()]
        tpl["purpose_paragraph"] = purpose
        tpl["closing_paragraph"] = closing
        templates[selected_case_type] = tpl
        save_govt_letter_templates(templates)
        st.toast(f"Saved {selected_case_type} template!")


with tab_govt:
    _render_govt_letter_templates()


# =============================================================================
# Tab 4: EOIR Templates
# =============================================================================

def _render_eoir_templates() -> None:
    st.caption(
        "Templates for EOIR-specific filings — motions, notices, certificates "
        "of service, and other court documents. Use {client_name}, {a_number}, "
        "and {date} as placeholders."
    )

    templates = get_eoir_templates()

    # Add new template
    with st.expander("Add New Template"):
        new_name = st.text_input("Template Name", key="_eoir_new_name", placeholder="e.g. Motion to Adjourn")
        new_category = st.selectbox("Category", EOIR_CATEGORIES, key="_eoir_new_cat")
        new_body = st.text_area("Body", key="_eoir_new_body", height=250)
        if st.button("Add Template", type="primary", key="_eoir_add"):
            if not new_name.strip():
                st.warning("Template name is required.")
            else:
                templates.append({
                    "id": f"eoir_{int(time.time() * 1000)}",
                    "name": new_name.strip(),
                    "category": new_category,
                    "body": new_body,
                })
                save_eoir_templates(templates)
                st.toast(f"Added template: {new_name.strip()}")
                st.rerun()

    # List / edit existing templates
    if not templates:
        st.info("No EOIR templates. Add one above.")
        return

    st.markdown(f"**{len(templates)} template{'s' if len(templates) != 1 else ''}**")

    templates_to_delete: list[int] = []

    for idx, tpl in enumerate(templates):
        with st.expander(f"{tpl.get('name', f'Template {idx + 1}')} ({tpl.get('category', 'Other')})"):
            tpl["name"] = st.text_input("Name", value=tpl.get("name", ""), key=f"_eoir_name_{idx}")
            tpl["category"] = st.selectbox(
                "Category",
                EOIR_CATEGORIES,
                index=EOIR_CATEGORIES.index(tpl.get("category", "Other")) if tpl.get("category", "Other") in EOIR_CATEGORIES else len(EOIR_CATEGORIES) - 1,
                key=f"_eoir_cat_{idx}",
            )
            tpl["body"] = st.text_area("Body", value=tpl.get("body", ""), key=f"_eoir_body_{idx}", height=300)
            if st.button("Delete", key=f"_eoir_del_{idx}"):
                templates_to_delete.append(idx)

    if templates_to_delete:
        for idx in sorted(templates_to_delete, reverse=True):
            removed = templates.pop(idx)
            st.toast(f"Removed template: {removed.get('name', '')}")
        save_eoir_templates(templates)
        st.rerun()

    if st.button("Save EOIR Templates", type="primary", key="_eoir_save"):
        save_eoir_templates(templates)
        st.toast("EOIR templates saved!")


with tab_eoir:
    _render_eoir_templates()


# =============================================================================
# Tab 5: Brief Sections
# =============================================================================

def _render_brief_config_editor() -> None:
    """Manage brief types, sections, and boilerplate — migrated from Admin Panel."""
    brief_types: dict = get_brief_types()
    boilerplate: dict = get_boilerplate()

    # -- Merge field reference --
    with st.expander("Merge field reference"):
        rows = "| Placeholder | Description |\n|---|---|\n"
        for ph, desc in MERGE_FIELDS.items():
            rows += f"| `{ph}` | {desc} |\n"
        st.markdown(rows)

    st.subheader("Brief Types & Sections")

    type_names = list(brief_types.keys())

    # Add new brief type
    c1, c2 = st.columns([4, 1])
    with c1:
        new_bt = st.text_input("New brief type", key="_bs_new_type", placeholder="e.g. SIJS Brief")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", key="_bs_add_type") and new_bt.strip():
            if new_bt.strip() not in type_names:
                type_names.append(new_bt.strip())
                brief_types[new_bt.strip()] = []
                boilerplate.setdefault(new_bt.strip(), {})

    # Delete brief type
    to_delete = []
    for i, tn in enumerate(type_names):
        c1, c2 = st.columns([8, 1])
        with c1:
            n_secs = len(brief_types.get(tn, []))
            st.text(f"{tn}  ({n_secs} section{'s' if n_secs != 1 else ''})")
        with c2:
            if st.button("X", key=f"_bs_del_{i}"):
                to_delete.append(tn)
    for d in to_delete:
        type_names.remove(d)
        brief_types.pop(d, None)
        boilerplate.pop(d, None)

    st.divider()
    st.subheader("Sections & Boilerplate")

    if type_names:
        sel_bt = st.selectbox("Select brief type", type_names, key="_bs_sel_type")
        sections = brief_types.get(sel_bt, [])
        bp = boilerplate.get(sel_bt, {})

        sec_to_delete = []
        for idx, sec in enumerate(sections):
            with st.expander(f"{sec.get('heading', 'Section')} ({sec.get('key', '')})"):
                heading = st.text_input("Heading", value=sec.get("heading", ""), key=f"_bs_sec_h_{sel_bt}_{idx}")
                key = st.text_input("Key", value=sec.get("key", ""), key=f"_bs_sec_k_{sel_bt}_{idx}")
                sec["heading"] = heading
                sec["key"] = key

                # Boilerplate for this section
                bp_text = bp.get(key, "")
                new_bp = st.text_area("Boilerplate", value=bp_text, key=f"_bs_bp_{sel_bt}_{idx}", height=120)
                if new_bp.strip():
                    bp[key] = new_bp
                elif key in bp:
                    del bp[key]

                # Subsections
                subs = sec.get("subsections", [])
                if subs:
                    st.caption("Subsections:")
                    sub_to_delete = []
                    for si, sub in enumerate(subs):
                        c1, c2, c3 = st.columns([3, 3, 1])
                        with c1:
                            sub["heading"] = st.text_input("Sub heading", value=sub.get("heading", ""), key=f"_bs_sub_h_{sel_bt}_{idx}_{si}")
                        with c2:
                            sub["key"] = st.text_input("Sub key", value=sub.get("key", ""), key=f"_bs_sub_k_{sel_bt}_{idx}_{si}")
                        with c3:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("X", key=f"_bs_sub_del_{sel_bt}_{idx}_{si}"):
                                sub_to_delete.append(si)
                        sub_bp = bp.get(sub["key"], "")
                        new_sub_bp = st.text_area("Sub boilerplate", value=sub_bp, key=f"_bs_sub_bp_{sel_bt}_{idx}_{si}", height=100)
                        if new_sub_bp.strip():
                            bp[sub["key"]] = new_sub_bp
                        elif sub["key"] in bp:
                            del bp[sub["key"]]
                    for si in sorted(sub_to_delete, reverse=True):
                        subs.pop(si)

                # Add subsection button
                if st.button("+ Add subsection", key=f"_bs_sub_add_{sel_bt}_{idx}"):
                    subs.append({"heading": "", "key": ""})
                sec["subsections"] = subs

                # Delete section button
                if st.button("Delete section", key=f"_bs_sec_del_{sel_bt}_{idx}"):
                    sec_to_delete.append(idx)

        for idx in sorted(sec_to_delete, reverse=True):
            sections.pop(idx)

        # Add section
        if st.button("+ Add section", key=f"_bs_sec_add_{sel_bt}"):
            sections.append({"heading": "", "key": "", "subsections": []})

        boilerplate[sel_bt] = bp
        brief_types[sel_bt] = sections

    if st.button("Save Brief Builder Config", type="primary", key="_bs_save"):
        save_brief_config(brief_types, boilerplate)
        st.toast("Brief Builder config saved!")


def _render_brief_assembler() -> None:
    """Assemble a brief draft from sections with drag-and-drop canvas."""

    brief_types = get_brief_types()
    all_boilerplate = get_boilerplate()
    type_names = list(brief_types.keys())

    if not type_names:
        st.info("No brief types defined. Switch to Manage Templates to create one.")
        return

    selected_type = st.selectbox("Brief type", type_names, key="_bs_assemble_type")

    # Detect brief type change → reset canvas
    prev_type = st.session_state.get("_bs_prev_type", "")
    type_changed = selected_type != prev_type
    if type_changed:
        st.session_state["_bs_prev_type"] = selected_type
        st.session_state.pop("_bs_canvas_order", None)
        st.session_state.pop("_bs_canvas_edits", None)
        st.session_state.pop("_bs_disabled_ids", None)

    # Build flat block list from sections + subsections
    sections = brief_types.get(selected_type, [])
    bp = all_boilerplate.get(selected_type, {})
    canvas_blocks = []
    for sec in sections:
        content = bp.get(sec["key"], "")
        canvas_blocks.append({
            "id": sec["key"],
            "label": sec["heading"],
            "heading": sec["heading"],
            "content": content,
            "depth": 0,
        })
        for sub in sec.get("subsections", []):
            sub_content = bp.get(sub["key"], "")
            canvas_blocks.append({
                "id": sub["key"],
                "label": sub["heading"],
                "heading": sub["heading"],
                "content": sub_content,
                "depth": 1,
            })

    # Merge field values
    with st.expander("Merge field values", expanded=False):
        field_values = {}
        for ph, desc in MERGE_FIELDS.items():
            field_key = f"_bs_field_{ph}"
            val = st.text_input(desc, key=field_key, placeholder=ph)
            if val.strip():
                field_values[ph] = val.strip()

    # Two-column layout: toggle list + canvas
    col_toggle, col_canvas = st.columns([1, 3])

    disabled_ids = list(st.session_state.get("_bs_disabled_ids", []))

    with col_toggle:
        st.caption("Sections")
        for blk in canvas_blocks:
            enabled = blk["id"] not in disabled_ids
            new_val = st.checkbox(
                blk["label"],
                value=enabled,
                key=f"_bs_toggle_{blk['id']}",
            )
            if new_val and blk["id"] in disabled_ids:
                disabled_ids.remove(blk["id"])
            elif not new_val and blk["id"] not in disabled_ids:
                disabled_ids.append(blk["id"])
        st.session_state["_bs_disabled_ids"] = disabled_ids

    with col_canvas:
        canvas_result = _brief_canvas_component(
            blocks=canvas_blocks,
            block_order=st.session_state.get("_bs_canvas_order"),
            block_edits=st.session_state.get("_bs_canvas_edits", {}),
            disabled_ids=disabled_ids,
            reset=type_changed,
            height=600,
            key="_bs_canvas",
        )

    # Process canvas result
    if canvas_result:
        if isinstance(canvas_result, dict):
            action = canvas_result.get("action")
            if action == "reset":
                st.session_state.pop("_bs_canvas_order", None)
                st.session_state.pop("_bs_canvas_edits", None)
                st.session_state["_bs_disabled_ids"] = []
                st.rerun()
            st.session_state["_bs_canvas_order"] = canvas_result.get("block_order")
            st.session_state["_bs_canvas_edits"] = canvas_result.get("block_edits", {})
            if canvas_result.get("disabled_ids") is not None:
                st.session_state["_bs_disabled_ids"] = canvas_result["disabled_ids"]

    # -- Assembled output preview --
    st.divider()
    st.subheader("Assembled Output")

    order = st.session_state.get("_bs_canvas_order") or [b["id"] for b in canvas_blocks]
    edits = st.session_state.get("_bs_canvas_edits", {})
    final_disabled = st.session_state.get("_bs_disabled_ids", [])

    block_map = {b["id"]: b for b in canvas_blocks}
    assembled_parts = []
    for bid in order:
        if bid in final_disabled:
            continue
        blk = block_map.get(bid)
        if not blk:
            continue
        content = edits.get(bid) if edits.get(bid) is not None else blk["content"]
        if field_values:
            content = resolve_merge_fields(content, field_values)
        heading = blk["heading"]
        if field_values:
            heading = resolve_merge_fields(heading, field_values)
        prefix = "    " if blk.get("depth", 0) >= 1 else ""
        assembled_parts.append(f"{prefix}{heading}\n\n{prefix}{content}")

    assembled_text = "\n\n\n".join(assembled_parts)

    if assembled_text.strip():
        st.text_area("Preview", value=assembled_text, height=400, disabled=True, key="_bs_preview")
        st.download_button(
            "Download .txt",
            data=assembled_text,
            file_name=f"{selected_type.replace(' ', '_').lower()}_draft.txt",
            mime="text/plain",
            key="_bs_download",
        )
    else:
        st.info("Enable sections and add content to see the assembled output.")


def _render_brief_sections() -> None:
    """Brief Sections tab — mode toggle between config editor and assembler."""
    st.caption(
        "Manage brief type templates and assemble draft briefs. "
        "Use {variable} placeholders for merge fields."
    )

    mode = st.radio(
        "Mode",
        ["Manage Templates", "Assemble Brief"],
        horizontal=True,
        key="_bs_mode",
    )

    if mode == "Manage Templates":
        _render_brief_config_editor()
    else:
        _render_brief_assembler()


with tab_brief:
    _render_brief_sections()
