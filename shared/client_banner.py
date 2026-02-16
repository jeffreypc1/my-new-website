"""Shared client info banner for all tool dashboards.

Renders a compact client info bar at the top of each tool page.
Loads the active client from the shared JSON file, with inline
option to pull a new client or refresh.

Usage in any tool's dashboard.py:
    from shared.client_banner import render_client_banner
    render_client_banner()  # call right after the nav bar
"""

from __future__ import annotations

import html as html_mod

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


def render_client_banner() -> dict | None:
    """Render a client info banner with inline pull/change.

    Reads the active client from the shared JSON file. If a ?client_id=
    query param is present, it takes priority (and updates the file).
    Shows a compact input row to pull or change clients.

    Returns the active client SF record dict, or None.
    """
    from shared.salesforce_client import (
        get_client,
        load_active_client,
        save_active_client,
    )

    # 1. Check query param (takes priority)
    params = st.query_params
    qp_cid = params.get("client_id", "")

    # 2. Load from shared file
    active = load_active_client()

    # 3. If query param has a different client, pull it
    if qp_cid and (not active or active.get("Customer_ID__c") != qp_cid):
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

    banner_cols = st.columns([2, 1, 1])
    with banner_cols[0]:
        new_cid = st.text_input(
            "Client #",
            value="",
            placeholder=f"Client # (current: {active.get('Customer_ID__c', 'none')})" if active else "Enter client number to pull",
            label_visibility="collapsed",
            key="_banner_client_id",
        )
    with banner_cols[1]:
        do_pull = st.button("Pull", use_container_width=True, type="primary", key="_banner_pull")
    with banner_cols[2]:
        do_refresh = st.button("Refresh", use_container_width=True, key="_banner_refresh",
                               disabled=not active)

    if do_pull and new_cid:
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

    if do_refresh and active:
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
