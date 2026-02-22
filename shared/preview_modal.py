"""Reusable full-screen preview / edit dialog for document tools.

Usage::

    from shared.preview_modal import show_preview_modal

    if should_open:
        show_preview_modal(
            title="Brief Preview",
            preview_html=html_string,
            plain_text=plain_string,
            tool_name="brief-builder",
        )
"""

from __future__ import annotations

from typing import Callable

import streamlit as st


def show_preview_modal(
    title: str,
    preview_html: str,
    plain_text: str,
    tool_name: str,
    edit_key: str = "_preview_edited_text",
    on_save: Callable[[str], None] | None = None,
) -> None:
    """Open a ``@st.dialog`` with HTML preview + editable text area.

    Parameters
    ----------
    title:
        Heading displayed inside the dialog.
    preview_html:
        Rendered HTML shown in a ``.preview-panel`` div.  Skipped when empty.
    plain_text:
        Initial value for the editable text area.
    tool_name:
        Used to namespace widget keys so multiple tools don't collide.
    edit_key:
        Session-state key where saved text is stored (default
        ``"_preview_edited_text"``).
    on_save:
        Optional callback receiving the edited text *before* rerun.
    """

    @st.dialog("Document Preview", width="large")
    def _dialog():
        st.markdown(f"**{title}**")

        if preview_html:
            st.markdown(
                f'<div class="preview-panel">{preview_html}</div>',
                unsafe_allow_html=True,
            )
            st.markdown("---")

        st.markdown("**Edit Final Text**")
        _ta_key = f"_pm_edit_{tool_name}"
        st.text_area(
            "Editable preview text",
            value=plain_text,
            height=500,
            key=_ta_key,
            label_visibility="collapsed",
        )

        btn_cols = st.columns(2)
        with btn_cols[0]:
            if st.button("Save Changes", type="primary", use_container_width=True):
                edited = st.session_state.get(_ta_key, "")
                st.session_state[edit_key] = edited
                if on_save is not None:
                    on_save(edited)
                st.rerun()
        with btn_cols[1]:
            if st.button("Close", use_container_width=True):
                st.rerun()

    _dialog()
