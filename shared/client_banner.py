"""Shared client info banner for all tool dashboards.

Renders a compact client info bar at the top of each tool page.
Loads the active client from the shared JSON file, with inline
option to pull a new client or refresh. Includes a "Files" button
that opens a Box folder browser dialog when the client has a
Box_Folder_ID__c.

Usage in any tool's dashboard.py:
    from shared.client_banner import render_client_banner
    render_client_banner()  # call right after the nav bar
"""

from __future__ import annotations

import html as html_mod
import time

import streamlit as st


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
</style>
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

    if not _sf_available:
        st.caption("Salesforce unavailable — showing cached data.")

    has_box = bool(active and (active.get("Box_Folder_ID__c") or ""))

    banner_cols = st.columns([3, 1, 1, 1])
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

    # Render info bar
    if active:
        parts = [f'<span class="sf-banner-name">{html_mod.escape(active.get("Name", ""))}</span>']
        parts.append('<span class="sf-banner-sep">|</span>')

        if active.get("Customer_ID__c"):
            parts.append(f'<span class="sf-banner-field"><strong>#</strong>{html_mod.escape(str(active["Customer_ID__c"]))}</span>')
        if active.get("A_Number__c"):
            parts.append(f'<span class="sf-banner-field"><strong>A#</strong> {html_mod.escape(str(active["A_Number__c"]))}</span>')
        if active.get("Country__c"):
            parts.append(f'<span class="sf-banner-field">{html_mod.escape(str(active["Country__c"]))}</span>')
        if active.get("Best_Language__c"):
            parts.append(f'<span class="sf-banner-field">{html_mod.escape(str(active["Best_Language__c"]))}</span>')
        if active.get("Immigration_Status__c"):
            parts.append(f'<span class="sf-banner-field">{html_mod.escape(str(active["Immigration_Status__c"]))}</span>')

        st.markdown(f'<div class="sf-banner">{"".join(parts)}</div>', unsafe_allow_html=True)

    return active
