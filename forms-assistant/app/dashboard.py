"""Forms Assistant -- Streamlit dashboard.

Tabbed orchestrator for the form ingestion, mapping, data-entry, and sync
subsystems.  Each tab is implemented as a module under ``app/tab_*.py``.

Backward compatible: all 16 hardcoded USCIS forms work with zero migration.
"""

from __future__ import annotations

import html as html_mod
import sys
from pathlib import Path

import streamlit as st

from app.form_definitions import (
    SUPPORTED_FORMS,
    check_completeness,
    delete_form_draft,
    get_fields_for_form,
    list_form_drafts,
    load_form_draft,
    new_draft_id,
    save_form_draft,
    validate_field,
)
from app.pdf_form_store import (
    get_all_forms,
    get_all_fields,
    is_uploaded_form,
    get_field_roles,
    get_field_sf_mappings,
)

# Tab modules
from app.tab_fill import render_fill_tab
from app.tab_ingest import render_ingest_tab
from app.tab_mappings import render_mappings_tab
from app.tab_sync import render_sync_tab

# Shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.client_banner import render_client_banner
from shared.config_store import get_config_value, set_config_value
from shared.tool_notes import render_tool_notes

try:
    from shared.tool_help import render_tool_help
except ImportError:
    render_tool_help = None
try:
    from shared.feedback_button import render_feedback_button
except ImportError:
    render_feedback_button = None
try:
    from shared.box_folder_browser import render_box_folder_browser
    from shared.box_client import parse_folder_id as _parse_folder_id
except ImportError:
    render_box_folder_browser = None
    _parse_folder_id = None

# -- Page config --------------------------------------------------------------

st.set_page_config(
    page_title="Forms Assistant -- O'Brien Immigration Law",
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

/* Section header */
.section-header {
    font-size: 1.1rem;
    font-weight: 600;
    color: #1a2744;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
}

/* Form metadata */
.form-meta {
    font-size: 0.85rem;
    color: #5a6a85;
    line-height: 1.6;
}

/* Field error */
.field-error {
    font-size: 0.82rem;
    color: #c62828;
    margin-top: -8px;
    margin-bottom: 8px;
}

/* Progress bar */
.progress-bar {
    background: #e8ecf0;
    border-radius: 6px;
    height: 10px;
    overflow: hidden;
    margin-bottom: 4px;
}
.progress-fill {
    height: 100%;
    background: #1a73e8;
    border-radius: 6px;
    transition: width 0.3s ease;
}

/* Preview panel */
.preview-panel {
    font-family: 'Inter', sans-serif;
    font-size: 0.82rem;
    line-height: 1.7;
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 20px 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    max-height: 75vh;
    overflow-y: auto;
}
.preview-panel .pv-section {
    font-weight: 700;
    font-size: 0.85rem;
    color: #1a2744;
    margin-top: 14px;
    margin-bottom: 6px;
    border-bottom: 1px solid #e8ecf0;
    padding-bottom: 3px;
}
.preview-panel .pv-field {
    display: flex;
    gap: 8px;
    padding: 2px 0;
}
.preview-panel .pv-label {
    font-weight: 600;
    color: #5a6a85;
    min-width: 160px;
    flex-shrink: 0;
}
.preview-panel .pv-value {
    color: #1a2744;
}
.preview-panel .pv-empty {
    color: #b0b8c4;
    font-style: italic;
}

/* Saved toast */
.saved-toast {
    font-size: 0.8rem;
    color: #2e7d32;
    font-weight: 600;
}

/* Help text below fields */
.help-text {
    font-size: 0.78rem;
    color: #86868b;
    margin-top: -6px;
    margin-bottom: 10px;
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
    <div class="nav-title">Forms Assistant<span class="nav-firm">&mdash; O'Brien Immigration Law</span></div>
    <div class="nav-spacer"></div>
</div>
""",
    unsafe_allow_html=True,
)
render_logout()

render_client_banner()
if render_tool_help:
    render_tool_help("forms-assistant")
if render_feedback_button:
    render_feedback_button("forms-assistant")

# -- Session state defaults ---------------------------------------------------

_DEFAULTS: dict = {
    "draft_id": None,
    "last_saved_msg": "",
    "form_data": {},
    "current_section": 0,
    "validation_errors": {},
    "selected_forms": [],
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

if st.session_state.draft_id is None:
    st.session_state.draft_id = new_draft_id()


# -- Helpers ------------------------------------------------------------------


def _do_save(form_id: str) -> None:
    """Save the current form data as a draft."""
    selected_forms = st.session_state.get("selected_forms", [])
    save_form_draft(
        st.session_state.draft_id,
        form_id,
        dict(st.session_state.form_data),
        st.session_state.current_section,
        form_ids=selected_forms if len(selected_forms) > 1 else None,
    )
    name = ""
    for key in ("full_name", "applicant_name", "petitioner_name", "appellant_name"):
        if st.session_state.form_data.get(key, "").strip():
            name = st.session_state.form_data[key].strip()
            break
    st.session_state.last_saved_msg = f"Saved -- {name or 'draft'}"


def _do_load(draft_id: str) -> None:
    """Load a draft into session state."""
    draft = load_form_draft(draft_id)
    if not draft:
        return
    st.session_state.draft_id = draft["id"]
    st.session_state.form_data = dict(draft.get("form_data", {}))
    st.session_state.current_section = draft.get("current_section", 0)
    st.session_state.validation_errors = {}
    st.session_state.last_saved_msg = ""
    st.session_state._loaded_form_id = draft.get("form_id", "I-589")
    # Restore multi-form selection if present
    if draft.get("form_ids"):
        st.session_state.selected_forms = list(draft["form_ids"])
    else:
        st.session_state.selected_forms = [draft.get("form_id", "I-589")]


def _do_new() -> None:
    """Start a fresh form."""
    st.session_state.draft_id = new_draft_id()
    st.session_state.last_saved_msg = ""
    st.session_state.form_data = {}
    st.session_state.current_section = 0
    st.session_state.validation_errors = {}
    if "_loaded_form_id" in st.session_state:
        del st.session_state["_loaded_form_id"]


def _auto_save(form_id: str) -> None:
    """Silently persist current form data as a draft."""
    selected_forms = st.session_state.get("selected_forms", [])
    save_form_draft(
        st.session_state.draft_id,
        form_id,
        dict(st.session_state.form_data),
        st.session_state.current_section,
        form_ids=selected_forms if len(selected_forms) > 1 else None,
    )


# -- Auto-load most recent draft on startup ----------------------------------

if not st.session_state.form_data:
    saved_drafts = list_form_drafts()
    if saved_drafts:
        _do_load(saved_drafts[0]["id"])


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

    saved_drafts = list_form_drafts()
    if saved_drafts:
        labels_map = {
            d["id"]: f"{d['client_name']} -- {d['form_id']}"
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
                delete_form_draft(selected_draft)
                st.rerun()

    if st.session_state.last_saved_msg:
        st.markdown(
            f'<div class="saved-toast">{html_mod.escape(st.session_state.last_saved_msg)}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # Form selector -- multi-select for unified data entry
    all_forms = get_all_forms()
    form_ids = list(all_forms.keys())
    form_labels = {}
    for fid, meta in all_forms.items():
        badge = " (PDF)" if meta.get("_uploaded") else ""
        form_labels[fid] = f"{fid}{badge} -- {meta.get('title', '')}"

    # Read disk-persisted selection as fallback
    persisted_selection = get_config_value("forms-assistant", "last_selected_forms", [])

    # If a draft was just loaded, use its form_id as default
    default_selection = st.session_state.get("selected_forms", [])
    if "_loaded_form_id" in st.session_state and not default_selection:
        loaded_fid = st.session_state._loaded_form_id
        if loaded_fid in form_ids:
            default_selection = [loaded_fid]

    # Fall back to disk-persisted selection
    if not default_selection:
        default_selection = persisted_selection

    if not default_selection:
        default_selection = [form_ids[0]] if form_ids else []

    # Ensure default selections are valid
    default_selection = [f for f in default_selection if f in form_ids]
    if not default_selection and form_ids:
        default_selection = [form_ids[0]]

    selected_forms = st.multiselect(
        "Forms",
        options=form_ids,
        default=default_selection,
        format_func=lambda x: form_labels.get(x, x),
        key="inp_form_selector",
    )
    st.session_state.selected_forms = selected_forms

    # Persist selection to disk when it changes
    if selected_forms != persisted_selection:
        set_config_value("forms-assistant", "last_selected_forms", selected_forms)

    # Show metadata for primary form
    primary_form = selected_forms[0] if selected_forms else None
    if primary_form:
        form_meta = all_forms.get(primary_form, {})
        st.markdown(
            f'<div class="form-meta">'
            f'<strong>Filing Fee:</strong> {html_mod.escape(form_meta.get("filing_fee", "N/A"))}<br>'
            f'<strong>Processing:</strong> {html_mod.escape(form_meta.get("processing_time", "N/A"))}<br>'
            f'<strong>Agency:</strong> {html_mod.escape(form_meta.get("agency", "N/A"))}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Auto-fill sections for uploaded forms
    if primary_form and is_uploaded_form(primary_form):
        roles = get_field_roles(primary_form)
        sf_mappings = get_field_sf_mappings(primary_form)

        has_attorney_roles = any(r.startswith("attorney_") for r in roles.values())
        has_preparer_roles = any(r.startswith("preparer_") for r in roles.values())

        # Client auto-fill from SF
        if sf_mappings:
            sf_client = st.session_state.get("sf_client")
            if sf_client:
                filled = 0
                for field_name, sf_key in sf_mappings.items():
                    if sf_client.get(sf_key) and not st.session_state.form_data.get(field_name):
                        st.session_state.form_data[field_name] = str(sf_client[sf_key])
                        filled += 1
                if filled:
                    st.divider()
                    st.caption(f"Auto-filled {filled} field(s) from Salesforce")

            # Sidebar SF sync button
            st.divider()
            st.markdown("#### Salesforce Sync")
            if sf_client:
                changed: dict[str, str] = {}
                for field_name, sf_key in sf_mappings.items():
                    form_val = str(st.session_state.form_data.get(field_name, "")).strip()
                    sf_val = str(sf_client.get(sf_key, "")).strip()
                    if form_val and form_val != sf_val:
                        changed[sf_key] = form_val
                if changed:
                    st.caption(f"{len(changed)} field(s) differ from Salesforce")
                    if st.button("Sync to Salesforce", type="primary", use_container_width=True, key="btn_sf_sync"):
                        try:
                            from shared.salesforce_client import update_client
                            sf_id = sf_client.get("Id")
                            if sf_id:
                                update_client(sf_id, changed)
                                for sf_key, val in changed.items():
                                    sf_client[sf_key] = val
                                st.toast(f"Pushed {len(changed)} field(s) to Salesforce")
                                st.rerun()
                            else:
                                st.error("No Salesforce record ID found.")
                        except Exception as e:
                            st.error(f"Sync failed: {e}")
                else:
                    st.caption("All mapped fields match Salesforce")
            else:
                st.caption("Pull a client to enable Salesforce sync.")

        # Attorney picklist
        if has_attorney_roles:
            st.divider()
            st.markdown("#### Attorney")
            try:
                from shared.attorney_store import load_attorneys
                attorneys = load_attorneys()
            except ImportError:
                attorneys = []
            if attorneys:
                atty_options = ["(None)"] + [a["name"] for a in attorneys]
                atty_sel = st.selectbox(
                    "Select attorney",
                    atty_options,
                    key="inp_attorney",
                    label_visibility="collapsed",
                )
                if atty_sel != "(None)":
                    atty = next((a for a in attorneys if a["name"] == atty_sel), None)
                    if atty:
                        role_to_atty_key = {
                            "attorney_name": "name",
                            "attorney_bar_number": "bar_number",
                            "attorney_firm": "firm",
                            "attorney_address": "address",
                            "attorney_phone": "phone",
                            "attorney_email": "email",
                        }
                        for field_name, role in roles.items():
                            atty_key = role_to_atty_key.get(role)
                            if atty_key and atty.get(atty_key):
                                st.session_state.form_data[field_name] = atty[atty_key]
            else:
                st.caption("No attorneys configured. Add them in Admin Panel.")

        # Preparer picklist
        if has_preparer_roles:
            st.divider()
            st.markdown("#### Preparer")
            try:
                from shared.preparer_store import load_preparers
                preparers = load_preparers()
            except ImportError:
                preparers = []
            if preparers:
                prep_options = ["(None)"] + [p["name"] for p in preparers]
                prep_sel = st.selectbox(
                    "Select preparer",
                    prep_options,
                    key="inp_preparer",
                    label_visibility="collapsed",
                )
                if prep_sel != "(None)":
                    prep = next((p for p in preparers if p["name"] == prep_sel), None)
                    if prep:
                        role_to_prep_key = {
                            "preparer_name": "name",
                            "preparer_firm": "firm",
                            "preparer_address": "address",
                            "preparer_phone": "phone",
                            "preparer_email": "email",
                            "preparer_bar_number": "bar_number",
                        }
                        for field_name, role in roles.items():
                            prep_key = role_to_prep_key.get(role)
                            if prep_key and prep.get(prep_key):
                                st.session_state.form_data[field_name] = prep[prep_key]
            else:
                st.caption("No preparers configured. Add them in Admin Panel.")

    st.divider()

    # Progress bar
    if primary_form:
        st.markdown("#### Progress")
        fields_dict = get_all_fields(primary_form)
        all_defined_fields = [f for section_fields in fields_dict.values() for f in section_fields]
        total_fields = len(all_defined_fields)
        filled_count = sum(
            1 for f in all_defined_fields
            if str(st.session_state.form_data.get(f.name, "")).strip()
        )
        pct = round((filled_count / total_fields) * 100) if total_fields > 0 else 0

        st.markdown(
            f'<div class="progress-bar"><div class="progress-fill" style="width:{pct}%"></div></div>',
            unsafe_allow_html=True,
        )
        st.caption(f"{pct}% complete ({filled_count}/{total_fields} fields)")

    st.divider()

    # Validate button
    validate_clicked = st.button("Validate Form", use_container_width=True)

    # -- Client Documents (Box folder browser) --------------------------------
    if render_box_folder_browser and _parse_folder_id:
        _sf = st.session_state.get("sf_client")
        _box_raw = (_sf.get("Box_Folder_Id__c", "") or "") if _sf else ""
        if _box_raw:
            st.divider()

            _box_folder_id = _parse_folder_id(_box_raw)

            # Header with "Open in Box" link
            st.markdown(
                f'<div style="display:flex; align-items:center; justify-content:space-between;">'
                f'<span style="font-size:1.05rem; font-weight:700;">Client Documents</span>'
                f'<a href="https://app.box.com/folder/{html_mod.escape(_box_folder_id)}" '
                f'target="_blank" style="font-size:0.8rem; color:#0066CC; text-decoration:none;">'
                f'Open in Box &#x2197;</a>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Initialize selected docs in session state
            if "_fa_selected_docs" not in st.session_state:
                st.session_state["_fa_selected_docs"] = []

            def _on_box_select(files: list[dict]) -> None:
                """Store selected files in session state."""
                existing_ids = {d["id"] for d in st.session_state.get("_fa_selected_docs", [])}
                for f in files:
                    if f["id"] not in existing_ids:
                        st.session_state["_fa_selected_docs"].append(f)

            already_ids = {d["id"] for d in st.session_state.get("_fa_selected_docs", [])}

            render_box_folder_browser(
                _box_folder_id,
                mode="picker",
                on_select=_on_box_select,
                already_selected_ids=already_ids,
                key_prefix="_fa_box",
                show_header=False,
                add_button_label="Add to Selection",
            )

            # Show selected documents with remove option
            selected_docs = st.session_state.get("_fa_selected_docs", [])
            if selected_docs:
                st.markdown("---")
                st.caption(f"**Selected:** {len(selected_docs)} document(s)")

                # Select All / Deselect All
                if st.button("Clear Selection", key="_fa_clear_sel", use_container_width=True):
                    st.session_state["_fa_selected_docs"] = []
                    st.rerun()

                for i, doc in enumerate(selected_docs):
                    doc_cols = st.columns([5, 1])
                    with doc_cols[0]:
                        ext = doc.get("extension", "") or ""
                        st.caption(f"{doc['name']}" + (f" (.{ext})" if ext else ""))
                    with doc_cols[1]:
                        if st.button("✕", key=f"_fa_rm_doc_{i}"):
                            st.session_state["_fa_selected_docs"].pop(i)
                            st.rerun()

    render_tool_notes("forms-assistant")


# -- Handle save (after sidebar renders) -------------------------------------

if save_clicked and primary_form:
    _do_save(primary_form)
    st.rerun()

# -- Handle validate ----------------------------------------------------------

if validate_clicked and primary_form:
    errors: dict[str, list[str]] = {}
    fields_dict = get_all_fields(primary_form)
    for _section_name, fields in fields_dict.items():
        for field_def in fields:
            val = str(st.session_state.form_data.get(field_def.name, ""))
            field_errors = validate_field(field_def, val)
            if field_errors:
                errors[field_def.name] = field_errors
    st.session_state.validation_errors = errors

# -- Main area: Tabs ----------------------------------------------------------

tab_fill, tab_ingest, tab_mappings, tab_sync = st.tabs(
    ["Fill Forms", "Manage Forms", "Field Mappings", "Sync & History"]
)

with tab_fill:
    render_fill_tab()

with tab_ingest:
    render_ingest_tab()

with tab_mappings:
    render_mappings_tab()

with tab_sync:
    render_sync_tab()

# -- Auto-save on every rerun ------------------------------------------------

if primary_form and st.session_state.form_data:
    _auto_save(primary_form)
