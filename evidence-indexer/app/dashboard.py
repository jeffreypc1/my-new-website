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
        "Manage all template types from one place. Changes are saved to config "
        "and shared with other tools automatically."
    )
    render_tool_notes("evidence-indexer")


# -- Tabs ---------------------------------------------------------------------

tab_email, tab_client, tab_govt, tab_eoir = st.tabs([
    "Email Templates",
    "Client Cover Letters",
    "Government Cover Letters",
    "EOIR Templates",
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
        "Templates for government cover letters used by the Cover Pages tool. "
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
