"""Compact Box document sidebar for drafting tools.

Call render_box_sidebar() inside a `with st.sidebar:` block.
Returns silently if no client loaded, no Box folder ID, or box_sdk_gen
not importable.

Thin wrapper around shared.box_folder_browser for backward compatibility.
"""

from __future__ import annotations

import streamlit as st


def render_box_sidebar():
    """Render a compact Box file browser in the sidebar (viewer mode)."""
    # Check for active client with Box folder
    sf = st.session_state.get("sf_client")
    if not sf:
        return

    folder_id_raw = sf.get("Box_Folder_Id__c", "") or ""
    if not folder_id_raw:
        return

    # Lazy import — silently skip if boxsdk not installed
    try:
        from shared.box_client import parse_folder_id
        from shared.box_folder_browser import render_box_folder_browser
    except ImportError:
        return

    folder_id = parse_folder_id(folder_id_raw)

    render_box_folder_browser(
        folder_id,
        mode="viewer",
        key_prefix="_bsb",
        header_label="Client Documents",
    )

    # Link to full browser
    st.markdown(
        '<a href="http://localhost:8512" target="_self" '
        'style="font-size:0.75rem;color:#0066CC;">Full browser in Client Info &rarr;</a>',
        unsafe_allow_html=True,
    )
