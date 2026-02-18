"""Shared client info banner for all tool dashboards.

Renders a compact client info bar at the top of each tool page.
Loads the active client from the shared JSON file, with inline
option to pull a new client or refresh. Includes a "Files" button
that opens a Box folder browser dialog when the client has a
Box_Folder_ID__c, and an "Email" button that opens a compose
dialog to send emails via Salesforce.

Usage in any tool's dashboard.py:
    from shared.client_banner import render_client_banner
    render_client_banner()  # call right after the nav bar
"""

from __future__ import annotations

import html as html_mod
import time

import streamlit as st
import streamlit.components.v1 as _components


_BANNER_FIELD_DEFAULTS = [
    "A_Number__c", "Country__c", "Best_Language__c", "Immigration_Status__c",
]

# Salesforce date fields that should display as MM/DD/YYYY
_DATE_FIELDS = {
    "Birthdate",
    "Date_of_First_Entry_to_US__c",
    "Date_of_Most_Recent_US_Entry__c",
}


def _format_date_value(val: str) -> str:
    """Convert YYYY-MM-DD to MM/DD/YYYY if it matches, otherwise return as-is."""
    if not val or len(val) != 10:
        return val
    try:
        parts = val.split("-")
        if len(parts) == 3 and len(parts[0]) == 4:
            return f"{parts[1]}/{parts[2]}/{parts[0]}"
    except Exception:
        pass
    return val


def _get_banner_fields() -> list[str]:
    """Load the list of enabled banner fields from global settings."""
    try:
        from shared.config_store import load_config
        settings = load_config("global-settings") or {}
        return settings.get("banner_fields", _BANNER_FIELD_DEFAULTS)
    except Exception:
        return _BANNER_FIELD_DEFAULTS


_BANNER_CSS = """
<style>
.sf-banner {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px 20px;
    padding: 8px 16px;
    margin: -0.5rem 0 0.8rem 0;
    background: #f0f4ff;
    border: 1px solid #d0daf0;
    border-radius: 8px;
    font-size: 0.82rem;
    color: #3a4a6b;
}
.sf-banner-name {
    font-weight: 700;
    color: #1a2744;
    font-size: 0.9rem;
}
.sf-banner-sep {
    color: #c0c8d8;
}
.sf-banner-field {
    color: #5a6a85;
}
.sf-banner-field strong {
    color: #1a2744;
    font-weight: 600;
}
/* Blue glow on client ID input */
input[placeholder*="client number"],
input[placeholder*="Client #"] {
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.35), 0 0 12px rgba(59, 130, 246, 0.2) !important;
    border: 2px solid rgba(59, 130, 246, 0.6) !important;
    border-radius: 8px !important;
}
</style>
"""

_SIDEBAR_TOGGLE_HTML = """
<style>
  body { margin: 0; padding: 0; background: transparent; overflow: hidden; }
  a {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 13px;
    font-weight: 500;
    color: #0066CC;
    text-decoration: none;
    cursor: pointer;
  }
  a:hover { text-decoration: underline; }
</style>
<a onclick="
    var doc = window.parent.document;
    var expand = doc.querySelector('[data-testid=\\'stExpandSidebarButton\\']');
    var collapse = doc.querySelector('[data-testid=\\'stSidebarCollapseButton\\']');
    if (expand) { expand.click(); }
    else if (collapse) { collapse.click(); }
">&#9776; Toggle Sidebar</a>
"""


# -- Box folder dialog --------------------------------------------------------

@st.dialog("Client Files", width="large")
def _show_box_files(folder_id: str, client_name: str):
    """Dialog showing Box folder contents with navigation."""
    try:
        from shared.box_client import (
            list_folder_items,
            get_folder_name,
            parse_folder_id,
        )
    except ImportError:
        st.error("Box client not available. Check that box-sdk-gen is installed.")
        return

    root_id = parse_folder_id(folder_id)

    # Track client for nav reset
    client_id = st.session_state.get("_box_dlg_client", "")
    current_client = st.session_state.get("sf_client", {}).get("Customer_ID__c", "")
    if client_id != current_client:
        st.session_state._box_dlg_nav = [root_id]
        st.session_state._box_dlg_client = current_client
        st.session_state.pop("_box_dlg_cache", None)

    if "_box_dlg_nav" not in st.session_state:
        st.session_state._box_dlg_nav = [root_id]

    current = st.session_state._box_dlg_nav[-1]

    # Header with back button and folder name
    if len(st.session_state._box_dlg_nav) > 1:
        c1, c2 = st.columns([1, 5])
        with c1:
            if st.button("Back", use_container_width=True, key="_box_dlg_back"):
                st.session_state._box_dlg_nav.pop()
                st.session_state.pop("_box_dlg_cache", None)
                st.rerun()
        with c2:
            try:
                fname = get_folder_name(current)
            except Exception:
                fname = f"Folder {current}"
            st.markdown(f"**{fname}**")
    else:
        st.markdown(f"**{client_name} — Documents**")

    # Cached listing (60-second TTL)
    cache = st.session_state.get("_box_dlg_cache", {})
    cached = cache.get(current)
    if cached and (time.time() - cached["ts"] < 60):
        items = cached["items"]
    else:
        try:
            with st.spinner("Loading files..."):
                items = list_folder_items(current)
            cache[current] = {"items": items, "ts": time.time()}
            st.session_state._box_dlg_cache = cache
        except Exception as e:
            st.error(f"Box error: {e}")
            return

    if not items:
        st.caption("Empty folder")
    else:
        for idx, item in enumerate(items):
            ext = (item.get("extension", "") or "").lower()
            if item["type"] == "folder":
                badge = "DIR"
            elif ext == "pdf":
                badge = "PDF"
            elif ext in ("doc", "docx"):
                badge = "DOC"
            elif ext in ("jpg", "jpeg", "png", "gif"):
                badge = "IMG"
            elif ext in ("xls", "xlsx", "csv"):
                badge = "XLS"
            else:
                badge = "FILE"

            if item["type"] == "folder":
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"`{badge}` **{item['name']}**")
                with c2:
                    if st.button("Open", key=f"_box_dlg_f_{item['id']}_{idx}",
                                 use_container_width=True):
                        st.session_state._box_dlg_nav.append(item["id"])
                        st.session_state.pop("_box_dlg_cache", None)
                        st.rerun()
            else:
                # Format file size
                size = item.get("size", 0)
                if size >= 1_000_000:
                    size_str = f"{size / 1_000_000:.1f} MB"
                elif size >= 1_000:
                    size_str = f"{size / 1_000:.0f} KB"
                else:
                    size_str = f"{size} B"

                st.markdown(
                    f"`{badge}` [{item['name']}]({item['web_url']}) "
                    f"<span style='color:#86868b;font-size:0.75rem;'>({size_str})</span>",
                    unsafe_allow_html=True,
                )

    # Footer link
    box_url = f"https://app.box.com/folder/{root_id}"
    st.markdown("---")
    st.markdown(
        f"[Open folder in Box]({box_url}) &nbsp;|&nbsp; "
        f"[Full browser in Client Info](http://localhost:8512)",
        unsafe_allow_html=True,
    )


# -- Email compose dialog -----------------------------------------------------

@st.dialog("Send Email", width="large")
def _show_email_compose(client_record: dict, sf_available: bool):
    """Dialog for composing and sending an email via Salesforce."""
    from shared.config_store import load_config

    client_name = client_record.get("Name", "Client")
    client_email = client_record.get("Email", "")

    st.markdown(f"**To:** {client_name} ({client_email})")

    # Load staff directory for sender selection
    staff = load_config("staff-directory") or []
    staff_options = []
    for member in staff:
        first = member.get("first_name", "")
        last = member.get("last_name", "")
        email = member.get("email", "")
        display = f"{first} {last}".strip()
        if email:
            display += f" ({email})"
        staff_options.append(display)

    if staff_options:
        sender_idx = st.selectbox(
            "From (sender)",
            range(len(staff_options)),
            format_func=lambda i: staff_options[i],
            key="_email_sender",
        )
        sender_name = f"{staff[sender_idx].get('first_name', '')} {staff[sender_idx].get('last_name', '')}".strip()
    else:
        st.warning("No staff members configured. Add staff in Admin Panel > Integrations > Staff Directory.")
        sender_name = ""

    # Load email templates
    templates = load_config("email-templates") or []
    template_names = ["(none)"] + [t.get("name", f"Template {i}") for i, t in enumerate(templates)]

    selected_tpl = st.selectbox("Template", template_names, key="_email_template")

    # Determine initial subject/body from template
    init_subject = ""
    init_body = ""
    if selected_tpl != "(none)":
        tpl_idx = template_names.index(selected_tpl) - 1  # offset for "(none)"
        if 0 <= tpl_idx < len(templates):
            tpl = templates[tpl_idx]
            try:
                from shared.email_service import merge_template
                init_subject, init_body = merge_template(
                    tpl.get("subject", ""),
                    tpl.get("body", ""),
                    client_record,
                )
            except ImportError:
                init_subject = tpl.get("subject", "")
                init_body = tpl.get("body", "")

    # Use session state to handle template switching
    if "_email_last_tpl" not in st.session_state or st.session_state._email_last_tpl != selected_tpl:
        st.session_state._email_last_tpl = selected_tpl
        st.session_state._email_subj_val = init_subject
        st.session_state._email_body_val = init_body
        st.rerun()

    subject = st.text_input("Subject", value=st.session_state.get("_email_subj_val", init_subject), key="_email_subject")
    body = st.text_area("Body", value=st.session_state.get("_email_body_val", init_body), key="_email_body", height=250)

    # Send button
    can_send = bool(subject.strip() and body.strip() and sender_name and sf_available)
    if st.button("Send Email", type="primary", key="_email_send", disabled=not can_send):
        try:
            from shared.email_service import send_email
            from shared.salesforce_client import _sf_conn
            sf = _sf_conn()
            contact_id = client_record.get("Id", "")
            result = send_email(sf, contact_id, client_email, subject, body, sender_name)
            if result.get("success"):
                st.success(result.get("message", "Email sent!"))
                # Clean up session state
                for key in ("_email_last_tpl", "_email_subj_val", "_email_body_val"):
                    st.session_state.pop(key, None)
            else:
                st.error(f"Failed to send: {result.get('error', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error: {e}")

    if not sf_available:
        st.caption("Salesforce is unavailable. Email cannot be sent.")


# -- Main banner function ----------------------------------------------------

def render_client_banner() -> dict | None:
    """Render a client info banner with inline pull/change.

    Reads the active client from the shared JSON file. If a ?client_id=
    query param is present, it takes priority (and updates the file).
    Shows a compact input row to pull or change clients.

    Returns the active client SF record dict, or None.
    """
    _sf_available = True
    try:
        from shared.salesforce_client import (
            get_client,
            load_active_client,
            save_active_client,
        )
    except Exception:
        _sf_available = False
        import json as _json
        from pathlib import Path as _Path
        _FB = _Path(__file__).resolve().parent.parent / "data" / "active_client.json"
        def load_active_client():
            try: return _json.loads(_FB.read_text()) if _FB.exists() else None
            except Exception: return None
        def save_active_client(r): pass
        def get_client(c): return None

    # 1. Check query param (takes priority)
    params = st.query_params
    qp_cid = params.get("client_id", "")

    # 2. Load from shared file
    active = load_active_client()

    # 3. If query param has a different client, pull it
    if _sf_available and qp_cid and (not active or active.get("Customer_ID__c") != qp_cid):
        try:
            record = get_client(qp_cid.strip())
            if record:
                save_active_client(record)
                active = record
        except Exception:
            pass

    # 4. Sync to session state
    if active:
        st.session_state.sf_client = active

    # 5. Render pull bar + banner
    st.markdown(_BANNER_CSS, unsafe_allow_html=True)
    _components.html(_SIDEBAR_TOGGLE_HTML, height=28)

    if not _sf_available:
        st.caption("Salesforce unavailable — showing cached data.")

    has_box = bool(active and (active.get("Box_Folder_ID__c") or ""))
    has_email = bool(active and (active.get("Email") or ""))

    banner_cols = st.columns([3, 1, 1, 1, 1])
    with banner_cols[0]:
        new_cid = st.text_input(
            "Client #",
            value="",
            placeholder=f"Client # (current: {active.get('Customer_ID__c', 'none')})" if active else "Enter client number to pull",
            label_visibility="collapsed",
            key="_banner_client_id",
        )
    with banner_cols[1]:
        do_pull = st.button("Pull", use_container_width=True, type="primary", key="_banner_pull",
                            disabled=not _sf_available)
    with banner_cols[2]:
        do_refresh = st.button("Refresh", use_container_width=True, key="_banner_refresh",
                               disabled=not active or not _sf_available)
    with banner_cols[3]:
        do_files = st.button("Files", use_container_width=True, key="_banner_files",
                             disabled=not has_box)
    with banner_cols[4]:
        do_email = st.button("Email", use_container_width=True, key="_banner_email",
                             disabled=not has_email or not _sf_available)

    if do_pull and new_cid and _sf_available:
        try:
            record = get_client(new_cid.strip())
            if record:
                save_active_client(record)
                st.session_state.sf_client = record
                st.rerun()
            else:
                st.warning(f"No client found for #{new_cid}")
        except Exception as e:
            st.error(f"Salesforce error: {e}")

    if do_refresh and active and _sf_available:
        cid = active.get("Customer_ID__c", "")
        if cid:
            try:
                record = get_client(cid)
                if record:
                    save_active_client(record)
                    st.session_state.sf_client = record
                    st.rerun()
            except Exception as e:
                st.error(f"Refresh failed: {e}")

    if do_files and active:
        folder_id = active.get("Box_Folder_ID__c", "")
        client_name = active.get("Name", "Client")
        _show_box_files(folder_id, client_name)

    if do_email and active:
        _show_email_compose(active, _sf_available)

    # Render info bar
    if active:
        parts = [f'<span class="sf-banner-name">{html_mod.escape(active.get("Name", ""))}</span>']
        parts.append('<span class="sf-banner-sep">|</span>')

        # Customer ID is always shown
        if active.get("Customer_ID__c"):
            parts.append(f'<span class="sf-banner-field"><strong>#</strong>{html_mod.escape(str(active["Customer_ID__c"]))}</span>')

        # Load configurable fields from global settings
        _banner_fields = _get_banner_fields()

        # Display labels for nicer rendering
        _FIELD_LABELS = {
            "A_Number__c": "A#",
            "Birthdate": "DOB",
            "Gender__c": "Gender",
            "Pronoun__c": "Pronouns",
            "Marital_status__c": "Marital",
            "Email": "Email",
            "Phone": "Phone",
            "MobilePhone": "Mobile",
            "Country__c": None,  # show value only (no label prefix)
            "City_of_Birth__c": "Born in",
            "Best_Language__c": None,
            "Immigration_Status__c": None,
            "Immigration_Court__c": "Court",
            "Legal_Case_Type__c": "Case Type",
            "Client_Status__c": "Status",
            "CaseNumber__c": "Case #",
            "Nexus__c": "Nexus",
            "PSG__c": "PSG",
            "Date_of_First_Entry_to_US__c": "First Entry",
            "Date_of_Most_Recent_US_Entry__c": "Last Entry",
            "Status_of_Last_Arrival__c": "Arrival Status",
            "Place_of_Last_Arrival__c": "Arrival Place",
            "Spouse_Name__c": "Spouse",
        }

        for field_key in _banner_fields:
            val = active.get(field_key)
            if val:
                label = _FIELD_LABELS.get(field_key)
                display_val = _format_date_value(str(val)) if field_key in _DATE_FIELDS else str(val)
                escaped = html_mod.escape(display_val)
                if label:
                    parts.append(f'<span class="sf-banner-field"><strong>{label}</strong> {escaped}</span>')
                else:
                    parts.append(f'<span class="sf-banner-field">{escaped}</span>')

        st.markdown(f'<div class="sf-banner">{"".join(parts)}</div>', unsafe_allow_html=True)

    return active
