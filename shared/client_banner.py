"""Shared client info banner for all tool dashboards.

Renders a read-only client info ribbon at the top of each tool page.
Loads the active client from the shared JSON file; if a ?client_id=
query param is present it pulls that client on first visit.
Client changes are made on the home page dashboard.

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


def _get_banner_font_size() -> int:
    """Load banner font size from global settings (default 13px)."""
    try:
        from shared.config_store import load_config
        settings = load_config("global-settings") or {}
        return settings.get("banner_font_size", 13)
    except Exception:
        return 13


def _show_pull_bar() -> bool:
    """Return True if the pull bar is enabled in global settings."""
    try:
        from shared.config_store import load_config
        settings = load_config("global-settings") or {}
        return bool(settings.get("show_pull_bar", False))
    except Exception:
        return False


def _banner_css() -> str:
    """Generate banner CSS with configurable font size."""
    _size = _get_banner_font_size()
    _name_size = _size + 1
    return f"""
<style>
.sf-banner {{
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px 20px;
    padding: 8px 16px;
    margin: -0.5rem 0 0.8rem 0;
    background: #f0f4ff;
    border: 1px solid #d0daf0;
    border-radius: 8px;
    font-size: {_size}px;
    color: #3a4a6b;
}}
.sf-banner-name {{
    font-weight: 700;
    color: #1a2744;
    font-size: {_name_size}px;
}}
.sf-banner-sep {{
    color: #c0c8d8;
}}
.sf-banner-field {{
    color: #5a6a85;
}}
.sf-banner-field strong {{
    color: #1a2744;
    font-weight: 600;
}}
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



# -- Files dialog (shown when pull bar is enabled) ----------------------------

@st.dialog("Client Files", width="large")
def _show_client_files(client_record: dict):
    """Dialog with two tabs: Documents (LC_Task__c CRUD) and Box Files."""
    client_name = client_record.get("Name", "Client")
    contact_sf_id = client_record.get("Id", "")
    folder_id = client_record.get("Box_Folder_ID__c", "")

    tab_docs, tab_box = st.tabs(["Documents", "Box Files"])

    # ── Documents tab ────────────────────────────────────────────────────────
    with tab_docs:
        if not contact_sf_id:
            st.info("No Salesforce Contact ID available for this client.")
        else:
            sf_tasks: list[dict] = []
            try:
                from shared.salesforce_client import get_lc_tasks
                sf_tasks = get_lc_tasks(contact_sf_id)
            except Exception:
                sf_tasks = []

            pending_deletes: list[str] = list(
                st.session_state.get("_files_dlg_pending_delete", [])
            )

            if sf_tasks:
                has_edits = False
                for task in sf_tasks:
                    task_id = task.get("Id", "")
                    task_label = task.get("For__c") or task.get("Name") or "Untitled"
                    is_pending_delete = task_id in pending_deletes
                    edit_key = f"_files_dlg_edit_{task_id}"

                    if is_pending_delete:
                        st.markdown(f"~~{html_mod.escape(task_label)}~~")
                        undo_cols = st.columns([8, 1])
                        with undo_cols[1]:
                            if st.button("Undo", key=f"_files_dlg_undo_{task_id}",
                                         use_container_width=True):
                                pending_deletes.remove(task_id)
                                st.session_state._files_dlg_pending_delete = pending_deletes
                                st.rerun()
                    else:
                        tc = st.columns([8, 0.5])
                        with tc[0]:
                            st.text_input(
                                "Edit document name",
                                value=st.session_state.get(edit_key, task_label),
                                key=edit_key,
                                label_visibility="collapsed",
                            )
                        with tc[1]:
                            if st.button("X", key=f"_files_dlg_del_{task_id}",
                                         help="Mark for deletion"):
                                pending_deletes.append(task_id)
                                st.session_state._files_dlg_pending_delete = pending_deletes
                                st.rerun()

                        edited_val = st.session_state.get(edit_key, "").strip()
                        if edited_val and edited_val != task_label:
                            has_edits = True

                has_changes = has_edits or len(pending_deletes) > 0
                if has_changes:
                    badge_parts: list[str] = []
                    edit_count = sum(
                        1 for t in sf_tasks
                        if t.get("Id", "") not in pending_deletes
                        and st.session_state.get(
                            f"_files_dlg_edit_{t.get('Id', '')}", ""
                        ).strip()
                        != (t.get("For__c") or t.get("Name") or "Untitled")
                        and st.session_state.get(
                            f"_files_dlg_edit_{t.get('Id', '')}", ""
                        ) != ""
                    )
                    if edit_count:
                        badge_parts.append(
                            f"{edit_count} edit{'s' if edit_count != 1 else ''}"
                        )
                    if pending_deletes:
                        del_count = len(pending_deletes)
                        badge_parts.append(
                            f"{del_count} deletion{'s' if del_count != 1 else ''}"
                        )
                    st.caption(" | ".join(badge_parts))

                    if st.button("Save Changes to Salesforce", type="primary",
                                 use_container_width=True, key="_files_dlg_save_all"):
                        save_errors: list[str] = []
                        try:
                            from shared.salesforce_client import update_lc_task, delete_lc_task
                            for t in sf_tasks:
                                tid = t.get("Id", "")
                                if tid in pending_deletes:
                                    continue
                                orig = t.get("For__c") or t.get("Name") or "Untitled"
                                new_val = st.session_state.get(f"_files_dlg_edit_{tid}", "").strip()
                                if new_val and new_val != orig:
                                    try:
                                        update_lc_task(tid, new_val)
                                    except Exception as e:
                                        save_errors.append(f"Edit '{new_val}': {e}")
                            for tid in pending_deletes:
                                try:
                                    delete_lc_task(tid)
                                except Exception as e:
                                    save_errors.append(f"Delete {tid}: {e}")
                            st.session_state._files_dlg_pending_delete = []
                            for t in sf_tasks:
                                ek = f"_files_dlg_edit_{t.get('Id', '')}"
                                if ek in st.session_state:
                                    del st.session_state[ek]
                            if save_errors:
                                st.warning(f"Saved with {len(save_errors)} error(s): {'; '.join(save_errors)}")
                            else:
                                st.success("Changes saved to Salesforce.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Save failed: {e}")
            else:
                st.caption("No documents found for this client.")

            st.markdown("---")
            add_cols = st.columns([5, 1])
            with add_cols[0]:
                new_task_desc = st.text_input(
                    "New document", key="_files_dlg_new_task",
                    placeholder="Add a document...", label_visibility="collapsed",
                )
            with add_cols[1]:
                if st.button("Add", use_container_width=True, key="_files_dlg_add") and new_task_desc:
                    try:
                        from shared.salesforce_client import create_lc_task
                        create_lc_task(contact_sf_id, new_task_desc.strip())
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create: {e}")

            with st.expander("Bulk Add Documents"):
                mass_input = st.text_area(
                    "Paste comma-separated document names", key="_files_dlg_mass",
                    height=80, placeholder="e.g.: I-589 Application, Passport Copy, Birth Certificate",
                    label_visibility="collapsed",
                )
                if st.button("Upload All", use_container_width=True, key="_files_dlg_mass_btn") and mass_input.strip():
                    items = [item.strip() for item in mass_input.split(",") if item.strip()]
                    if not items:
                        st.warning("No documents found. Separate items with commas.")
                    else:
                        created = errors = 0
                        try:
                            from shared.salesforce_client import create_lc_task
                            for item in items:
                                try:
                                    create_lc_task(contact_sf_id, item)
                                    created += 1
                                except Exception:
                                    errors += 1
                            if errors:
                                st.warning(f"Created {created} record(s), {errors} failed.")
                            else:
                                st.success(f"Created {created} record(s) in Salesforce.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to upload: {e}")

    # ── Box Files tab ────────────────────────────────────────────────────────
    with tab_box:
        if not folder_id:
            st.info("No Box folder configured for this client. "
                    "Set the Box_Folder_ID__c field in Salesforce to enable file browsing.")
        else:
            try:
                from shared.box_client import list_folder_items, get_folder_name, parse_folder_id
            except ImportError:
                st.error("Box client not available. Check that box-sdk-gen is installed.")
                return

            root_id = parse_folder_id(folder_id)
            prev_client = st.session_state.get("_box_dlg_client", "")
            current_client = client_record.get("Customer_ID__c", "")
            if prev_client != current_client:
                st.session_state._box_dlg_nav = [root_id]
                st.session_state._box_dlg_client = current_client
                st.session_state.pop("_box_dlg_cache", None)

            if "_box_dlg_nav" not in st.session_state:
                st.session_state._box_dlg_nav = [root_id]

            current = st.session_state._box_dlg_nav[-1]

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

            cache = st.session_state.get("_box_dlg_cache", {})
            cached = cache.get(current)
            if cached and (time.time() - cached["ts"] < 60):
                box_items = cached["items"]
            else:
                try:
                    with st.spinner("Loading files..."):
                        box_items = list_folder_items(current)
                    cache[current] = {"items": box_items, "ts": time.time()}
                    st.session_state._box_dlg_cache = cache
                except Exception as e:
                    st.error(f"Box error: {e}")
                    return

            if not box_items:
                st.caption("Empty folder")
            else:
                for idx, item in enumerate(box_items):
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

            box_url = f"https://app.box.com/folder/{root_id}"
            st.markdown("---")
            st.markdown(
                f"[Open folder in Box]({box_url}) &nbsp;|&nbsp; "
                f"[Full browser in Client Info](http://localhost:8512)",
                unsafe_allow_html=True,
            )


# -- Email dialog (shown when pull bar is enabled) ---------------------------

@st.dialog("Send Email", width="large")
def _show_email_compose(client_record: dict, sf_available: bool):
    """Dialog for composing and sending an email via Salesforce."""
    from shared.config_store import load_config

    client_name = client_record.get("Name", "Client")
    client_email = client_record.get("Email", "")

    st.markdown(f"**To:** {client_name} ({client_email})")

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
            "From (sender)", range(len(staff_options)),
            format_func=lambda i: staff_options[i], key="_email_sender",
        )
        sender_name = f"{staff[sender_idx].get('first_name', '')} {staff[sender_idx].get('last_name', '')}".strip()
    else:
        st.warning("No staff members configured. Add staff in Admin Panel > Integrations > Staff Directory.")
        sender_name = ""

    templates = load_config("email-templates") or []
    template_names = ["(none)"] + [t.get("name", f"Template {i}") for i, t in enumerate(templates)]
    selected_tpl = st.selectbox("Template", template_names, key="_email_template")

    init_subject = ""
    init_body = ""
    if selected_tpl != "(none)":
        tpl_idx = template_names.index(selected_tpl) - 1
        if 0 <= tpl_idx < len(templates):
            tpl = templates[tpl_idx]
            try:
                from shared.email_service import merge_template
                init_subject, init_body = merge_template(tpl.get("subject", ""), tpl.get("body", ""), client_record)
            except ImportError:
                init_subject = tpl.get("subject", "")
                init_body = tpl.get("body", "")

    if "_email_last_tpl" not in st.session_state or st.session_state._email_last_tpl != selected_tpl:
        st.session_state._email_last_tpl = selected_tpl
        st.session_state._email_subj_val = init_subject
        st.session_state._email_body_val = init_body
        st.rerun()

    subject = st.text_input("Subject", value=st.session_state.get("_email_subj_val", init_subject), key="_email_subject")
    body = st.text_area("Body", value=st.session_state.get("_email_body_val", init_body), key="_email_body", height=250)

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
    """Render a read-only client info ribbon.

    Reads the active client from the shared JSON file. If a ?client_id=
    query param is present, it pulls that client on first visit.
    Client changes are made on the home page dashboard.

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

    # 1. Check query param
    qp_cid = st.query_params.get("client_id", "")

    # 2. Load from shared file
    active = load_active_client()

    # 3. Consume query param ONCE per value.  We track the last-consumed
    #    param in session state so it won't keep overriding manual pulls
    #    on every rerun (the param stays in the URL but is ignored after
    #    the first consumption).  Avoids `del st.query_params[...]` which
    #    triggers an extra Streamlit rerun and can disrupt widget state.
    _qp_consumed = st.session_state.get("_banner_qp_consumed", "")
    if _sf_available and qp_cid and qp_cid != _qp_consumed:
        st.session_state._banner_qp_consumed = qp_cid
        if not active or active.get("Customer_ID__c") != qp_cid:
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

    # 5. Render banner
    st.markdown(_banner_css(), unsafe_allow_html=True)
    _components.html(_SIDEBAR_TOGGLE_HTML, height=28)

    if not _sf_available:
        st.caption("Salesforce unavailable — showing cached data.")

    # 6. Optional pull bar (controlled by Admin Panel toggle)
    if _show_pull_bar():
        has_client = bool(active)
        has_email = bool(active and (active.get("Email") or ""))

        if "_banner_client_id" not in st.session_state:
            st.session_state["_banner_client_id"] = ""
        if st.session_state.pop("_banner_clear_input", False):
            st.session_state["_banner_client_id"] = ""

        banner_cols = st.columns([3, 1, 1, 1])
        with banner_cols[0]:
            new_cid = st.text_input(
                "Client #",
                placeholder=(
                    f"Client # (current: {active.get('Customer_ID__c', 'none')})"
                    if active
                    else "Enter client number to pull"
                ),
                label_visibility="collapsed",
                key="_banner_client_id",
            )
        with banner_cols[1]:
            do_pull = st.button(
                "Pull", use_container_width=True, type="primary",
                key="_banner_pull", disabled=not _sf_available,
            )
        with banner_cols[2]:
            do_files = st.button(
                "Files", use_container_width=True,
                key="_banner_files", disabled=not has_client,
            )
        with banner_cols[3]:
            do_email = st.button(
                "Email", use_container_width=True,
                key="_banner_email", disabled=not has_email or not _sf_available,
            )

        # Pull logic
        _prev_cid = st.session_state.get("_banner_last_pulled", "")
        _entered_new = bool(new_cid.strip() and new_cid.strip() != _prev_cid)

        if (do_pull or _entered_new) and _sf_available:
            cid_to_pull = (
                new_cid.strip()
                if new_cid.strip()
                else (active.get("Customer_ID__c", "") if active else "")
            )
            if cid_to_pull:
                try:
                    record = get_client(cid_to_pull)
                    if record:
                        save_active_client(record)
                        st.session_state.sf_client = record
                        st.session_state._banner_last_pulled = cid_to_pull
                        st.session_state._banner_clear_input = True
                        active = record
                        st.rerun()
                    else:
                        st.warning(f"No client found for #{cid_to_pull}")
                        st.session_state._banner_last_pulled = cid_to_pull
                except Exception as e:
                    st.error(f"Salesforce error: {e}")
            else:
                st.info("Enter a client number to pull.")

        if do_files and active:
            _show_client_files(active)
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
