"""Admin recipient address book manager.

Full CRUD for the recipient address book used by the Filing Assembler
and other tools. Reads/writes via cover-letters/app/templates.py functions.
"""

import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Reuse existing data layer from cover-letters/app/templates.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "cover-letters"))
from app.templates import (
    RECIPIENT_CATEGORIES,
    get_recipient_addresses,
    save_recipient_addresses,
)


def render_recipient_manager() -> None:
    """Render the admin recipient address CRUD UI."""

    addresses = get_recipient_addresses()

    # Store working copy in session state so edits survive reruns
    if "_recip_mgr_addresses" not in st.session_state:
        st.session_state["_recip_mgr_addresses"] = [dict(a) for a in addresses]

    working: list[dict] = st.session_state["_recip_mgr_addresses"]

    # -- Add New Address --
    with st.expander("Add New Address", icon=":material/add:"):
        new_name = st.text_input("Name", key="_recip_new_name", placeholder="e.g. USCIS Dallas Field Office")
        new_cat = st.selectbox("Category", RECIPIENT_CATEGORIES, key="_recip_new_cat")
        new_addr = st.text_area(
            "Address",
            key="_recip_new_addr",
            height=100,
            placeholder="Full mailing address\n(one line per line)",
        )
        new_sal = st.text_input(
            "Salutation",
            key="_recip_new_sal",
            placeholder="Dear Sir or Madam:",
        )
        if st.button("Add Address", key="_recip_add_btn", type="secondary"):
            if not new_name.strip():
                st.warning("Name is required.")
            else:
                entry = {
                    "id": new_name.strip().lower().replace(" ", "_").replace("(", "").replace(")", ""),
                    "name": new_name.strip(),
                    "category": new_cat,
                    "address": new_addr.strip(),
                    "salutation": new_sal.strip() or "Dear Sir or Madam:",
                }
                working.append(entry)
                st.session_state["_recip_mgr_addresses"] = working
                # Clear the input fields
                for k in ("_recip_new_name", "_recip_new_addr", "_recip_new_sal"):
                    st.session_state.pop(k, None)
                st.rerun()

    st.markdown("---")

    # -- List existing addresses grouped by category --
    if not working:
        st.info("No recipient addresses configured.")
    else:
        to_delete: list[int] = []

        # Group by category (preserve order)
        seen_cats: list[str] = []
        for addr in working:
            cat = addr.get("category", "Other")
            if cat not in seen_cats:
                seen_cats.append(cat)

        for cat in seen_cats:
            st.markdown(f"#### {cat}")
            for idx, addr in enumerate(working):
                if addr.get("category", "Other") != cat:
                    continue
                with st.expander(addr.get("name", "(unnamed)"), expanded=False):
                    cols = st.columns([3, 1])
                    with cols[0]:
                        working[idx]["name"] = st.text_input(
                            "Name", value=addr.get("name", ""), key=f"_recip_name_{idx}",
                        )
                        working[idx]["category"] = st.selectbox(
                            "Category",
                            RECIPIENT_CATEGORIES,
                            index=RECIPIENT_CATEGORIES.index(addr.get("category", "Other"))
                            if addr.get("category", "Other") in RECIPIENT_CATEGORIES
                            else len(RECIPIENT_CATEGORIES) - 1,
                            key=f"_recip_cat_{idx}",
                        )
                        working[idx]["address"] = st.text_area(
                            "Address", value=addr.get("address", ""), key=f"_recip_addr_{idx}",
                            height=100,
                        )
                        working[idx]["salutation"] = st.text_input(
                            "Salutation", value=addr.get("salutation", ""), key=f"_recip_sal_{idx}",
                        )
                    with cols[1]:
                        st.markdown("")
                        st.markdown("")
                        if st.button(
                            "Delete",
                            key=f"_recip_del_{idx}",
                            type="secondary",
                            use_container_width=True,
                        ):
                            to_delete.append(idx)

        # Process deletes
        if to_delete:
            for idx in sorted(to_delete, reverse=True):
                working.pop(idx)
            st.session_state["_recip_mgr_addresses"] = working
            st.rerun()

    st.markdown("---")

    # -- Save / Reload --
    col_save, col_reload = st.columns(2)
    with col_save:
        if st.button("Save All Changes", type="primary", key="_recip_save", use_container_width=True):
            save_recipient_addresses(working)
            st.toast("Recipient addresses saved!")
    with col_reload:
        if st.button("Reload from Disk", key="_recip_reload", use_container_width=True):
            fresh = get_recipient_addresses()
            st.session_state["_recip_mgr_addresses"] = [dict(a) for a in fresh]
            st.toast("Reloaded from saved data.")
            st.rerun()
