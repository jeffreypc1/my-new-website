"""Reusable Box folder browser component.

Props-driven hierarchical browser that can be placed in a sidebar or main
area.  Supports two modes:

- **picker** -- multi-select files with checkboxes, batch-add via callback
- **viewer** -- click a file to open it in Box (web link)

Usage::

    from shared.box_folder_browser import render_box_folder_browser

    # Picker mode (Document Assembler style)
    render_box_folder_browser(
        root_folder_id="163957038141",
        mode="picker",
        on_select=lambda files: handle_selected(files),
        already_selected_ids={"12345", "67890"},
    )

    # Viewer mode (sidebar read-only browser)
    render_box_folder_browser(
        root_folder_id="163957038141",
        mode="viewer",
    )
"""

from __future__ import annotations

import html as html_mod
import time
from typing import Callable

import streamlit as st


# ---------------------------------------------------------------------------
# CSS (injected once per page)
# ---------------------------------------------------------------------------

_BOX_BROWSER_CSS = """\
.box-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 13px;
    cursor: default;
}
.box-item:hover { background: #f1f5f9; }
.box-folder {
    color: #1e40af;
    cursor: pointer;
    font-weight: 500;
}
.box-ext {
    font-size: 9px;
    font-weight: 600;
    padding: 1px 5px;
    border-radius: 3px;
    text-transform: uppercase;
}
.box-ext-pdf { background: #fee2e2; color: #dc2626; }
.box-ext-img { background: #dbeafe; color: #2563eb; }
.box-ext-doc { background: #e0e7ff; color: #4338ca; }
.box-ext-other { background: #f1f5f9; color: #64748b; }
"""


def _inject_css() -> None:
    """Inject Box browser CSS once per Streamlit page."""
    if not st.session_state.get("_box_browser_css_injected"):
        st.markdown(f"<style>{_BOX_BROWSER_CSS}</style>", unsafe_allow_html=True)
        st.session_state["_box_browser_css_injected"] = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ext_badge_html(ext: str) -> str:
    """Return an HTML span for a coloured file-extension badge."""
    ext = ext.lower()
    if ext == "pdf":
        cls = "box-ext-pdf"
    elif ext in ("jpg", "jpeg", "png", "tiff", "tif", "bmp", "webp", "gif"):
        cls = "box-ext-img"
    elif ext in ("doc", "docx"):
        cls = "box-ext-doc"
    else:
        cls = "box-ext-other"
    return f'<span class="box-ext {cls}">{html_mod.escape(ext)}</span>'


def _get_folder_items_cached(folder_id: str, cache_key: str) -> list[dict]:
    """Folder listing with 60-second in-session cache."""
    from shared.box_client import list_folder_items

    cache: dict = st.session_state.get(cache_key, {})
    now = time.time()
    if folder_id in cache and now - cache[folder_id]["ts"] < 60:
        return cache[folder_id]["items"]

    items = list_folder_items(folder_id)
    cache[folder_id] = {"items": items, "ts": now}
    st.session_state[cache_key] = cache
    return items


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_box_folder_browser(
    root_folder_id: str,
    *,
    mode: str = "picker",
    on_select: Callable[[list[dict]], None] | None = None,
    already_selected_ids: set[str] | None = None,
    key_prefix: str = "_box",
    show_header: bool = True,
    add_button_label: str = "Add Selected",
    header_label: str = "Box Folder Browser",
) -> None:
    """Render a hierarchical Box folder browser.

    Parameters
    ----------
    root_folder_id:
        Box folder ID (numeric string) for the root of the tree.
    mode:
        ``"picker"`` -- checkboxes + batch-add; calls *on_select*.
        ``"viewer"`` -- files rendered as links opening in Box.
    on_select:
        Callback receiving a ``list[dict]`` of selected file items when the
        user clicks the add button (picker mode only).  Each dict has keys:
        ``id, name, type, extension, web_url, size, modified_at``.
    already_selected_ids:
        Set of file IDs that have already been added.  Shown greyed-out
        with a checkmark in picker mode.
    key_prefix:
        Namespace for session-state keys to avoid collisions when the
        component is rendered more than once on the same page.
    show_header:
        If ``True``, renders a header above the browser.
    add_button_label:
        Label for the batch-add button (picker mode).
    header_label:
        Text displayed as the header when *show_header* is ``True``.
    """
    _inject_css()

    # Lazy import so tools without boxsdk can still import this module
    try:
        from shared.box_client import list_folder_items as _lfi  # noqa: F401
    except ImportError:
        st.warning("Box SDK not available.")
        return

    if already_selected_ids is None:
        already_selected_ids = set()

    # -- Session state keys (namespaced) ------------------------------------
    nav_key = f"{key_prefix}_nav"
    cache_key = f"{key_prefix}_cache"

    if nav_key not in st.session_state or not st.session_state[nav_key]:
        st.session_state[nav_key] = [root_folder_id]

    # Reset nav stack if root folder changes (e.g. new client)
    if st.session_state[nav_key][0] != root_folder_id:
        st.session_state[nav_key] = [root_folder_id]
        st.session_state.pop(cache_key, None)

    nav: list[str] = st.session_state[nav_key]
    current_folder = nav[-1]

    # -- Header -------------------------------------------------------------
    if show_header:
        st.markdown(f"#### {header_label}")

    # -- Back button --------------------------------------------------------
    if len(nav) > 1:
        if st.button("\u2190 Back", key=f"{key_prefix}_back"):
            nav.pop()
            st.rerun()

    # -- Folder listing -----------------------------------------------------
    try:
        items = _get_folder_items_cached(current_folder, cache_key)
    except Exception as e:
        st.error(f"Error loading folder: {e}")
        items = []

    folders = [i for i in items if i["type"] == "folder"]
    files = [i for i in items if i["type"] != "folder"]

    # -- Folders ------------------------------------------------------------
    for folder in folders:
        if st.button(
            f"\U0001F4C1 {folder['name']}",
            key=f"{key_prefix}_nav_{folder['id']}",
        ):
            nav.append(folder["id"])
            st.rerun()

    # -- Files --------------------------------------------------------------
    if not files:
        if not folders:
            st.caption("Empty folder")
        return

    st.markdown("---")
    st.caption(f"{len(files)} file(s)")

    if mode == "picker":
        _render_picker(files, already_selected_ids, on_select, key_prefix, add_button_label)
    else:
        _render_viewer(files, key_prefix)


# ---------------------------------------------------------------------------
# Mode renderers
# ---------------------------------------------------------------------------

def _render_picker(
    files: list[dict],
    already_selected_ids: set[str],
    on_select: Callable[[list[dict]], None] | None,
    key_prefix: str,
    add_button_label: str,
) -> None:
    """Picker mode: checkboxes, already-added indicators, batch-add button."""
    checked: list[dict] = []

    for f in files:
        ext = f.get("extension", "") or ""
        if f["id"] in already_selected_ids:
            st.markdown(
                f"<div class='box-item' style='opacity:0.5'>"
                f"\u2705 {_ext_badge_html(ext)} {html_mod.escape(f['name'])}</div>",
                unsafe_allow_html=True,
            )
        else:
            if st.checkbox(f["name"], key=f"{key_prefix}_chk_{f['id']}"):
                checked.append(f)

    if checked and on_select is not None:
        if st.button(add_button_label, type="primary", key=f"{key_prefix}_add_sel"):
            on_select(checked)
            st.rerun()


def _render_viewer(files: list[dict], key_prefix: str) -> None:
    """Viewer mode: files rendered as clickable links to Box."""
    for f in files:
        ext = f.get("extension", "") or ""
        badge = _ext_badge_html(ext) if ext else ""
        url = f.get("web_url", "")
        name = html_mod.escape(f["name"])
        if url:
            st.markdown(
                f'<div class="box-item">{badge} '
                f'<a href="{url}" target="_blank" style="color:#1e40af;text-decoration:none;">'
                f'{name}</a></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="box-item">{badge} {name}</div>',
                unsafe_allow_html=True,
            )
