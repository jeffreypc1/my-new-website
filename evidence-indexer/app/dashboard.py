"""Templates — Streamlit dashboard for managing all template types.

Centralized template management for email, letters, court filings, briefs,
declarations, filing packets, contracts, checklists, and outcome documents.
Replaces the Evidence Indexer dashboard (evidence.py and api.py remain in
the directory untouched).

Part of the O'Brien Immigration Law tool suite.
"""

from __future__ import annotations

import copy
import html as html_mod
import sys
import time
from collections.abc import Callable
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.layout import init_layout
import streamlit.components.v1 as st_components

from app.templates_store import (
    CHECKLIST_CATEGORIES,
    COURT_FILING_CATEGORIES,
    get_checklist_templates,
    get_client_letter_templates,
    get_contract_templates,
    get_court_filing_templates,
    get_declaration_templates,
    get_email_templates,
    get_govt_letter_templates,
    get_outcome_templates,
    save_checklist_templates,
    save_client_letter_templates,
    save_contract_templates,
    save_court_filing_templates,
    save_declaration_templates,
    save_email_templates,
    save_govt_letter_templates,
    save_outcome_templates,
)
from app.brief_sections_store import (
    MERGE_FIELDS,
    get_boilerplate,
    get_brief_types,
    resolve_merge_fields,
    save_brief_config,
)
from app.merge_fields_store import (
    MANAGED_OBJECTS,
    find_duplicate_aliases,
    get_enabled_merge_fields,
    get_field_cache,
    get_merge_field_config,
    refresh_all_field_caches,
    refresh_field_cache,
    save_merge_field_config,
)
from app.foundation_store import (
    get_foundation_by_id,
    get_foundations,
    merge_template_with_foundation,
    save_foundation,
)
from app.template_exporter import (
    build_template_docx,
    build_template_pdf,
    resolve_merge_fields_for_export,
)

_brief_canvas_component = st_components.declare_component(
    "brief_sections_canvas",
    path=str(Path(__file__).resolve().parent / "brief_sections_canvas"),
)

_template_canvas_component = st_components.declare_component(
    "template_canvas",
    path=str(Path(__file__).resolve().parent / "template_canvas"),
)

# -- Layout -------------------------------------------------------------------

zones = init_layout(
    tool_name="evidence-indexer",
    tool_title="Templates",
    right_rail=False,
    extra_css="""
        /* Prevent Streamlit from fading the template canvas during reruns.
           Streamlit applies opacity:0.33 via styled-components on stale elements.
           We override with !important on [data-stale] attribute selectors. */
        [data-stale="true"] {
            opacity: 1 !important;
            transition: none !important;
        }
    """,
)


# -- Helpers ------------------------------------------------------------------


def _esc(text: str) -> str:
    """HTML-escape a string."""
    return html_mod.escape(str(text))


def _render_export_buttons(
    foundation_id: str,
    canvas_sections: list[dict],
    order_key: str,
    edits_key: str,
    disabled_key: str,
    default_disabled: list[str],
    key_prefix: str,
) -> None:
    """Render Word / PDF / Google Docs export row below a canvas."""
    block_order = st.session_state.get(order_key) or [s["id"] for s in canvas_sections]
    block_edits = st.session_state.get(edits_key, {})
    disabled_ids = st.session_state.get(disabled_key, default_disabled)

    # Resolve merge fields — real client data if loaded, sample fallback
    sf_client = st.session_state.get("sf_client")
    legal_case = sf_client.get("selected_legal_case") if sf_client else None
    merge_values = resolve_merge_fields_for_export(sf_client, legal_case)

    # Letterhead toggle — only show if a letterhead image has been uploaded
    from app.template_exporter import _get_letterhead_path
    has_letterhead = _get_letterhead_path() is not None
    include_logo = False
    if has_letterhead:
        include_logo = st.checkbox("Include letterhead", value=True, key=f"_{key_prefix}_incl_logo")

    docx_bytes = build_template_docx(
        foundation_id, canvas_sections, block_order, block_edits, disabled_ids,
        merge_values=merge_values,
        include_letterhead=include_logo,
    )
    pdf_bytes = build_template_pdf(
        foundation_id, canvas_sections, block_order, block_edits, disabled_ids,
        merge_values=merge_values,
        include_letterhead=include_logo,
    )

    exp_cols = st.columns(3)
    with exp_cols[0]:
        st.download_button(
            "Download Word (.docx)",
            data=docx_bytes,
            file_name="template.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"_{key_prefix}_dl_docx",
        )
    with exp_cols[1]:
        st.download_button(
            "Download PDF",
            data=pdf_bytes,
            file_name="template.pdf",
            mime="application/pdf",
            key=f"_{key_prefix}_dl_pdf",
        )
    with exp_cols[2]:
        if st.button("Open in Google Docs", key=f"_{key_prefix}_gdoc"):
            with st.spinner("Uploading to Google Docs..."):
                try:
                    from shared.google_upload import upload_to_google_docs

                    url = upload_to_google_docs(docx_bytes, "Template Preview")
                    st.session_state[f"_{key_prefix}_gdoc_url"] = url
                except Exception as e:
                    st.error(f"Upload failed: {e}")
        gdoc_url = st.session_state.get(f"_{key_prefix}_gdoc_url")
        if gdoc_url:
            st.markdown(f"[Open Google Doc]({gdoc_url})")

    # Inline PDF preview
    with st.expander("Preview"):
        import base64

        b64 = base64.b64encode(pdf_bytes).decode()
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{b64}" '
            f'width="100%" height="800" style="border:1px solid #ddd; border-radius:4px;">'
            f"</iframe>",
            unsafe_allow_html=True,
        )


def _render_merge_fields_table(
    fields: list[tuple[str, str]] | None = None,
    *,
    key_prefix: str = "",
) -> None:
    """Render a merge fields expander with a markdown table.

    If *fields* is None, uses the centralized merge field config with
    radio-button filtering by source object.
    Legacy callers can still pass a list of (placeholder, description) tuples.
    """
    with st.expander("Available merge fields"):
        if fields is not None:
            rows = "| Placeholder | Description |\n|---|---|\n"
            for placeholder, description in fields:
                rows += f"| `{{{placeholder}}}` | {description} |\n"
            st.markdown(rows)
        else:
            enabled = get_enabled_merge_fields()
            sources = ["All"] + [obj["tab_label"] for obj in MANAGED_OBJECTS]
            selected = st.radio(
                "Source",
                sources,
                horizontal=True,
                key=f"_mf_radio_{key_prefix}",
                label_visibility="collapsed",
            )
            if selected != "All":
                enabled = [e for e in enabled if e[2] == selected]
            rows = "| Placeholder | Description | Source |\n|---|---|---|\n"
            for alias, label, source in enabled:
                rows += f"| `{{{alias}}}` | {label} | {source} |\n"
            st.markdown(rows)


def _render_merge_fields_expander(key_prefix: str = "") -> None:
    """Render Available merge fields from centralized config."""
    _render_merge_fields_table(None, key_prefix=key_prefix)


def _render_template_editor(
    templates: list[dict],
    tpl_idx: int,
    save_fn: Callable,
    default_foundation: str,
    key_prefix: str,
) -> None:
    """Full-tab editor view for a single template — shows canvas at full width."""
    tpl = templates[tpl_idx]
    fnd_id = tpl.get("foundation_id", default_foundation)
    fnd = get_foundation_by_id(fnd_id)

    # Header bar
    col_back, col_title, col_save = st.columns([1, 4, 1])
    with col_back:
        if st.button("Back", key=f"_{key_prefix}_ed_back"):
            # Clean up editor state
            cv_key = f"_{key_prefix}_ed_cv"
            for suffix in ("_order", "_edits", "_disabled"):
                st.session_state.pop(f"{cv_key}{suffix}", None)
            st.session_state.pop(f"_{key_prefix}_editing_idx", None)
            st.rerun()
    with col_title:
        fnd_label = "EOIR Pleading Paper" if fnd_id == "eoir_pleading" else "Cover Letter"
        st.markdown(f"### {_esc(tpl.get('name', 'Untitled'))}  \n"
                     f"Foundation: **{fnd_label}**")
    with col_save:
        save_clicked = st.button("Save", type="primary", key=f"_{key_prefix}_ed_save")

    # Merge the template onto its foundation
    merged = merge_template_with_foundation(tpl, fnd)
    canvas_sections = []
    disabled_ids = []
    for sec in merged:
        canvas_sections.append({
            "id": sec["id"],
            "label": sec.get("label", ""),
            "block_type": sec.get("block_type", "paragraph"),
            "content": sec.get("content", sec.get("default_content", "")),
            "default_content": sec.get("default_content", ""),
            "enabled_by_default": sec.get("enabled_by_default", True),
        })
        if not sec.get("enabled_by_default", True):
            disabled_ids.append(sec["id"])

    mf_list = [{"alias": a, "label": l, "source": s} for a, l, s in get_enabled_merge_fields()]

    cv_key = f"_{key_prefix}_ed_cv"
    canvas_result = _template_canvas_component(
        foundation_id=fnd_id,
        sections=canvas_sections,
        block_order=st.session_state.get(f"{cv_key}_order"),
        block_edits=st.session_state.get(f"{cv_key}_edits", {}),
        disabled_ids=st.session_state.get(f"{cv_key}_disabled", disabled_ids),
        merge_fields=mf_list,
        mode="page_view",
        reset=False,
        key=cv_key,
        height=800,
    )

    if canvas_result:
        if canvas_result.get("action") == "reset":
            for suffix in ("_order", "_edits", "_disabled"):
                st.session_state.pop(f"{cv_key}{suffix}", None)
            st.rerun()
        else:
            st.session_state[f"{cv_key}_order"] = canvas_result.get("block_order")
            st.session_state[f"{cv_key}_edits"] = canvas_result.get("block_edits", {})
            st.session_state[f"{cv_key}_disabled"] = canvas_result.get("disabled_ids", [])

    _render_export_buttons(
        foundation_id=fnd_id,
        canvas_sections=canvas_sections,
        order_key=f"{cv_key}_order",
        edits_key=f"{cv_key}_edits",
        disabled_key=f"{cv_key}_disabled",
        default_disabled=disabled_ids,
        key_prefix=f"{key_prefix}_ed_exp",
    )

    if save_clicked:
        edits = st.session_state.get(f"{cv_key}_edits", {})
        if edits:
            sec_map = {s["id"]: s for s in tpl.get("sections", [])}
            for sec_id, html_content in edits.items():
                if sec_id in sec_map:
                    sec_map[sec_id]["content"] = html_content
                else:
                    # Section from foundation not yet in template — add it
                    for fsec in fnd.get("sections", []):
                        if fsec["id"] == sec_id:
                            tpl.setdefault("sections", []).append({
                                "id": sec_id,
                                "label": fsec.get("label", ""),
                                "content": html_content,
                                "enabled_by_default": fsec.get("enabled_by_default", True),
                            })
                            break
        save_fn(templates)
        st.toast(f"Saved {tpl.get('name', 'template')}!")


def _render_section_based_tab(
    caption: str,
    merge_fields: list[tuple[str, str]] | None,
    get_fn: Callable[[], list[dict]],
    save_fn: Callable[[list[dict]], None],
    categories: list[str] | None,
    key_prefix: str,
    *,
    default_foundation: str = "cover_letter",
) -> None:
    """Shared UI for section-based template tabs (Court Filings, Contracts, Outcome Documents).

    Has two modes:
    - **List mode** (default): shows all templates with expanders for editing fields
    - **Editor mode**: full-tab canvas editor for a single template (enter via Edit button)
    """
    templates = get_fn()

    # Check if we're in editor mode
    editing_idx = st.session_state.get(f"_{key_prefix}_editing_idx")
    if editing_idx is not None and 0 <= editing_idx < len(templates):
        _render_template_editor(
            templates, editing_idx, save_fn, default_foundation, key_prefix,
        )
        return

    # -- List mode ----------------------------------------------------------------
    st.caption(caption)
    _render_merge_fields_table(merge_fields, key_prefix=key_prefix)

    # Add new template
    with st.expander("Add New Template"):
        new_name = st.text_input("Template Name", key=f"_{key_prefix}_new_name")
        if categories:
            new_cat = st.selectbox("Category", categories, key=f"_{key_prefix}_new_cat")
        new_fnd = st.radio(
            "Foundation",
            ["Cover Letter", "EOIR Pleading Paper"],
            horizontal=True,
            key=f"_{key_prefix}_new_fnd",
            index=0 if default_foundation == "cover_letter" else 1,
        )
        if st.button("Add Template", type="primary", key=f"_{key_prefix}_add"):
            if not new_name.strip():
                st.warning("Template name is required.")
            else:
                new_tpl: dict = {
                    "id": f"{key_prefix}_{int(time.time() * 1000)}",
                    "name": new_name.strip(),
                    "foundation_id": "cover_letter" if new_fnd == "Cover Letter" else "eoir_pleading",
                    "sections": [],
                }
                if categories:
                    new_tpl["category"] = new_cat
                templates.append(new_tpl)
                save_fn(templates)
                st.toast(f"Added template: {new_name.strip()}")
                st.rerun()

    if not templates:
        st.info("No templates yet. Add one above.")
        return

    st.markdown(f"**{len(templates)} template{'s' if len(templates) != 1 else ''}**")

    templates_to_delete: list[int] = []

    for idx, tpl in enumerate(templates):
        label = tpl.get("name", f"Template {idx + 1}")
        if categories and tpl.get("category"):
            label += f" ({tpl['category']})"
        fnd_id = tpl.get("foundation_id", default_foundation)
        fnd_short = "EOIR" if fnd_id == "eoir_pleading" else "Cover Letter"
        label += f"  [{fnd_short}]"

        with st.expander(label):
            tpl["name"] = st.text_input("Name", value=tpl.get("name", ""), key=f"_{key_prefix}_name_{idx}")
            if categories:
                cat_val = tpl.get("category", categories[-1])
                cat_idx = categories.index(cat_val) if cat_val in categories else len(categories) - 1
                tpl["category"] = st.selectbox("Category", categories, index=cat_idx, key=f"_{key_prefix}_cat_{idx}")

            # Foundation selector
            fnd_choices = ["Cover Letter", "EOIR Pleading Paper"]
            cur_fnd = tpl.get("foundation_id", default_foundation)
            fnd_idx = 0 if cur_fnd == "cover_letter" else 1
            fnd_label = st.radio(
                "Foundation",
                fnd_choices,
                horizontal=True,
                index=fnd_idx,
                key=f"_{key_prefix}_fnd_{idx}",
            )
            tpl["foundation_id"] = "cover_letter" if fnd_label == "Cover Letter" else "eoir_pleading"

            # Sections
            sections = tpl.get("sections", [])
            secs_to_delete: list[int] = []

            for si, sec in enumerate(sections):
                st.markdown(f"**Section {si + 1}:** {sec.get('label', '')}")
                sec["label"] = st.text_input("Label", value=sec.get("label", ""), key=f"_{key_prefix}_sl_{idx}_{si}")
                sec["content"] = st.text_area("Content", value=sec.get("content", ""), key=f"_{key_prefix}_sc_{idx}_{si}", height=120)
                sec["enabled_by_default"] = st.checkbox("Enabled by default", value=sec.get("enabled_by_default", True), key=f"_{key_prefix}_se_{idx}_{si}")
                if st.button("Delete Section", key=f"_{key_prefix}_sd_{idx}_{si}"):
                    secs_to_delete.append(si)
                st.divider()

            for si in sorted(secs_to_delete, reverse=True):
                sections.pop(si)

            if st.button("+ Add Section", key=f"_{key_prefix}_sa_{idx}"):
                sections.append({"id": f"sec_{int(time.time() * 1000)}", "label": "", "content": "", "enabled_by_default": True})
                st.rerun()

            tpl["sections"] = sections

            col_edit, col_delete = st.columns([1, 1])
            with col_edit:
                if st.button("Edit in Preview", key=f"_{key_prefix}_edit_{idx}"):
                    # Save current form state first, then enter editor
                    save_fn(templates)
                    st.session_state[f"_{key_prefix}_editing_idx"] = idx
                    st.rerun()
            with col_delete:
                if st.button("Delete Template", key=f"_{key_prefix}_del_{idx}"):
                    templates_to_delete.append(idx)

    if templates_to_delete:
        for idx in sorted(templates_to_delete, reverse=True):
            removed = templates.pop(idx)
            st.toast(f"Removed template: {removed.get('name', '')}")
        save_fn(templates)
        st.rerun()

    if st.button("Save", type="primary", key=f"_{key_prefix}_save"):
        save_fn(templates)
        st.toast("Templates saved!")


# -- Sidebar ------------------------------------------------------------------

with zones.A1:
    st.markdown("#### Templates")
    st.caption(
        "Manage all template types — email, letters, court filings, briefs, "
        "declarations, filing packets, contracts, checklists, outcome "
        "documents, and foundation layouts — from one place. Changes are "
        "saved to config and shared with other tools automatically."
    )


# -- Tabs ---------------------------------------------------------------------

with zones.B2:
    (tab_email, tab_letters, tab_court, tab_briefs, tab_decl,
     tab_packets, tab_contracts, tab_checklists, tab_outcomes,
     tab_merge, tab_foundations) = st.tabs([
        "Email",
        "Letters",
        "Court Filings",
        "Legal Briefs",
        "Declarations",
        "Filing Packets",
        "Contracts",
        "Checklists",
        "Outcome Documents",
        "Merge Fields",
        "Foundations",
    ])


# =============================================================================
# Tab 1: Email
# =============================================================================

def _render_email_templates() -> None:
    st.caption(
        "Create and edit email templates. Use {field_name} placeholders that will "
        "be filled with client data when composing. Templates are available in the "
        "Email button on every tool."
    )

    _render_merge_fields_expander("et")

    templates = get_email_templates()

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
# Tab 2: Letters
# =============================================================================

def _render_client_letter_templates() -> None:
    st.caption(
        "Templates for letters addressed to the client — appointment letters, "
        "status updates, document requests. Use {field_name} placeholders for "
        "merge fields."
    )

    _render_merge_fields_expander("cl")

    templates = get_client_letter_templates()

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

    if st.button("Save Letter Templates", type="primary", key="_cl_save"):
        save_client_letter_templates(templates)
        st.toast("Letter templates saved!")


with tab_letters:
    _render_client_letter_templates()


# =============================================================================
# Tab 3: Court Filings (section-based — replaces old EOIR Templates)
# =============================================================================

with tab_court:
    _render_section_based_tab(
        caption=(
            "Templates for court filings — motions, notices, certificates of "
            "service, and other EOIR documents. Each template has toggleable "
            "sections with merge field placeholders."
        ),
        merge_fields=None,
        get_fn=get_court_filing_templates,
        save_fn=save_court_filing_templates,
        categories=COURT_FILING_CATEGORIES,
        key_prefix="cf",
        default_foundation="eoir_pleading",
    )


# =============================================================================
# Tab 4: Legal Briefs
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

    # Detect brief type change -> reset canvas
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


with tab_briefs:
    _render_brief_sections()


# =============================================================================
# Tab 5: Declarations (question-based sections)
# =============================================================================

def _render_declaration_templates() -> None:
    st.caption(
        "Templates for declarations — each has sections with guided questions "
        "and tips for attorneys. Used by the Declaration Drafter tool."
    )
    _render_merge_fields_expander("dt")

    templates = get_declaration_templates()

    # Add new template
    with st.expander("Add New Declaration Template"):
        new_name = st.text_input("Template Name", key="_dt_new_name", placeholder="e.g. Bond Declaration")
        if st.button("Add Template", type="primary", key="_dt_add"):
            if not new_name.strip():
                st.warning("Template name is required.")
            else:
                templates.append({
                    "id": f"decl_{int(time.time() * 1000)}",
                    "name": new_name.strip(),
                    "sections": [],
                })
                save_declaration_templates(templates)
                st.toast(f"Added template: {new_name.strip()}")
                st.rerun()

    if not templates:
        st.info("No declaration templates yet. Add one above.")
        return

    st.markdown(f"**{len(templates)} template{'s' if len(templates) != 1 else ''}**")

    templates_to_delete: list[int] = []

    for idx, tpl in enumerate(templates):
        with st.expander(tpl.get("name", f"Template {idx + 1}")):
            tpl["name"] = st.text_input("Name", value=tpl.get("name", ""), key=f"_dt_name_{idx}")

            sections = tpl.get("sections", [])
            secs_to_delete: list[int] = []

            for si, sec in enumerate(sections):
                st.markdown(f"---\n**Section: {sec.get('title', '')}**")
                sec["title"] = st.text_input("Section Title", value=sec.get("title", ""), key=f"_dt_st_{idx}_{si}")
                sec["instructions"] = st.text_area("Instructions", value=sec.get("instructions", ""), key=f"_dt_si_{idx}_{si}", height=80)

                # Questions
                questions = sec.get("questions", [])
                qs_to_delete: list[int] = []

                for qi, q in enumerate(questions):
                    c1, c2 = st.columns([8, 1])
                    with c1:
                        q["label"] = st.text_input("Question", value=q.get("label", ""), key=f"_dt_ql_{idx}_{si}_{qi}")
                        q["tip"] = st.text_input("Tip", value=q.get("tip", ""), key=f"_dt_qt_{idx}_{si}_{qi}")
                    with c2:
                        st.markdown("<br><br>", unsafe_allow_html=True)
                        if st.button("X", key=f"_dt_qd_{idx}_{si}_{qi}"):
                            qs_to_delete.append(qi)

                for qi in sorted(qs_to_delete, reverse=True):
                    questions.pop(qi)

                if st.button("+ Add Question", key=f"_dt_qa_{idx}_{si}"):
                    questions.append({"id": f"q_{int(time.time() * 1000)}", "label": "", "tip": ""})
                    st.rerun()

                sec["questions"] = questions

                if st.button("Delete Section", key=f"_dt_sd_{idx}_{si}"):
                    secs_to_delete.append(si)

            for si in sorted(secs_to_delete, reverse=True):
                sections.pop(si)

            if st.button("+ Add Section", key=f"_dt_sa_{idx}"):
                sections.append({"id": f"sec_{int(time.time() * 1000)}", "title": "", "instructions": "", "questions": []})
                st.rerun()

            tpl["sections"] = sections

            if st.button("Delete Template", key=f"_dt_del_{idx}"):
                templates_to_delete.append(idx)

    if templates_to_delete:
        for idx in sorted(templates_to_delete, reverse=True):
            removed = templates.pop(idx)
            st.toast(f"Removed template: {removed.get('name', '')}")
        save_declaration_templates(templates)
        st.rerun()

    if st.button("Save Declaration Templates", type="primary", key="_dt_save"):
        save_declaration_templates(templates)
        st.toast("Declaration templates saved!")


with tab_decl:
    _render_declaration_templates()


# =============================================================================
# Tab 6: Filing Packets (was Government Cover Letters)
# =============================================================================

def _render_govt_letter_templates() -> None:
    st.caption(
        "Templates for government cover letters used by the Filing Assembler tool. "
        "Each case type has standard enclosed documents, purpose and closing paragraphs."
    )
    _render_merge_fields_expander("govt")

    templates = get_govt_letter_templates()
    case_types = list(templates.keys())

    # Add new case type
    with st.expander("Add New Case Type"):
        new_ct_name = st.text_input("Case Type Name", key="_govt_new_ct", placeholder="e.g. Humanitarian Parole")
        if st.button("Add Case Type", type="primary", key="_govt_add_ct"):
            if not new_ct_name.strip():
                st.warning("Case type name is required.")
            elif new_ct_name.strip() in templates:
                st.warning("Case type already exists.")
            else:
                templates[new_ct_name.strip()] = {
                    "form_numbers": [],
                    "filing_offices": [],
                    "standard_enclosed_docs": [],
                    "purpose_paragraph": "",
                    "closing_paragraph": "",
                }
                save_govt_letter_templates(templates)
                st.toast(f"Added case type: {new_ct_name.strip()}")
                st.rerun()

    if not case_types:
        st.info("No government cover letter templates found. Add one above.")
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

    if st.button("Save Filing Packet Templates", type="primary", key="_govt_save"):
        tpl["form_numbers"] = [f.strip() for f in form_nums_str.split(",") if f.strip()]
        tpl["filing_offices"] = [o.strip() for o in offices_str.strip().splitlines() if o.strip()]
        tpl["standard_enclosed_docs"] = [d.strip() for d in docs_str.strip().splitlines() if d.strip()]
        tpl["purpose_paragraph"] = purpose
        tpl["closing_paragraph"] = closing
        templates[selected_case_type] = tpl
        save_govt_letter_templates(templates)
        st.toast(f"Saved {selected_case_type} template!")


with tab_packets:
    _render_govt_letter_templates()


# =============================================================================
# Tab 7: Contracts (section-based)
# =============================================================================

with tab_contracts:
    _render_section_based_tab(
        caption=(
            "Templates for retainer agreements, flat fee agreements, and "
            "limited scope engagements. Each has toggleable sections."
        ),
        merge_fields=None,
        get_fn=get_contract_templates,
        save_fn=save_contract_templates,
        categories=None,
        key_prefix="ct",
    )


# =============================================================================
# Tab 8: Checklists (case-type task lists)
# =============================================================================

def _render_checklist_templates() -> None:
    st.caption(
        "Templates for case checklists — each case type has a list of tasks "
        "organized by category. Used by the Case Checklist tool."
    )

    templates = get_checklist_templates()
    case_types = list(templates.keys())

    if not case_types:
        st.info("No checklist templates found.")
        return

    selected_type = st.selectbox("Case Type", case_types, key="_ck_case_type")
    tasks = templates.get(selected_type, [])

    # Group by category
    for cat in CHECKLIST_CATEGORIES:
        cat_tasks = [t for t in tasks if t.get("category") == cat]
        with st.expander(f"{cat} ({len(cat_tasks)} tasks)", expanded=False):
            tasks_to_delete: list[int] = []
            for ti, task in enumerate(cat_tasks):
                # Find global index
                global_idx = tasks.index(task)
                c1, c2 = st.columns([8, 1])
                with c1:
                    new_title = st.text_input(
                        "Task",
                        value=task.get("title", ""),
                        key=f"_ck_t_{selected_type}_{cat}_{ti}",
                        label_visibility="collapsed",
                    )
                    task["title"] = new_title
                with c2:
                    if st.button("X", key=f"_ck_td_{selected_type}_{cat}_{ti}"):
                        tasks_to_delete.append(global_idx)

            if tasks_to_delete:
                for gi in sorted(tasks_to_delete, reverse=True):
                    tasks.pop(gi)
                templates[selected_type] = tasks
                save_checklist_templates(templates)
                st.rerun()

            # Add task to this category
            if st.button(f"+ Add {cat} Task", key=f"_ck_ta_{selected_type}_{cat}"):
                tasks.append({"title": "", "category": cat})
                templates[selected_type] = tasks
                save_checklist_templates(templates)
                st.rerun()

    # Add new case type
    st.divider()
    c1, c2 = st.columns([4, 1])
    with c1:
        new_ct = st.text_input("New Case Type", key="_ck_new_ct", placeholder="e.g. Humanitarian Parole")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", key="_ck_add_ct") and new_ct.strip():
            if new_ct.strip() not in templates:
                templates[new_ct.strip()] = []
                save_checklist_templates(templates)
                st.toast(f"Added case type: {new_ct.strip()}")
                st.rerun()

    if st.button("Save Checklist Templates", type="primary", key="_ck_save"):
        templates[selected_type] = tasks
        save_checklist_templates(templates)
        st.toast("Checklist templates saved!")


with tab_checklists:
    _render_checklist_templates()


# =============================================================================
# Tab 9: Outcome Documents (section-based)
# =============================================================================

with tab_outcomes:
    _render_section_based_tab(
        caption=(
            "Templates for post-decision documents — approval letters, RFE "
            "response covers, and denial appeal covers. Each has toggleable "
            "sections with merge field placeholders."
        ),
        merge_fields=None,
        get_fn=get_outcome_templates,
        save_fn=save_outcome_templates,
        categories=None,
        key_prefix="od",
    )


# =============================================================================
# Tab 10: Merge Fields
# =============================================================================

def _render_merge_fields_tab() -> None:
    """Manage which Salesforce fields are available as merge fields."""
    st.caption(
        "Manage which Salesforce fields are available as merge fields "
        "across all template tabs. Enable fields, set aliases, and "
        "they\u2019ll appear in the \u201cAvailable merge fields\u201d "
        "reference table on every tab."
    )

    # Refresh All button
    if st.button("Refresh All from Salesforce", key="_mf_refresh_all"):
        try:
            results = refresh_all_field_caches()
            summary = ", ".join(f"{label}: {cnt}" for label, cnt in results.items())
            st.toast(f"Refreshed all objects ({summary})")
            st.rerun()
        except Exception as exc:
            st.error(f"Failed to refresh: {exc}")

    # Duplicate alias warning
    dupes = find_duplicate_aliases()
    if dupes:
        lines = []
        for alias, locs in dupes.items():
            lines.append(f"- **{{{alias}}}** used by: {', '.join(locs)}")
        st.warning(
            "**Duplicate aliases detected** — these will conflict during "
            "template resolution. Rename one of each pair:\n\n"
            + "\n".join(lines)
        )

    config = get_merge_field_config()

    # Build subtab labels with enabled counts
    tab_labels = []
    for obj in MANAGED_OBJECTS:
        count = len(config.get(obj["api_name"], []))
        tab_labels.append(f"{obj['tab_label']} ({count})")

    sub_tabs = st.tabs(tab_labels)

    for obj_def, sub_tab in zip(MANAGED_OBJECTS, sub_tabs):
        with sub_tab:
            _render_object_subtab(obj_def, config)


def _render_object_subtab(obj_def: dict, config: dict) -> None:
    """Render one SF object subtab inside the Merge Fields tab."""
    api_name = obj_def["api_name"]
    tab_label = obj_def["tab_label"]

    # Refresh button
    col_r, col_ts = st.columns([1, 3])
    with col_r:
        if st.button("Refresh from Salesforce", key=f"_mf_refresh_{api_name}"):
            try:
                fields = refresh_field_cache(api_name)
                st.toast(f"Loaded {len(fields)} fields from {tab_label}")
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to refresh: {exc}")
    with col_ts:
        ts = config.get("_cache_timestamp")
        if ts:
            st.caption(f"Last refresh: {ts[:19].replace('T', ' ')} UTC")
        else:
            st.caption("Not yet refreshed from Salesforce")

    cached_fields = get_field_cache(api_name)
    enabled_fields: list[dict] = config.get(api_name, [])
    enabled_map = {f["sf_api_name"]: f for f in enabled_fields}
    enabled_api_names = set(enabled_map.keys())

    if not cached_fields:
        # Show only enabled (default) fields if no cache
        st.info(
            "Click \u201cRefresh from Salesforce\u201d to load all available "
            "fields. Currently showing only pre-enabled defaults."
        )
        _render_enabled_fields_editor(api_name, enabled_fields, config)
        return

    # Filters
    col_search, col_filter = st.columns([3, 1])
    with col_search:
        search = st.text_input(
            "Search fields", key=f"_mf_search_{api_name}",
            placeholder="Filter by name or label...",
        )
    with col_filter:
        show_enabled_only = st.checkbox(
            "Show only enabled", key=f"_mf_enabled_only_{api_name}",
        )

    # Build display list
    filtered = cached_fields
    if search:
        q = search.lower()
        filtered = [
            f for f in filtered
            if q in f["name"].lower() or q in f["label"].lower()
        ]
    if show_enabled_only:
        filtered = [f for f in filtered if f["name"] in enabled_api_names]

    st.markdown(f"**{len(filtered)}** fields shown \u00b7 **{len(enabled_fields)}** enabled")

    # Track which enabled fields appear in the filtered view so we can
    # preserve fields that are NOT visible (filtered out / scrolled past).
    visible_api_names: set[str] = set()
    new_enabled_from_view: list[dict] = []

    for sf_field in filtered:
        fname = sf_field["name"]
        flabel = sf_field["label"]
        ftype = sf_field.get("type", "")
        is_enabled = fname in enabled_api_names
        existing = enabled_map.get(fname)
        visible_api_names.add(fname)

        # Use SF API name in widget key for stable identity across refreshes
        safe_key = fname.replace(".", "_")

        col_toggle, col_info, col_alias, col_desc = st.columns([0.5, 2.5, 2, 3])

        with col_toggle:
            new_val = st.checkbox(
                "on", value=is_enabled, label_visibility="collapsed",
                key=f"_mf_tog_{api_name}_{safe_key}",
            )
        with col_info:
            if is_enabled and existing:
                st.markdown(f"**{flabel}**  \n`{fname}` \u00b7 {ftype} \u00b7 use as `{{{existing['alias']}}}`")
            else:
                st.markdown(f"**{flabel}**  \n`{fname}` \u00b7 {ftype}")

        if new_val:
            default_alias = existing["alias"] if existing else fname.lower().rstrip("__c").replace("__", "_")
            default_label = existing["label"] if existing else flabel

            with col_alias:
                alias = st.text_input(
                    "Alias", value=default_alias,
                    key=f"_mf_alias_{api_name}_{safe_key}",
                    label_visibility="collapsed",
                    placeholder="placeholder_name",
                    help=f"Use as {{{default_alias}}} in templates",
                )
            with col_desc:
                label = st.text_input(
                    "Description", value=default_label,
                    key=f"_mf_desc_{api_name}_{safe_key}",
                    label_visibility="collapsed",
                    placeholder="Description",
                )

            new_enabled_from_view.append({
                "sf_api_name": fname,
                "alias": alias,
                "label": label,
                "type": ftype,
            })

    # Merge: keep enabled fields that weren't visible (not affected by
    # current search/filter), plus the fields from the visible view.
    merged: list[dict] = [
        f for f in enabled_fields if f["sf_api_name"] not in visible_api_names
    ]
    merged.extend(new_enabled_from_view)

    if st.button("Save", type="primary", key=f"_mf_save_{api_name}"):
        config[api_name] = merged
        save_merge_field_config(config)
        st.toast(f"Saved {len(merged)} {tab_label} merge fields!")


def _render_enabled_fields_editor(
    api_name: str, enabled_fields: list[dict], config: dict,
) -> None:
    """Simplified editor when no SF cache exists — edit enabled defaults only."""
    if not enabled_fields:
        st.info("No fields enabled. Refresh from Salesforce to see available fields.")
        return

    st.markdown(f"**{len(enabled_fields)} enabled fields**")

    fields_to_remove: list[int] = []
    for fi, field in enumerate(enabled_fields):
        col_x, col_api, col_alias, col_desc = st.columns([0.5, 2.5, 2, 3])
        with col_x:
            if st.button("X", key=f"_mf_rm_{api_name}_{fi}"):
                fields_to_remove.append(fi)
        with col_api:
            st.markdown(f"`{field['sf_api_name']}` \u00b7 {field.get('type', '')} \u00b7 use as `{{{field['alias']}}}`")
        with col_alias:
            field["alias"] = st.text_input(
                "Alias", value=field["alias"],
                key=f"_mf_ea_{api_name}_{fi}",
                label_visibility="collapsed",
            )
        with col_desc:
            field["label"] = st.text_input(
                "Desc", value=field["label"],
                key=f"_mf_ed_{api_name}_{fi}",
                label_visibility="collapsed",
            )

    for fi in sorted(fields_to_remove, reverse=True):
        enabled_fields.pop(fi)

    if st.button("Save", type="primary", key=f"_mf_save_{api_name}"):
        config[api_name] = enabled_fields
        save_merge_field_config(config)
        st.toast("Saved!")


with tab_merge:
    _render_merge_fields_tab()


# =============================================================================
# Tab 11: Foundations
# =============================================================================

def _render_foundations_tab() -> None:
    """Edit foundation layout templates (Cover Letter / EOIR Pleading Paper)."""
    st.caption(
        "Foundation templates define the structural layout for documents. "
        "Each foundation has a set of sections (letterhead, date, recipient, body, "
        "signature, etc.) that individual templates inherit and override."
    )

    # Foundation selector
    foundation_choice = st.radio(
        "Foundation",
        ["Cover Letter", "EOIR Pleading Paper"],
        horizontal=True,
        key="_fnd_choice",
    )
    foundation_id = "cover_letter" if foundation_choice == "Cover Letter" else "eoir_pleading"
    foundation = get_foundation_by_id(foundation_id)

    # Detect foundation change for canvas reset
    prev_fnd = st.session_state.get("_fnd_prev_id")
    fnd_changed = prev_fnd != foundation_id
    if fnd_changed:
        st.session_state["_fnd_prev_id"] = foundation_id
        st.session_state.pop("_fnd_canvas_order", None)
        st.session_state.pop("_fnd_canvas_edits", None)
        st.session_state.pop("_fnd_disabled_ids", None)

    # -- Section list (collapsible) ----------------------------------------------
    with st.expander("Sections", expanded=True):
        sections = foundation.get("sections", [])
        secs_to_delete: list[int] = []

        for si, sec in enumerate(sections):
            with st.expander(f"{si + 1}. {sec.get('label', 'Untitled')}", expanded=False):
                sec["label"] = st.text_input(
                    "Label", value=sec.get("label", ""),
                    key=f"_fnd_sl_{foundation_id}_{si}",
                )
                sec["block_type"] = st.text_input(
                    "Block Type", value=sec.get("block_type", "paragraph"),
                    key=f"_fnd_bt_{foundation_id}_{si}",
                )
                sec["enabled_by_default"] = st.checkbox(
                    "Enabled by default",
                    value=sec.get("enabled_by_default", True),
                    key=f"_fnd_en_{foundation_id}_{si}",
                )
                sec["default_content"] = st.text_area(
                    "Default Content (HTML)",
                    value=sec.get("default_content", ""),
                    key=f"_fnd_dc_{foundation_id}_{si}",
                    height=100,
                )
                if st.button("Delete Section", key=f"_fnd_sd_{foundation_id}_{si}"):
                    secs_to_delete.append(si)

        for si in sorted(secs_to_delete, reverse=True):
            sections.pop(si)

        col_add, col_save = st.columns([1, 1])
        with col_add:
            if st.button("+ Add Section", key=f"_fnd_sa_{foundation_id}"):
                sections.append({
                    "id": f"sec_{int(time.time() * 1000)}",
                    "label": "New Section",
                    "block_type": "paragraph",
                    "default_content": "",
                    "enabled_by_default": True,
                })
                st.rerun()
        with col_save:
            if st.button("Save Foundation", type="primary", key=f"_fnd_save_{foundation_id}"):
                foundation["sections"] = sections
                save_foundation(foundation)
                st.toast(f"Saved {foundation['name']} foundation!")

        foundation["sections"] = sections

    # -- Full-width preview editor below ----------------------------------------
    st.markdown("**Preview Editor** — click any section to edit with rich text")

    canvas_sections = []
    disabled_ids = []
    for sec in foundation.get("sections", []):
        canvas_sections.append({
            "id": sec["id"],
            "label": sec.get("label", ""),
            "block_type": sec.get("block_type", "paragraph"),
            "content": sec.get("default_content", ""),
            "default_content": sec.get("default_content", ""),
            "enabled_by_default": sec.get("enabled_by_default", True),
        })
        if not sec.get("enabled_by_default", True):
            disabled_ids.append(sec["id"])

    mf_list = []
    for alias, label, source in get_enabled_merge_fields():
        mf_list.append({"alias": alias, "label": label, "source": source})

    canvas_result = _template_canvas_component(
        foundation_id=foundation_id,
        sections=canvas_sections,
        block_order=st.session_state.get("_fnd_canvas_order"),
        block_edits=st.session_state.get("_fnd_canvas_edits", {}),
        disabled_ids=st.session_state.get("_fnd_disabled_ids", disabled_ids),
        merge_fields=mf_list,
        mode="page_view",
        reset=fnd_changed,
        _foundation_changed=fnd_changed,
        key=f"_fnd_canvas_{foundation_id}",
        height=800,
    )

    if canvas_result:
        if canvas_result.get("action") == "reset":
            st.session_state.pop("_fnd_canvas_order", None)
            st.session_state.pop("_fnd_canvas_edits", None)
            st.session_state.pop("_fnd_disabled_ids", None)
            st.rerun()
        else:
            st.session_state["_fnd_canvas_order"] = canvas_result.get("block_order")
            st.session_state["_fnd_canvas_edits"] = canvas_result.get("block_edits", {})
            st.session_state["_fnd_disabled_ids"] = canvas_result.get("disabled_ids", [])

    _render_export_buttons(
        foundation_id=foundation_id,
        canvas_sections=canvas_sections,
        order_key="_fnd_canvas_order",
        edits_key="_fnd_canvas_edits",
        disabled_key="_fnd_disabled_ids",
        default_disabled=disabled_ids,
        key_prefix="fnd_exp",
    )

    # Save canvas edits back to the foundation
    if st.button("Save Preview Edits to Foundation", type="primary", key=f"_fnd_cv_save_{foundation_id}"):
        edits = st.session_state.get("_fnd_canvas_edits", {})
        if edits:
            sec_map = {s["id"]: s for s in foundation.get("sections", [])}
            for sec_id, html_content in edits.items():
                if sec_id in sec_map:
                    sec_map[sec_id]["default_content"] = html_content
            save_foundation(foundation)
            st.session_state.pop("_fnd_canvas_edits", None)
            st.toast(f"Saved preview edits to {foundation['name']}!")
            st.rerun()
        else:
            st.toast("No edits to save.")


with tab_foundations:
    _render_foundations_tab()
