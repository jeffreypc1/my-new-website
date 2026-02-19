"""Shared 'Add Documents' widget for creating LC_Task__c records."""

import re

import streamlit as st

from shared.salesforce_client import create_lc_task


def render_document_adder(tool_name: str) -> None:
    """Render a self-contained Add Documents widget.

    Provides a text area for adding one or more documents (one per line
    or comma-separated) to Salesforce as LC_Task__c records. Reads
    ``st.session_state.sf_client`` to obtain the Contact ID.

    Args:
        tool_name: Identifier used to namespace session-state keys
                   (e.g. ``"cover-letters"``).
    """
    active_client = st.session_state.get("sf_client")
    contact_id = active_client.get("Id", "") if active_client else ""

    if not contact_id:
        st.info("Pull a client to add documents.")
        return

    st.markdown("---")

    # Show result from previous submission (survives rerun)
    _result_key = f"_docadder_{tool_name}_result"
    if _result_key in st.session_state:
        _result = st.session_state.pop(_result_key)
        if _result.get("errors"):
            st.warning(f"Added {_result['created']} document(s), {_result['errors']} failed.")
            for _msg in _result.get("error_msgs", []):
                st.caption(f"Error: {_msg}")
        else:
            st.success(f"Added {_result['created']} document(s) to Salesforce.")

    bulk_key = f"_docadder_{tool_name}_bulk"
    # Clear text area if flagged by previous submission (must happen before widget renders)
    _clear_key = f"_docadder_{tool_name}_clear"
    if st.session_state.pop(_clear_key, False):
        st.session_state[bulk_key] = ""

    bulk_input = st.text_area(
        "Add documents",
        key=bulk_key,
        height=80,
        placeholder="e.g.:\nI-589 Application\nPassport Copy\nBirth Certificate",
        help="Enter one or more document names, one per line or separated by commas.",
    )
    if st.button(
        "Add to Salesforce",
        use_container_width=True,
        key=f"_docadder_{tool_name}_btn_bulk",
    ):
        raw = (bulk_input or "").strip()
        if not raw:
            return
        # Split on newlines and/or commas, deduplicate while preserving order
        items = list(dict.fromkeys(
            item.strip() for item in re.split(r"[,\n]+", raw) if item.strip()
        ))
        if not items:
            st.warning("No documents found. Enter one per line or separate with commas.")
            return

        created = 0
        error_msgs: list[str] = []
        with st.spinner(f"Adding {len(items)} document(s) to Salesforce..."):
            for item in items:
                try:
                    create_lc_task(contact_id, item)
                    created += 1
                except Exception as e:
                    error_msgs.append(f"{item}: {e}")

        # Store result in session state so it displays after rerun
        st.session_state[_result_key] = {"created": created, "errors": len(error_msgs), "error_msgs": error_msgs}
        # Flag text area to clear on next rerun (before widget renders)
        st.session_state[_clear_key] = True
        st.rerun()
