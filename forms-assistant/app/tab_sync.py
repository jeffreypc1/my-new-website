"""Sync & History tab -- sync controls, diff table, and audit log viewer.

Provides bidirectional Salesforce sync UI (pull/push), a field-level diff
comparison table, and expandable history panels for sync and audit logs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

from app.sync_engine import pull_from_sf, push_to_sf, compute_diff, get_sync_log
from app.audit_log import get_recent_entries
from app.mapping_store import load_mapping_set
from app.pdf_form_store import get_all_forms

# Shared imports (monorepo)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
try:
    from shared.salesforce_client import load_active_client
except ImportError:
    def load_active_client() -> dict | None:  # type: ignore[misc]
        return None

SF_OBJECT_LABELS = {
    "Contact": "Contact",
    "Contact_Plus__c": "Contact Plus",
    "Contact_Plus_1__c": "Contact Plus 1",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _direction_label(direction: str) -> str:
    """Human-friendly label for sync direction."""
    return {"sf_to_form": "Pull", "form_to_sf": "Push"}.get(direction, direction)


def _status_color(status: str) -> str:
    """Return a CSS color for a sync/audit status value."""
    return {
        "success": "#2e7d32",
        "partial": "#e65100",
        "failed": "#c62828",
    }.get(status, "#5a6a85")


def _format_timestamp(ts: str) -> str:
    """Shorten an ISO timestamp for display."""
    # Show date + time (drop sub-second / timezone tail for readability)
    if "T" in ts:
        date_part, time_part = ts.split("T", 1)
        time_short = time_part[:8]  # HH:MM:SS
        return f"{date_part} {time_short}"
    return ts


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_sync_tab() -> None:
    """Render the full Sync & History tab."""

    sf_client: dict | None = st.session_state.get("sf_client")
    form_data: dict = st.session_state.get("form_data", {})
    selected_forms: list[str] = st.session_state.get("selected_forms", ["I-589"])
    form_id: str = selected_forms[0] if selected_forms else "I-589"

    # ── Top section: Sync Controls ──────────────────────────────────────
    st.markdown("### Sync Controls")

    if sf_client:
        client_name = sf_client.get("Name", sf_client.get("FirstName", ""))
        if not client_name:
            first = sf_client.get("FirstName", "")
            last = sf_client.get("LastName", "")
            client_name = f"{first} {last}".strip() or "Unknown"
        client_id = sf_client.get("Id", "N/A")
        st.markdown(
            f"**Active client:** {client_name} &nbsp;&bull;&nbsp; "
            f"<code style='font-size:0.82rem'>{client_id}</code>",
            unsafe_allow_html=True,
        )
    else:
        st.info(
            "No Salesforce client loaded. Pull a client from the Staff Dashboard "
            "to enable sync features."
        )

    st.caption(f"Form: **{form_id}**")

    # Buttons
    btn_col1, btn_col2 = st.columns(2)

    with btn_col1:
        pull_clicked = st.button(
            "Pull from SF",
            use_container_width=True,
            disabled=sf_client is None,
            key="btn_sync_pull",
        )
    with btn_col2:
        push_clicked = st.button(
            "Push to SF",
            use_container_width=True,
            type="primary",
            disabled=sf_client is None,
            key="btn_sync_push",
        )

    # ── Pull from SF ────────────────────────────────────────────────────
    if pull_clicked and sf_client:
        with st.spinner("Pulling from Salesforce..."):
            pulled = pull_from_sf(form_id, form_data)

        if not pulled:
            st.warning("No field values were returned from Salesforce.")
        else:
            st.success(f"Pulled {len(pulled)} field(s) from Salesforce.")

            # Show diff table so the user can choose Apply/Skip per field
            st.markdown("**Review pulled values:**")
            apply_keys: list[str] = []

            for idx, (field_key, sf_val) in enumerate(pulled.items()):
                current_val = form_data.get(field_key, "")
                cols = st.columns([3, 3, 2])
                with cols[0]:
                    st.text(field_key)
                with cols[1]:
                    st.text(str(sf_val))
                with cols[2]:
                    if st.checkbox(
                        "Apply",
                        value=True,
                        key=f"pull_apply_{idx}_{field_key}",
                    ):
                        apply_keys.append(field_key)

            if st.button("Apply Selected", key="btn_apply_pulled", type="primary"):
                applied = 0
                for key in apply_keys:
                    if key in pulled:
                        st.session_state.form_data[key] = pulled[key]
                        applied += 1
                st.success(f"Applied {applied} field(s) to form data.")
                st.rerun()

    # ── Push to SF ──────────────────────────────────────────────────────
    if push_clicked and sf_client:
        # Show confirmation before pushing
        st.session_state["_push_pending"] = True

    if st.session_state.get("_push_pending"):
        st.warning("You are about to push form data to Salesforce. This will overwrite existing field values.")
        conf_col1, conf_col2 = st.columns(2)
        with conf_col1:
            if st.button("Confirm Push", type="primary", key="btn_confirm_push"):
                st.session_state.pop("_push_pending", None)
                with st.spinner("Pushing to Salesforce..."):
                    pushed = push_to_sf(form_id, form_data)
                if pushed:
                    st.success(f"Successfully pushed {len(pushed)} field(s) to Salesforce.")
                else:
                    st.error("Push failed or no fields were eligible. Check the sync log for details.")
                st.rerun()
        with conf_col2:
            if st.button("Cancel", key="btn_cancel_push"):
                st.session_state.pop("_push_pending", None)
                st.rerun()

    # ── Middle section: Diff Table ──────────────────────────────────────
    st.markdown("---")
    st.markdown("### Field Diff Comparison")

    if sf_client:
        # Build sf_data from the client record, keyed by SF API field name
        mapping_set = load_mapping_set(form_id)
        if mapping_set and mapping_set.get_approved_mappings():
            # Collect SF field values from the loaded client record
            sf_data: dict = {}
            for m in mapping_set.get_approved_mappings():
                if m.sf_field and m.sf_field in sf_client:
                    sf_data[m.sf_field] = sf_client[m.sf_field]

            diffs = compute_diff(form_id, form_data, sf_data)

            if diffs:
                # Table header
                hdr_cols = st.columns([2.5, 1.5, 2.5, 2.5, 2])
                with hdr_cols[0]:
                    st.markdown("**Field**")
                with hdr_cols[1]:
                    st.markdown("**Object**")
                with hdr_cols[2]:
                    st.markdown("**Form Value**")
                with hdr_cols[3]:
                    st.markdown("**SF Value**")
                with hdr_cols[4]:
                    st.markdown("**Status**")

                differs_count = 0
                match_count = 0

                for i, row in enumerate(diffs):
                    row_cols = st.columns([2.5, 1.5, 2.5, 2.5, 2])
                    differs = row.get("differs", False)
                    if differs:
                        differs_count += 1
                    else:
                        match_count += 1

                    with row_cols[0]:
                        st.text(row.get("display_label", row.get("field_id", "")))
                    with row_cols[1]:
                        obj = row.get("sf_object", "Contact")
                        obj_label = SF_OBJECT_LABELS.get(obj, obj)
                        st.markdown(
                            f'<span style="font-size:0.82rem;">{obj_label}</span>',
                            unsafe_allow_html=True,
                        )
                    with row_cols[2]:
                        st.text(str(row.get("form_value", "")))
                    with row_cols[3]:
                        st.text(str(row.get("sf_value", "")))
                    with row_cols[4]:
                        if differs:
                            st.markdown(
                                '<span style="color:#e65100;font-weight:600;">Differs</span>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                '<span style="color:#2e7d32;font-weight:600;">Match</span>',
                                unsafe_allow_html=True,
                            )

                st.caption(
                    f"{match_count} matching, {differs_count} differing "
                    f"out of {len(diffs)} mapped field(s)."
                )

                # For differing fields, allow user to choose which value to keep
                differing_rows = [r for r in diffs if r.get("differs")]
                if differing_rows:
                    st.markdown("**Resolve differences:**")
                    for j, row in enumerate(differing_rows):
                        fid = row.get("field_id", "")
                        label = row.get("display_label", fid)
                        form_val = str(row.get("form_value", ""))
                        sf_val = str(row.get("sf_value", ""))

                        choice = st.radio(
                            f"{label}",
                            options=["Keep Form Value", "Use SF Value"],
                            horizontal=True,
                            key=f"diff_resolve_{j}_{fid}",
                        )
                        if choice == "Use SF Value":
                            # Stage the SF value; will be applied on button click
                            st.session_state.setdefault("_diff_overrides", {})[fid] = sf_val
                        else:
                            overrides = st.session_state.get("_diff_overrides", {})
                            overrides.pop(fid, None)

                    if st.button("Apply Resolutions", key="btn_apply_diff"):
                        overrides = st.session_state.pop("_diff_overrides", {})
                        applied = 0
                        for fid, val in overrides.items():
                            st.session_state.form_data[fid] = val
                            applied += 1
                        if applied:
                            st.success(f"Applied {applied} SF value(s) to form data.")
                        else:
                            st.info("No changes applied (all kept as form values).")
                        st.rerun()
            else:
                st.info("No approved mappings have data to compare.")
        else:
            st.info(
                "No approved field mappings found for this form. "
                "Map and approve fields in the Mappings tab first."
            )
    else:
        st.info("Load a Salesforce client to view field differences.")

    # ── Bottom section: History ─────────────────────────────────────────
    st.markdown("---")
    st.markdown("### History")

    # -- Sync Log --
    with st.expander("Sync Log", expanded=False):
        sync_entries = get_sync_log(limit=30)
        if not sync_entries:
            st.caption("No sync operations recorded yet.")
        else:
            for entry in sync_entries:
                direction = _direction_label(entry.direction)
                ts = _format_timestamp(entry.timestamp)
                color = _status_color(entry.status)
                fields_count = len(entry.fields_synced) if entry.fields_synced else 0

                header = (
                    f"**{ts}** &nbsp;|&nbsp; {direction} &nbsp;|&nbsp; "
                    f"`{entry.form_id}` &nbsp;|&nbsp; "
                    f"{fields_count} field(s) &nbsp;|&nbsp; "
                    f'<span style="color:{color};font-weight:600;">{entry.status}</span>'
                )
                st.markdown(header, unsafe_allow_html=True)

                if entry.error:
                    st.caption(f"Error: {entry.error}")

                # Expandable detail of which fields were synced
                if entry.fields_synced:
                    with st.expander(f"Fields detail ({fields_count})", expanded=False):
                        for sf_field, changes in entry.fields_synced.items():
                            if isinstance(changes, dict):
                                old_val = changes.get("old", "")
                                new_val = changes.get("new", "")
                                st.text(f"  {sf_field}: {old_val!r} -> {new_val!r}")
                            else:
                                st.text(f"  {sf_field}: {changes}")

    # -- Audit Log --
    with st.expander("Audit Log", expanded=False):
        audit_entries = get_recent_entries(limit=50)
        if not audit_entries:
            st.caption("No audit entries recorded yet.")
        else:
            # Action type filter
            all_actions = sorted({e.action for e in audit_entries})
            selected_actions = st.multiselect(
                "Filter by action type",
                options=all_actions,
                default=all_actions,
                key="audit_action_filter",
            )

            filtered = [e for e in audit_entries if e.action in selected_actions]

            if not filtered:
                st.caption("No entries match the selected filter.")
            else:
                for entry in filtered:
                    ts = _format_timestamp(entry.timestamp)
                    detail_str = ""
                    if entry.details:
                        detail_parts = [
                            f"{k}={v}" for k, v in entry.details.items()
                        ]
                        detail_str = " &nbsp;|&nbsp; " + ", ".join(detail_parts)

                    field_str = ""
                    if entry.field_id:
                        field_str = f" &nbsp;|&nbsp; field: `{entry.field_id}`"

                    form_str = ""
                    if entry.form_id:
                        form_str = f" &nbsp;|&nbsp; `{entry.form_id}`"

                    line = (
                        f"**{ts}** &nbsp;|&nbsp; "
                        f"**{entry.action}**"
                        f"{form_str}{field_str}{detail_str}"
                    )
                    st.markdown(line, unsafe_allow_html=True)
