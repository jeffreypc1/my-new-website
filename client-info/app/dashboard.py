"""Client Info — View and update Salesforce contact data.

Pull client data by Customer ID, review and edit fields, and push
changes back to Salesforce. Picklist fields render as dropdowns with
valid Salesforce values.
"""

from __future__ import annotations

import html as html_mod
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.salesforce_client import (
    get_client,
    get_field_metadata,
    load_active_client,
    save_active_client,
    update_client,
)

# -- Page config --------------------------------------------------------------

st.set_page_config(
    page_title="Client Info — O'Brien Immigration Law",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -- CSS ----------------------------------------------------------------------

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

#MainMenu, header[data-testid="stHeader"], footer,
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
</style>
""",
    unsafe_allow_html=True,
)

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
    ],
}

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

# -- Editable fields ----------------------------------------------------------

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

                # Choose widget based on Salesforce field type
                if ftype == "picklist" and picklist_vals:
                    options = [""] + [pv["value"] for pv in picklist_vals]
                    try:
                        idx = options.index(display_val)
                    except ValueError:
                        # Current value not in picklist — add it
                        if display_val:
                            options.insert(1, display_val)
                            idx = 1
                        else:
                            idx = 0
                    new_val = st.selectbox(label, options=options, index=idx, key=key)

                elif ftype == "multipicklist" and picklist_vals:
                    all_opts = [pv["value"] for pv in picklist_vals]
                    current_selected = [v.strip() for v in display_val.split(";")] if display_val else []
                    selected = st.multiselect(label, options=all_opts, default=current_selected, key=key)
                    new_val = ";".join(selected) if selected else ""

                elif ftype == "textarea":
                    new_val = st.text_area(label, value=display_val, key=key, height=80)

                elif ftype == "boolean":
                    new_val = st.checkbox(label, value=display_val.lower() == "true", key=key)
                    # Convert back to compare
                    bool_str = str(new_val).lower()
                    if bool_str != display_val.lower():
                        edited_values[api_name] = new_val
                    continue

                else:
                    # string, email, phone, date, etc. — text input
                    new_val = st.text_input(label, value=display_val, key=key)

                if new_val != display_val:
                    edited_values[api_name] = new_val if new_val else None

# -- Push to Salesforce -------------------------------------------------------

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
                update_client(sf_id, edited_values)
                # Refresh the record
                record = get_client(sf.get("Customer_ID__c", ""))
                if record:
                    st.session_state.sf_client = record
                    save_active_client(record)
                # Clear widget keys so they reload with fresh values
                for key in list(st.session_state.keys()):
                    if key.startswith("fld_"):
                        del st.session_state[key]
                st.success(f"Updated {len(edited_values)} field(s) in Salesforce")
                st.rerun()
            except Exception as e:
                st.error(f"Push failed: {e}")

    if not edited_values:
        st.caption("Edit any field above, then push changes back to Salesforce.")
