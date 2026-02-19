"""Shared 'Add Documents' widget for creating LC_Task__c records."""

import streamlit as st

from shared.salesforce_client import create_lc_task


def render_document_adder(tool_name: str) -> None:
    """Render a self-contained Add Documents widget.

    Provides a single-add text input and an expandable bulk-add section.
    Reads ``st.session_state.sf_client`` to obtain the Contact ID.

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

    # -- Single add --------------------------------------------------------
    input_key = f"_docadder_{tool_name}_input"
    cols = st.columns([5, 1])
    with cols[0]:
        new_desc = st.text_input(
            "New document",
            key=input_key,
            placeholder="Add a document...",
            label_visibility="collapsed",
        )
    with cols[1]:
        if st.button("Add", use_container_width=True, key=f"_docadder_{tool_name}_btn_add"):
            desc = (new_desc or "").strip()
            if desc:
                try:
                    create_lc_task(contact_id, desc)
                    st.toast(f"Added: {desc}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create task: {e}")

    # -- Bulk add ----------------------------------------------------------
    bulk_key = f"_docadder_{tool_name}_bulk"
    with st.expander("Bulk Add Documents"):
        bulk_input = st.text_area(
            "Paste comma-separated document names",
            key=bulk_key,
            height=80,
            placeholder="e.g.: I-589 Application, Passport Copy, Birth Certificate",
            label_visibility="collapsed",
        )
        if st.button(
            "Add All",
            use_container_width=True,
            key=f"_docadder_{tool_name}_btn_bulk",
        ):
            raw = (bulk_input or "").strip()
            if not raw:
                return
            items = list(dict.fromkeys(
                item.strip() for item in raw.split(",") if item.strip()
            ))
            if not items:
                st.warning("No documents found. Separate items with commas.")
                return

            created = 0
            errors = 0
            for item in items:
                try:
                    create_lc_task(contact_id, item)
                    created += 1
                except Exception:
                    errors += 1

            if errors:
                st.toast(f"Created {created} record(s), {errors} failed.", icon="⚠️")
            else:
                st.toast(f"Created {created} record(s).", icon="✅")
            st.rerun()
