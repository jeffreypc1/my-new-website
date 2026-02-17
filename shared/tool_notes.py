"""Persistent review notes component for tool sidebars."""

from __future__ import annotations

import streamlit as st

from shared.config_store import load_config, save_config

_CONFIG_NAME = "tool-notes"
_RESPONSE_CONFIG_NAME = "tool-notes-responses"


def _check_sidebar_for_tool(tool_name: str) -> None:
    """Hide the sidebar via CSS if the admin panel has it turned off for this tool."""
    settings = load_config("global-settings") or {}
    sidebars = settings.get("sidebars", {})
    if not sidebars.get(tool_name, True):
        st.markdown(
            "<style>"
            '[data-testid="stSidebar"] { display: none !important; }'
            '[data-testid="stSidebarContent"] { display: none !important; }'
            '[data-testid="stSidebarUserContent"] { display: none !important; }'
            "</style>",
            unsafe_allow_html=True,
        )


def render_tool_notes(tool_name: str) -> None:
    """Render a Review Notes text area in the sidebar with save button."""
    _check_sidebar_for_tool(tool_name)
    st.divider()
    st.markdown("#### Review Notes")
    notes = (load_config(_CONFIG_NAME) or {}).get(tool_name, "")
    updated = st.text_area(
        "Notes",
        value=notes,
        key=f"_review_notes_{tool_name}",
        height=120,
        placeholder="Jot down feedback or notes for this tool...",
        label_visibility="collapsed",
    )
    if st.button("Save Notes", key=f"_save_notes_{tool_name}", use_container_width=True):
        all_notes = load_config(_CONFIG_NAME) or {}
        all_notes[tool_name] = updated
        save_config(_CONFIG_NAME, all_notes)
        st.toast("Notes saved!")

    # Claude's response to the notes
    response_data = (load_config(_RESPONSE_CONFIG_NAME) or {}).get(tool_name, {})
    if response_data:
        st.markdown("#### Claude's Response")
        st.caption(response_data.get("timestamp", ""))
        st.info(response_data.get("response", ""), icon="\u2709\ufe0f")
