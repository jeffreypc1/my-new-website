"""Compact Box document sidebar for drafting tools.

Call render_box_sidebar() inside a `with st.sidebar:` block.
Returns silently if no client loaded, no Box folder ID, or box_sdk_gen
not importable.
"""

from __future__ import annotations

import time

import streamlit as st


def render_box_sidebar():
    """Render a compact Box file browser in the sidebar."""
    # Check for active client with Box folder
    sf = st.session_state.get("sf_client")
    if not sf:
        return

    folder_id_raw = sf.get("Box_Folder_ID__c", "") or ""
    if not folder_id_raw:
        return

    # Lazy import — silently skip if boxsdk not installed
    try:
        from shared.box_client import list_folder_items, get_folder_name, parse_folder_id
    except ImportError:
        return

    folder_id = parse_folder_id(folder_id_raw)

    st.markdown("#### Client Documents")

    # Reset nav stack when client changes
    client_id = sf.get("Customer_ID__c", "")
    if st.session_state.get("_bsb_client_id") != client_id:
        st.session_state._bsb_nav_stack = [folder_id]
        st.session_state._bsb_client_id = client_id
        st.session_state.pop("_bsb_cache", None)

    if "_bsb_nav_stack" not in st.session_state:
        st.session_state._bsb_nav_stack = [folder_id]

    current_folder = st.session_state._bsb_nav_stack[-1]

    # Back button
    if len(st.session_state._bsb_nav_stack) > 1:
        if st.button("Back", key="bsb_back", use_container_width=True):
            st.session_state._bsb_nav_stack.pop()
            st.session_state.pop("_bsb_cache", None)
            st.rerun()

    # Folder name
    try:
        fname = get_folder_name(current_folder)
        st.caption(fname)
    except Exception:
        st.caption(f"Folder {current_folder}")

    # Cached listing (60-second TTL)
    cache = st.session_state.get("_bsb_cache", {})
    cached = cache.get(current_folder)
    if cached and (time.time() - cached["ts"] < 60):
        items = cached["items"]
    else:
        try:
            items = list_folder_items(current_folder)
            cache[current_folder] = {"items": items, "ts": time.time()}
            st.session_state._bsb_cache = cache
        except Exception as e:
            st.error(f"Box error: {e}")
            return

    if not items:
        st.caption("Empty folder")
    else:
        def _badge(item: dict) -> str:
            ext = item.get("extension", "").lower()
            if item["type"] == "folder":
                return "DIR"
            if ext == "pdf":
                return "PDF"
            if ext in ("doc", "docx"):
                return "DOC"
            if ext in ("jpg", "jpeg", "png", "gif"):
                return "IMG"
            return "FILE"

        for idx, item in enumerate(items):
            badge = _badge(item)
            if item["type"] == "folder":
                c1, c2 = st.columns([5, 2])
                with c1:
                    st.markdown(f"`{badge}` {item['name']}")
                with c2:
                    if st.button("Open", key=f"bsb_open_{item['id']}_{idx}"):
                        st.session_state._bsb_nav_stack.append(item["id"])
                        st.session_state.pop("_bsb_cache", None)
                        st.rerun()
            else:
                st.markdown(
                    f"`{badge}` [{item['name']}]({item['web_url']})",
                    unsafe_allow_html=True,
                )

    # Link to full browser
    st.markdown(
        '<a href="http://localhost:8512" target="_self" '
        'style="font-size:0.75rem;color:#0066CC;">Full browser in Client Info &rarr;</a>',
        unsafe_allow_html=True,
    )
