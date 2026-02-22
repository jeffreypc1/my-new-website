"""Client Info — View and update Salesforce contact data.

Pull client data by Customer ID, review and edit fields, and push
changes back to Salesforce. Picklist fields render as dropdowns with
valid Salesforce values.
"""

from __future__ import annotations

import html as html_mod
import sys
from datetime import date as _date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.config_store import get_config_value
from shared.salesforce_client import (
    get_client,
    get_field_metadata,
    get_legal_cases,
    get_legal_case_field_metadata,
    load_active_client,
    save_active_client,
    update_client,
    update_legal_case,
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
    page_title="Client Info — O'Brien Immigration Law",
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

.nav-bar {
    display: flex;
    align-items: center;
    padding: 10px 4px;
    margin: -1rem 0 1.2rem 0;
    border-bottom: 1px solid rgba(0,0,0,0.07);
}
.nav-back {
    display: flex; align-items: center; gap: 6px;
    font-family: 'Inter', sans-serif; font-size: 0.85rem;
    font-weight: 500; color: #0066CC; text-decoration: none;
    min-width: 150px;
}
.nav-back:hover { color: #004499; text-decoration: underline; }
.nav-title {
    flex: 1; text-align: center;
    font-family: 'Inter', sans-serif; font-size: 1.15rem;
    font-weight: 700; color: #1a2744; letter-spacing: -0.02em;
}
.nav-firm { font-weight: 400; color: #86868b; font-size: 0.85rem; margin-left: 8px; }
.nav-spacer { min-width: 150px; }

.section-label {
    font-size: 0.78rem; font-weight: 600; color: #5a6a85;
    text-transform: uppercase; letter-spacing: 0.04em;
    margin-bottom: 4px; margin-top: 16px;
}

/* Read-only fields: plain text labels */
.ro-field { margin-bottom: 14px; }
.ro-label {
    font-size: 0.82rem; font-weight: 500; color: #5a6a85;
    margin-bottom: 2px;
}
.ro-value {
    font-size: 0.95rem; color: #1a2744; font-weight: 500;
    padding: 6px 0 4px 0;
    border-bottom: 1px solid #e8ecf1;
    min-height: 1.4em;
}

/* Editable fields: active border */
[data-testid="stTextInput"] input:not(:disabled),
[data-testid="stNumberInput"] input:not(:disabled),
[data-testid="stTextArea"] textarea:not(:disabled),
[data-testid="stDateInput"] input {
    border: 1.5px solid #4A90D9 !important;
    background: #ffffff !important;
}
[data-testid="stSelectbox"] > div > div > div,
[data-testid="stMultiSelect"] > div > div > div {
    border-color: #4A90D9 !important;
    background: #ffffff !important;
}
</style>
""",
    unsafe_allow_html=True,
)

from shared.auth import require_auth, render_logout
require_auth()

# -- Nav bar ------------------------------------------------------------------

st.markdown(
    """
<div class="nav-bar">
    <a href="http://localhost:8502" class="nav-back">&#8592; Staff Dashboard</a>
    <div class="nav-title">Client Info<span class="nav-firm">&mdash; O'Brien Immigration Law</span></div>
    <div class="nav-spacer"></div>
</div>
""",
    unsafe_allow_html=True,
)
render_logout()

# -- Client banner (shared) ---------------------------------------------------
try:
    from shared.client_banner import render_client_banner
    render_client_banner()
    if render_tool_help:
        render_tool_help("client-info")
    if render_feedback_button:
        render_feedback_button("client-info")
except Exception:
    pass

# -- Sidebar ------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Client Info")
    active = load_active_client()
    if active:
        st.caption(f"**{active.get('Name', '')}** #{active.get('Customer_ID__c', '')}")
        box_fid = active.get("Box_Folder_Id__c", "")
        if box_fid:
            st.markdown(f"[Open Box Folder](https://app.box.com/folder/{box_fid})")
    st.markdown("---")
    st.caption("Tabs:")
    st.markdown("- Contact Fields")
    st.markdown("- Legal Cases")
    try:
        from shared.tool_notes import render_tool_notes
        render_tool_notes("client-info")
    except Exception:
        pass

# -- Pull client --------------------------------------------------------------

pull_cols = st.columns([2, 1, 5])
with pull_cols[0]:
    customer_id = st.text_input(
        "Client #",
        value=st.query_params.get("client_id", ""),
        placeholder="Enter client number",
        label_visibility="collapsed",
    )
with pull_cols[1]:
    do_pull = st.button("Pull from Salesforce", type="primary", use_container_width=True)

# Auto-pull on first load from query param or shared file
if not st.session_state.get("_ci_loaded"):
    if customer_id:
        do_pull = True
    else:
        active = load_active_client()
        if active:
            st.session_state.sf_client = active
            st.session_state.sf_id = active.get("Id", "")
            st.session_state.sf_legal_cases = active.get("legal_cases", [])
            st.session_state.sf_legal_case = active.get("selected_legal_case")
            st.session_state._ci_loaded = True

if do_pull and customer_id:
    # Clear old field widget keys so stale values don't persist
    for key in list(st.session_state.keys()):
        if key.startswith("fld_"):
            del st.session_state[key]
    try:
        record = get_client(customer_id.strip())
        if record:
            st.session_state.sf_client = record
            st.session_state.sf_id = record.get("Id", "")
            st.session_state._ci_loaded = True
            # Fetch Legal Cases
            sf_id = record.get("Id", "")
            if sf_id:
                try:
                    cases = get_legal_cases(sf_id)
                except Exception:
                    cases = []
                st.session_state.sf_legal_cases = cases
                # Auto-select: match Contact's Legal_Case__c lookup, or sole case
                lc_lookup = record.get("Legal_Case__c")
                match = next((c for c in cases if c["Id"] == lc_lookup), None) if lc_lookup else None
                st.session_state.sf_legal_case = match or (cases[0] if len(cases) == 1 else None)
                # Persist for cross-tool access
                record["legal_cases"] = cases
                record["selected_legal_case"] = st.session_state.sf_legal_case
            save_active_client(record)
            st.rerun()
        else:
            st.warning(f"No client found for #{customer_id}")
    except Exception as e:
        st.error(f"Salesforce error: {e}")

if not st.session_state.get("sf_client"):
    st.info("Enter a client number and click Pull to load their information.")
    st.stop()

sf = st.session_state.sf_client

# -- Load field metadata for smart widgets ------------------------------------

# Collect all API names we'll display
FIELD_GROUPS = {
    "Identity": [
        "FirstName", "LastName", "A_Number__c", "Birthdate",
        "Gender__c", "Pronoun__c", "Marital_status__c",
    ],
    "Contact Information": [
        "Email", "MobilePhone", "Phone",
        "MailingStreet", "MailingCity", "MailingState",
        "MailingPostalCode", "MailingCountry",
    ],
    "Immigration Details": [
        "Country__c", "City_of_Birth__c", "Best_Language__c",
        "Immigration_Status__c", "Immigration_Court__c",
        "Legal_Case_Type__c", "Client_Status__c",
        "Date_of_First_Entry_to_US__c", "Date_of_Most_Recent_US_Entry__c",
        "Status_of_Last_Arrival__c", "Place_of_Last_Arrival__c",
    ],
    "Family": [
        "Spouse_Name__c", "Mother_s_First_Name__c", "Mother_s_Last_Name__c",
        "Father_s_First_Name__c", "Father_s_Last_Name__c",
    ],
    "Case Information": [
        "CaseNumber__c", "Client_Case_Strategy__c", "Nexus__c", "PSG__c",
        "Box_Folder_Id__c",
    ],
}

# Filter out fields disabled in Admin Panel
_disabled_fields: list[str] = get_config_value("salesforce", "disabled_fields", [])
for group in FIELD_GROUPS:
    FIELD_GROUPS[group] = [f for f in FIELD_GROUPS[group] if f not in _disabled_fields]

all_field_names = []
for fields in FIELD_GROUPS.values():
    all_field_names.extend(fields)

try:
    field_meta = get_field_metadata(all_field_names)
except Exception:
    field_meta = {}

# -- Header -------------------------------------------------------------------

st.markdown(f"### {html_mod.escape(sf.get('Name', ''))}")
st.caption(f"Customer ID: {sf.get('Customer_ID__c', '')} · Salesforce ID: {sf.get('Id', '')}")

# -- Helpers for field rendering ----------------------------------------------

def _parse_sf_date(val) -> _date | None:
    """Parse a Salesforce date/datetime string to a Python date."""
    if not val:
        return None
    s = str(val)[:10]  # YYYY-MM-DD portion
    try:
        return _date.fromisoformat(s)
    except (ValueError, TypeError):
        return None

def _format_date_display(val) -> str:
    """Format a date value as MM/DD/YYYY for read-only display."""
    d = _parse_sf_date(val) if not isinstance(val, _date) else val
    return d.strftime("%m/%d/%Y") if d else ""

def _render_ro_field(label: str, value: str):
    """Render a read-only field as a styled plain-text label."""
    v = html_mod.escape(str(value)) if value else "\u2014"
    st.markdown(
        f'<div class="ro-field">'
        f'<div class="ro-label">{html_mod.escape(label)}</div>'
        f'<div class="ro-value">{v}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

# -- Tabs ---------------------------------------------------------------------

tab_contact, tab_cases = st.tabs(["Contact Fields", "Legal Cases"])

# -- Contact Fields tab -------------------------------------------------------

with tab_contact:
    edited_values = {}

    col_left, col_right = st.columns(2, gap="large")

    group_names = list(FIELD_GROUPS.keys())
    left_groups = group_names[:3]
    right_groups = group_names[3:]

    for col, groups in [(col_left, left_groups), (col_right, right_groups)]:
        with col:
            for group_name in groups:
                api_names = FIELD_GROUPS[group_name]
                st.markdown(f'<div class="section-label">{group_name}</div>', unsafe_allow_html=True)

                for api_name in api_names:
                    meta = field_meta.get(api_name, {})
                    label = meta.get("label", api_name)
                    ftype = meta.get("type", "string")
                    picklist_vals = meta.get("picklistValues", [])
                    current_val = sf.get(api_name)
                    display_val = str(current_val) if current_val is not None else ""
                    key = f"fld_{api_name}"
                    edit_label = f"\u270f\ufe0f {label}"

                    # Choose widget based on Salesforce field type
                    if ftype == "picklist" and picklist_vals:
                        options = [""] + [pv["value"] for pv in picklist_vals]
                        try:
                            idx = options.index(display_val)
                        except ValueError:
                            if display_val:
                                options.insert(1, display_val)
                                idx = 1
                            else:
                                idx = 0
                        new_val = st.selectbox(edit_label, options=options, index=idx, key=key)

                    elif ftype == "multipicklist" and picklist_vals:
                        all_opts = [pv["value"] for pv in picklist_vals]
                        current_selected = [v.strip() for v in display_val.split(";")] if display_val else []
                        selected = st.multiselect(edit_label, options=all_opts, default=current_selected, key=key)
                        new_val = ";".join(selected) if selected else ""

                    elif ftype == "textarea":
                        new_val = st.text_area(edit_label, value=display_val, key=key, height=80)

                    elif ftype == "boolean":
                        new_val = st.checkbox(edit_label, value=display_val.lower() == "true", key=key)
                        bool_str = str(new_val).lower()
                        if bool_str != display_val.lower():
                            edited_values[api_name] = new_val
                        continue

                    elif ftype == "date":
                        parsed = _parse_sf_date(current_val)
                        new_date = st.date_input(edit_label, value=parsed, format="MM/DD/YYYY", key=key)
                        orig_str = str(current_val)[:10] if current_val else None
                        new_str = new_date.strftime("%Y-%m-%d") if new_date else None
                        if new_str != orig_str:
                            edited_values[api_name] = new_str
                        continue

                    else:
                        new_val = st.text_input(edit_label, value=display_val, key=key)

                    if new_val != display_val:
                        edited_values[api_name] = new_val if new_val else None

    # -- Push to Salesforce ---------------------------------------------------

    st.markdown("---")
    push_cols = st.columns([1, 2, 1])
    with push_cols[1]:
        if edited_values:
            st.info(f"{len(edited_values)} field(s) changed")

        if st.button(
            "Push to Salesforce",
            type="primary",
            use_container_width=True,
            disabled=not edited_values,
        ):
            sf_id = st.session_state.get("sf_id", "")
            if not sf_id:
                st.error("No Salesforce record ID found. Pull the client again.")
            else:
                try:
                    # Remove any disabled fields as safety net
                    push_values = {k: v for k, v in edited_values.items() if k not in _disabled_fields}
                    update_client(sf_id, push_values)
                    # Refresh the record
                    record = get_client(sf.get("Customer_ID__c", ""))
                    if record:
                        st.session_state.sf_client = record
                        save_active_client(record)
                    # Clear widget keys so they reload with fresh values
                    for key in list(st.session_state.keys()):
                        if key.startswith("fld_"):
                            del st.session_state[key]
                    st.success(f"Updated {len(push_values)} field(s) in Salesforce")
                    st.rerun()
                except Exception as e:
                    st.error(f"Push failed: {e}")

        if not edited_values:
            st.caption("Edit any field above, then push changes back to Salesforce.")

# -- Legal Cases tab ----------------------------------------------------------

# Field groups for the Legal Case tab layout
_LC_FIELD_GROUPS = {
    "Case Identity": [
        "Name", "Legal_Case_Full_Name__c", "Primary_CID__c",
        "A_number_dashed__c", "Id", "CreatedDate", "LastModifiedDate",
    ],
    "Case Details": [
        "Legal_Case_Type__c", "Bar_Number__c",
        "EOIR_Email_Subject__c", "Make_Service_Request__c",
    ],
    "People": [
        "Primary_Applicant__c", "Primary_Attorney__c",
        "Primary_Assistant__c", "Hearing_Attorney__c",
    ],
    "Dates": [
        "Application_Priority_Date__c", "Submitted_Date__c",
        "Outcome_Date__c", "Next_Government_Date__c",
        "Type_of_next_date__c", "Watch_Date__c", "Watch_Date_Picklist__c",
    ],
}

# Reference fields: show resolved name instead of raw ID
_LC_REF_NAME_MAP = {
    "Primary_Applicant__c": "Primary_Applicant__r_Name",
    "Primary_Attorney__c": "Primary_Attorney__r_Name",
    "Primary_Assistant__c": "Primary_Assistant__r_Name",
    "Hearing_Attorney__c": "Hearing_Attorney__r_Name",
}

with tab_cases:
    legal_cases = st.session_state.get("sf_legal_cases", [])

    if not legal_cases:
        st.info("No Legal Cases found for this client.")
    else:
        st.caption(f"{len(legal_cases)} legal case(s) found")

        lc_options = [c.get("Name", "?") for c in legal_cases]
        current_lc = st.session_state.get("sf_legal_case")
        current_idx = 0
        if current_lc:
            for i, c in enumerate(legal_cases):
                if c["Id"] == current_lc.get("Id"):
                    current_idx = i
                    break

        selected_idx = st.selectbox(
            "Select Legal Case",
            range(len(lc_options)),
            format_func=lambda i: lc_options[i],
            index=current_idx,
            key="lc_select",
        )

        selected_case = legal_cases[selected_idx]

        # Persist selection if it changed
        if st.session_state.sf_legal_case != selected_case:
            st.session_state.sf_legal_case = selected_case
            sf["selected_legal_case"] = selected_case
            save_active_client(sf)

        # Load field metadata for smart widgets
        try:
            lc_meta = get_legal_case_field_metadata()
        except Exception:
            lc_meta = {}

        st.markdown("---")

        lc_edited = {}
        lc_col_left, lc_col_right = st.columns(2, gap="large")
        lc_group_names = list(_LC_FIELD_GROUPS.keys())

        for col, groups in [(lc_col_left, lc_group_names[:2]), (lc_col_right, lc_group_names[2:])]:
            with col:
                for group_name in groups:
                    api_names = _LC_FIELD_GROUPS[group_name]
                    st.markdown(f'<div class="section-label">{group_name}</div>', unsafe_allow_html=True)

                    for api_name in api_names:
                        meta = lc_meta.get(api_name, {})
                        label = meta.get("label", api_name)
                        ftype = meta.get("type", "string")
                        is_formula = meta.get("formula", False)
                        is_updateable = meta.get("updateable", False)
                        picklist_vals = meta.get("picklistValues", [])
                        is_ref = api_name in _LC_REF_NAME_MAP
                        key = f"lc_{api_name}"

                        # Reference fields → plain text with resolved name
                        if is_ref:
                            name_key = _LC_REF_NAME_MAP[api_name]
                            display = selected_case.get(name_key) or selected_case.get(api_name) or ""
                            _render_ro_field(label, display)
                            continue

                        current_val = selected_case.get(api_name)
                        display_val = str(current_val) if current_val is not None else ""
                        read_only = not is_updateable or is_formula

                        # Read-only → plain text label
                        if read_only:
                            if ftype in ("date", "datetime"):
                                _render_ro_field(label, _format_date_display(current_val))
                            else:
                                _render_ro_field(label, display_val)
                            continue

                        edit_label = f"\u270f\ufe0f {label}"

                        if ftype == "picklist" and picklist_vals:
                            options = [""] + [pv["value"] for pv in picklist_vals]
                            try:
                                idx = options.index(display_val)
                            except ValueError:
                                if display_val:
                                    options.insert(1, display_val)
                                    idx = 1
                                else:
                                    idx = 0
                            new_val = st.selectbox(edit_label, options=options, index=idx, key=key)

                        elif ftype == "date":
                            parsed = _parse_sf_date(current_val)
                            new_date = st.date_input(edit_label, value=parsed, format="MM/DD/YYYY", key=key)
                            orig_str = str(current_val)[:10] if current_val else None
                            new_str = new_date.strftime("%Y-%m-%d") if new_date else None
                            if new_str != orig_str:
                                lc_edited[api_name] = new_str
                            continue

                        else:
                            new_val = st.text_input(edit_label, value=display_val, key=key)

                        if new_val != display_val:
                            lc_edited[api_name] = new_val if new_val else None

        # -- Push Legal Case changes ------------------------------------------
        st.markdown("---")
        lc_push_cols = st.columns([1, 2, 1])
        with lc_push_cols[1]:
            if lc_edited:
                st.info(f"{len(lc_edited)} field(s) changed")

            if st.button(
                "Push Legal Case to Salesforce",
                type="primary",
                use_container_width=True,
                disabled=not lc_edited,
                key="lc_push",
            ):
                case_id = selected_case.get("Id", "")
                if not case_id:
                    st.error("No Legal Case record ID found.")
                else:
                    try:
                        update_legal_case(case_id, lc_edited)
                        # Re-fetch all cases to refresh data
                        sf_id = st.session_state.get("sf_id", "")
                        if sf_id:
                            cases = get_legal_cases(sf_id)
                            st.session_state.sf_legal_cases = cases
                            # Re-select the same case
                            updated = next((c for c in cases if c["Id"] == case_id), None)
                            st.session_state.sf_legal_case = updated
                            sf["legal_cases"] = cases
                            sf["selected_legal_case"] = updated
                            save_active_client(sf)
                        # Clear lc widget keys
                        for wkey in list(st.session_state.keys()):
                            if wkey.startswith("lc_"):
                                del st.session_state[wkey]
                        st.success(f"Updated {len(lc_edited)} field(s) on Legal Case")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Push failed: {e}")

            if not lc_edited:
                st.caption("Edit any field above, then push changes back to Salesforce.")

# ═══════════════════════════════════════════════════════════════════════════════
# BOX DOCUMENT BROWSER
# ═══════════════════════════════════════════════════════════════════════════════

import base64
import time

_box_available = True
try:
    from shared.box_client import list_folder_items, get_file_content, get_folder_name, parse_folder_id
except ImportError:
    _box_available = False

st.markdown("---")
st.subheader("Client Documents (Box)")

_folder_id_raw = sf.get("Box_Folder_Id__c", "") or ""
_folder_id = parse_folder_id(_folder_id_raw) if (_box_available and _folder_id_raw) else _folder_id_raw

if not _folder_id:
    st.info("No Box folder linked. Enter the Box Folder ID in the **Box_Folder_Id__c** field above and push to Salesforce.")
elif not _box_available:
    st.warning("Box SDK not installed. Run `uv sync` in the client-info directory.")
else:
    # Reset nav stack when client changes
    if st.session_state.get("_box_client_id") != sf.get("Customer_ID__c"):
        st.session_state._box_nav_stack = [_folder_id]
        st.session_state._box_client_id = sf.get("Customer_ID__c")
        st.session_state.pop("_box_cache", None)

    if "_box_nav_stack" not in st.session_state:
        st.session_state._box_nav_stack = [_folder_id]

    current_folder_id = st.session_state._box_nav_stack[-1]

    # Back button + folder name
    nav_cols = st.columns([1, 5])
    with nav_cols[0]:
        if len(st.session_state._box_nav_stack) > 1:
            if st.button("Back", key="box_back"):
                st.session_state._box_nav_stack.pop()
                st.session_state.pop("_box_cache", None)
                st.rerun()
    with nav_cols[1]:
        try:
            folder_name = get_folder_name(current_folder_id)
            st.caption(f"Folder: **{folder_name}** (`{current_folder_id}`)")
        except Exception:
            st.caption(f"Folder ID: `{current_folder_id}`")

    # Cached folder listing (60-second TTL)
    cache = st.session_state.get("_box_cache", {})
    cache_key = current_folder_id
    cached = cache.get(cache_key)
    if cached and (time.time() - cached["ts"] < 60):
        items = cached["items"]
    else:
        try:
            with st.spinner("Loading folder contents..."):
                items = list_folder_items(current_folder_id)
            cache[cache_key] = {"items": items, "ts": time.time()}
            st.session_state._box_cache = cache
        except Exception as e:
            st.error(f"Could not load Box folder: {e}")
            items = []

    if not items:
        if not st.session_state.get("_box_load_error"):
            st.caption("This folder is empty.")
    else:
        def _type_badge(item: dict) -> str:
            ext = item.get("extension", "").lower()
            if item["type"] == "folder":
                return "FOLDER"
            if ext in ("pdf",):
                return "PDF"
            if ext in ("doc", "docx"):
                return "DOC"
            if ext in ("jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"):
                return "IMG"
            if ext in ("xls", "xlsx", "csv"):
                return "XLS"
            if ext in ("txt", "rtf", "md"):
                return "TXT"
            return "FILE"

        def _human_size(size: int) -> str:
            if size < 1024:
                return f"{size} B"
            if size < 1024 * 1024:
                return f"{size / 1024:.0f} KB"
            return f"{size / (1024 * 1024):.1f} MB"

        for idx, item in enumerate(items):
            badge = _type_badge(item)
            cols = st.columns([1, 4, 1, 2, 2])
            with cols[0]:
                st.markdown(f"**`{badge}`**")
            with cols[1]:
                st.markdown(item["name"])
            with cols[2]:
                if item["type"] != "folder":
                    st.caption(_human_size(item["size"]))
            with cols[3]:
                if item["type"] != "folder":
                    modified = item.get("modified_at", "")
                    if modified and len(modified) >= 10:
                        st.caption(modified[:10])
            with cols[4]:
                if item["type"] == "folder":
                    if st.button("Open", key=f"box_open_{item['id']}_{idx}"):
                        st.session_state._box_nav_stack.append(item["id"])
                        st.session_state.pop("_box_cache", None)
                        st.rerun()
                else:
                    btn_cols = st.columns(2)
                    with btn_cols[0]:
                        if st.button("Preview", key=f"box_preview_{item['id']}_{idx}"):
                            st.session_state._box_preview_item = item
                    with btn_cols[1]:
                        st.markdown(
                            f'<a href="{item["web_url"]}" target="_blank" '
                            f'style="font-size:0.8rem;color:#0066CC;text-decoration:none;">Open in Box</a>',
                            unsafe_allow_html=True,
                        )

    # Preview dialog
    @st.dialog("Document Preview", width="large")
    def _show_preview(item: dict):
        st.markdown(f"**{item['name']}**")
        ext = item.get("extension", "").lower()
        size = item.get("size", 0)
        content = None

        if size > 10 * 1024 * 1024:
            st.warning("File is larger than 10 MB. Download to view.")
        elif ext == "pdf":
            try:
                with st.spinner("Loading PDF..."):
                    content = get_file_content(item["id"])
                b64 = base64.b64encode(content).decode()
                st.markdown(
                    f'<iframe src="data:application/pdf;base64,{b64}" '
                    f'width="100%" height="600px" type="application/pdf"></iframe>',
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.error(f"Could not load PDF: {e}")
        elif ext in ("jpg", "jpeg", "png", "gif", "bmp", "webp"):
            try:
                with st.spinner("Loading image..."):
                    content = get_file_content(item["id"])
                st.image(content, caption=item["name"])
            except Exception as e:
                st.error(f"Could not load image: {e}")
        elif ext in ("txt", "md", "rtf", "csv"):
            try:
                with st.spinner("Loading file..."):
                    content = get_file_content(item["id"])
                st.code(content.decode("utf-8", errors="replace"), language=None)
            except Exception as e:
                st.error(f"Could not load file: {e}")
        else:
            st.info("Inline preview not available for this file type.")

        # Download button for any file
        try:
            if content is None:
                with st.spinner("Preparing download..."):
                    content = get_file_content(item["id"])
            st.download_button(
                "Download",
                data=content,
                file_name=item["name"],
                use_container_width=True,
            )
        except Exception:
            st.markdown(
                f'[Download from Box]({item["web_url"]})',
                unsafe_allow_html=True,
            )

    if st.session_state.get("_box_preview_item"):
        _show_preview(st.session_state._box_preview_item)
        st.session_state._box_preview_item = None
