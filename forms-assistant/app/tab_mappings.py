"""Field Mappings tab — section-grouped mapping review with search, inline
override, and linked/unlinked visual indicators.

Displays SF field mappings for a selected form grouped by form section
(e.g. "Part A.I - Information About You") with:
  - Search/filter bar
  - Per-row linked icon, override selector (type-filtered), and sync toggle
  - Bulk approve and re-map actions
  - Create-new-field flow for unmatched fields

Exports a single entry point: ``render_mappings_tab()``.
"""

from __future__ import annotations

import html as html_mod
import sys
from collections import OrderedDict
from pathlib import Path

import streamlit as st

# Shared imports (monorepo)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.mapping_store import (
    load_mapping_set,
    list_mapping_sets,
    approve_mapping,
    reject_mapping,
    override_mapping,
    get_unmatched_fields,
    bulk_approve_high_confidence,
    save_mapping_set,
)
from app.mapping_engine import auto_map_fields, _get_sf_field_labels
from app.pdf_form_store import get_all_forms, get_all_fields
from app.ingestion import load_form_schema
from app.schema import MappingSet, FieldMapping, FormFieldSchema

try:
    from shared.salesforce_client import (
        FORM_SF_OBJECTS,
        create_custom_field,
        describe_object_fields,
    )
except ImportError:
    FORM_SF_OBJECTS = ["Contact"]

    def create_custom_field(*args, **kwargs):  # type: ignore[misc]
        raise RuntimeError("Salesforce connection unavailable")

    def describe_object_fields(obj: str) -> list[dict]:  # type: ignore[misc]
        return []


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SF_OBJECT_LABELS = {
    "Contact": "Contact",
    "Contact_Plus__c": "Contact Plus",
    "Contact_Plus_1__c": "Contact Plus 1",
}

# Map form field types → suggested SF field types
_FORM_TYPE_TO_SF_TYPE = {
    "text": ("Text", 255),
    "date": ("Date", 0),
    "checkbox": ("Checkbox", 0),
    "select": ("Picklist", 0),
    "combo": ("Picklist", 0),
    "textarea": ("LongTextArea", 32768),
}

# Map form field types → compatible SF field types for filtering
_FORM_TYPE_COMPATIBLE_SF: dict[str, set[str]] = {
    "text": {"string", "textarea", "email", "phone", "url", "id", "picklist", "multipicklist"},
    "date": {"date", "datetime"},
    "checkbox": {"boolean"},
    "select": {"picklist", "string"},
    "combo": {"picklist", "string"},
    "textarea": {"textarea", "string"},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_sf_fields_with_types(object_name: str) -> list[dict]:
    """Return SF fields with type info for an object. Cached per session."""
    cache_key = f"_sf_fields_typed_{object_name}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    try:
        fields = describe_object_fields(object_name)
    except Exception:
        fields = []
    # Fallback for Contact
    if not fields and object_name == "Contact":
        try:
            from shared.pdf_form_extractor import SF_FIELD_LABELS
            fields = [
                {"name": api, "label": label, "type": "string", "updateable": True}
                for api, label in SF_FIELD_LABELS.items()
            ]
        except Exception:
            pass
    st.session_state[cache_key] = fields
    return fields


def _sf_field_options_typed(
    object_name: str,
    form_field_type: str = "",
) -> list[tuple[str, str]]:
    """Return (display_string, api_name) for SF fields, optionally filtered by type compatibility."""
    all_fields = _get_sf_fields_with_types(object_name)
    if not all_fields:
        return []

    compatible_types = _FORM_TYPE_COMPATIBLE_SF.get(form_field_type, set()) if form_field_type else set()

    results: list[tuple[str, str]] = []
    for f in all_fields:
        if not f.get("updateable", True) and f.get("type") != "boolean":
            continue
        if compatible_types and f.get("type") not in compatible_types:
            continue
        label = f.get("label", f["name"])
        results.append((f"{label} ({f['name']})", f["name"]))

    return sorted(results, key=lambda t: t[0].lower())


def _sf_field_options(object_name: str = "Contact") -> list[tuple[str, str]]:
    """Unfiltered SF field options (for backwards compat)."""
    return _sf_field_options_typed(object_name, "")


def _build_schema_lookup(form_id: str) -> dict[str, FormFieldSchema]:
    """Build a field_id → FormFieldSchema lookup for a form."""
    schema = load_form_schema(form_id)
    if not schema:
        return {}
    return {f.field_id: f for f in schema.fields}


def _display_label_for_field(schema_lookup: dict[str, FormFieldSchema], field_id: str) -> str:
    """Human-readable display label from schema or fallback."""
    fld = schema_lookup.get(field_id)
    if fld and fld.display_label:
        return fld.display_label
    # Fallback: parse the raw field id
    try:
        from shared.pdf_form_extractor import _parse_field_name
        return _parse_field_name(field_id)
    except ImportError:
        return field_id.replace("_", " ").title()


def _get_field_section(schema_lookup: dict[str, FormFieldSchema], field_id: str) -> str:
    """Get the section for a field from the schema."""
    fld = schema_lookup.get(field_id)
    if fld and fld.section:
        return fld.section
    return "Other"


def _get_form_field_type(schema_lookup: dict[str, FormFieldSchema], field_id: str) -> str:
    """Get the form field type for a field_id."""
    fld = schema_lookup.get(field_id)
    if fld:
        return fld.field_type
    return "text"


def _get_form_field_options(schema_lookup: dict[str, FormFieldSchema], field_id: str) -> list[str]:
    """Get picklist options for a form field."""
    fld = schema_lookup.get(field_id)
    if fld:
        return fld.options or []
    return []


def _linked_icon(mapping: FieldMapping) -> str:
    """Return a linked/unlinked indicator."""
    if mapping.approved:
        return '<span title="Linked to Salesforce" style="color:#2e7d32; font-size:1.1rem;">&#x1F517;</span>'
    if mapping.sf_field:
        return '<span title="Suggested (pending)" style="color:#f57f17; font-size:1.1rem;">&#x1F517;</span>'
    return '<span title="Not linked" style="color:#ccc; font-size:1.1rem;">&#x26D3;</span>'


def _method_badge(method: str) -> str:
    """Return an HTML badge for the match method."""
    if not method:
        return ""
    colors = {
        "exact":   ("#e8f5e9", "#2e7d32"),
        "synonym": ("#e8f5e9", "#388e3c"),
        "history": ("#e3f2fd", "#1565c0"),
        "fuzzy":   ("#fff8e1", "#f57f17"),
        "manual":  ("#e3f2fd", "#1565c0"),
    }
    bg, fg = colors.get(method, ("#f5f5f5", "#616161"))
    return (
        f'<span style="background:{bg}; color:{fg}; padding:1px 6px; '
        f'border-radius:4px; font-size:0.72rem; font-weight:600;">{method}</span>'
    )


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_mappings_tab() -> None:
    """Render the Field Mappings review tab."""

    # ------------------------------------------------------------------
    # 1. Form filter
    # ------------------------------------------------------------------
    all_mapping_sets = list_mapping_sets()
    if not all_mapping_sets:
        st.info(
            "No field mappings found yet. Upload and ingest a form first, "
            "then run the auto-mapper to generate mappings."
        )
        return

    all_forms = get_all_forms()
    form_ids_with_mappings = [ms.form_id for ms in all_mapping_sets]

    filter_options = ["All Forms"] + form_ids_with_mappings
    filter_labels: dict[str, str] = {"All Forms": "All Forms"}
    for fid in form_ids_with_mappings:
        meta = all_forms.get(fid, {})
        title = meta.get("title", "")
        filter_labels[fid] = f"{fid} -- {title}" if title else fid

    top_cols = st.columns([3, 4])
    with top_cols[0]:
        selected_filter = st.selectbox(
            "Filter by Form",
            options=filter_options,
            format_func=lambda x: filter_labels.get(x, x),
            key="mappings_form_filter",
        )
    with top_cols[1]:
        search_query = st.text_input(
            "Search fields",
            key="mappings_search",
            placeholder="Type to filter by field name, section, or SF field...",
        )

    if selected_filter == "All Forms":
        visible_sets = all_mapping_sets
    else:
        visible_sets = [ms for ms in all_mapping_sets if ms.form_id == selected_filter]

    # ------------------------------------------------------------------
    # 2. Summary stats + bulk actions
    # ------------------------------------------------------------------
    total_mappings = sum(len(ms.mappings) for ms in visible_sets)
    total_approved = sum(
        sum(1 for m in ms.mappings if m.approved) for ms in visible_sets
    )
    total_pending = sum(
        sum(1 for m in ms.mappings if m.sf_field and not m.approved)
        for ms in visible_sets
    )
    total_unmatched = sum(
        sum(1 for m in ms.mappings if not m.sf_field) for ms in visible_sets
    )

    stat_cols = st.columns(6)
    stat_cols[0].metric("Total Fields", total_mappings)
    stat_cols[1].metric("Linked", total_approved)
    stat_cols[2].metric("Pending", total_pending)
    stat_cols[3].metric("Unmatched", total_unmatched)
    with stat_cols[4]:
        if st.button("Approve All Pending", use_container_width=True, type="primary"):
            count = 0
            for ms in visible_sets:
                count += bulk_approve_high_confidence(ms.form_id, threshold=0.0)
            if count:
                st.toast(f"Approved {count} mapping(s).")
            else:
                st.toast("No pending mappings to approve.")
            st.rerun()
    with stat_cols[5]:
        if st.button("Re-ingest & Re-map", use_container_width=True):
            from app.ingestion import ingest_pdf, save_form_schema
            from app.pdf_form_store import get_template_pdf_bytes

            remapped = 0
            for ms in visible_sets:
                # Re-ingest the PDF if available (to get updated labels/sections)
                pdf_bytes = get_template_pdf_bytes(ms.form_id)
                if pdf_bytes:
                    form_title = all_forms.get(ms.form_id, {}).get("title", ms.form_id)
                    new_schema = ingest_pdf(pdf_bytes, ms.form_id, title=form_title)
                    save_form_schema(new_schema)
                    schema = new_schema
                else:
                    schema = load_form_schema(ms.form_id)
                if not schema:
                    continue

                # Preserve existing approved mappings
                old_ms = load_mapping_set(ms.form_id)
                approved_lookup: dict[str, FieldMapping] = {}
                if old_ms:
                    for m in old_ms.mappings:
                        if m.approved:
                            approved_lookup[m.field_id] = m
                new_ms = auto_map_fields(schema.fields, ms.form_id)
                for new_m in new_ms.mappings:
                    prev = approved_lookup.get(new_m.field_id)
                    if prev:
                        new_m.sf_field = prev.sf_field
                        new_m.sf_object = prev.sf_object
                        new_m.match_method = prev.match_method
                        new_m.confidence = prev.confidence
                        new_m.approved = True
                        new_m.approved_by = prev.approved_by
                        new_m.approved_at = prev.approved_at
                save_mapping_set(new_ms)
                remapped += 1
            if remapped:
                st.toast(f"Re-ingested & re-mapped {remapped} form(s). Approved mappings preserved.")
            st.rerun()

    # ------------------------------------------------------------------
    # 3. SF field cache
    # ------------------------------------------------------------------
    obj_options = list(FORM_SF_OBJECTS)

    # ------------------------------------------------------------------
    # 4. Render each form's mappings grouped by section
    # ------------------------------------------------------------------
    search_lower = search_query.strip().lower() if search_query else ""

    for ms in visible_sets:
        form_meta = all_forms.get(ms.form_id, {})
        form_title = form_meta.get("title", "")
        header_text = f"{ms.form_id} -- {form_title}" if form_title else ms.form_id

        st.markdown("---")
        st.subheader(header_text)

        if not ms.mappings:
            st.info("No mappings for this form.")
            continue

        # Build schema lookup for display labels and sections
        schema_lookup = _build_schema_lookup(ms.form_id)

        # Group mappings by section
        section_groups: OrderedDict[str, list[FieldMapping]] = OrderedDict()
        for mapping in ms.mappings:
            section = _get_field_section(schema_lookup, mapping.field_id)
            section_groups.setdefault(section, [])
            section_groups[section].append(mapping)

        for section_name, section_mappings in section_groups.items():
            # Apply search filter
            if search_lower:
                filtered = []
                for m in section_mappings:
                    label = _display_label_for_field(schema_lookup, m.field_id)
                    searchable = f"{label} {section_name} {m.sf_field} {m.field_id}".lower()
                    if search_lower in searchable:
                        filtered.append(m)
                if not filtered:
                    continue
                section_mappings = filtered

            # Count linked/total for section header
            linked = sum(1 for m in section_mappings if m.approved)
            total = len(section_mappings)
            linked_pct = f"{linked}/{total}"

            st.markdown(
                f'<div style="font-size:0.95rem; font-weight:700; color:#1a2744; '
                f'margin:16px 0 6px 0; padding:6px 0; border-bottom:2px solid #e2e8f0;">'
                f'{html_mod.escape(section_name)}'
                f'<span style="float:right; font-size:0.8rem; font-weight:500; color:#86868b;">'
                f'{linked_pct} linked</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            for idx, mapping in enumerate(section_mappings):
                row_key = f"{ms.form_id}__{mapping.field_id}__{idx}"
                display_label = _display_label_for_field(schema_lookup, mapping.field_id)
                form_ftype = _get_form_field_type(schema_lookup, mapping.field_id)

                # Layout: [link icon] [field name + method] [SF field selector / override] [action]
                cols = st.columns([0.4, 3.5, 4, 1.5])

                # Link icon
                with cols[0]:
                    st.markdown(_linked_icon(mapping), unsafe_allow_html=True)

                # Field name + match method
                with cols[1]:
                    label_html = f'<span style="font-weight:600; font-size:0.88rem;">{html_mod.escape(display_label)}</span>'
                    if mapping.match_method:
                        label_html += f" {_method_badge(mapping.match_method)}"
                    st.markdown(label_html, unsafe_allow_html=True)

                # SF Field — show current mapping or override selector
                with cols[2]:
                    if mapping.approved:
                        # Show linked field with object badge
                        obj_label = SF_OBJECT_LABELS.get(mapping.sf_object, mapping.sf_object)
                        sf_label = mapping.sf_field
                        # Try to get the human-readable label
                        sf_fields = _get_sf_fields_with_types(mapping.sf_object)
                        for sf in sf_fields:
                            if sf["name"] == mapping.sf_field:
                                sf_label = f"{sf['label']} ({sf['name']})"
                                break
                        st.markdown(
                            f'<span style="font-size:0.85rem;">{html_mod.escape(sf_label)}</span> '
                            f'<span style="background:#e3f2fd; color:#1565c0; padding:1px 6px; '
                            f'border-radius:4px; font-size:0.7rem; font-weight:500;">'
                            f'{html_mod.escape(obj_label)}</span>',
                            unsafe_allow_html=True,
                        )
                    else:
                        # Override selector — type-filtered SF fields
                        obj_key = f"obj_{row_key}"
                        if obj_key not in st.session_state:
                            st.session_state[obj_key] = mapping.sf_object

                        # Compact: object + field in one row
                        ov_cols = st.columns([1, 3])
                        with ov_cols[0]:
                            selected_obj = st.selectbox(
                                "Obj",
                                options=obj_options,
                                format_func=lambda x: SF_OBJECT_LABELS.get(x, x),
                                key=obj_key,
                                label_visibility="collapsed",
                            )
                        with ov_cols[1]:
                            sf_options = _sf_field_options_typed(selected_obj, form_ftype)
                            display_strings = [t[0] for t in sf_options]
                            api_lookup = {t[0]: t[1] for t in sf_options}

                            # Pre-select current mapping if it exists
                            current_display = ""
                            if mapping.sf_field:
                                for ds, api in sf_options:
                                    if api == mapping.sf_field:
                                        current_display = ds
                                        break

                            options_list = [""] + display_strings
                            default_idx = 0
                            if current_display and current_display in options_list:
                                default_idx = options_list.index(current_display)

                            override_sel = st.selectbox(
                                "SF Field",
                                options=options_list,
                                index=default_idx,
                                key=f"sf_{row_key}",
                                label_visibility="collapsed",
                            )

                # Action button
                with cols[3]:
                    if mapping.approved:
                        # Unlink button
                        if st.button("Unlink", key=f"unlink_{row_key}", use_container_width=True):
                            reject_mapping(ms.form_id, mapping.field_id)
                            st.rerun()
                    elif override_sel and override_sel in api_lookup:
                        # Apply override (links and approves)
                        if st.button("Link", key=f"link_{row_key}", use_container_width=True, type="primary"):
                            api_name = api_lookup[override_sel]
                            override_mapping(
                                ms.form_id, mapping.field_id,
                                api_name, sf_object=selected_obj,
                            )
                            st.rerun()
                    elif mapping.sf_field and not mapping.approved:
                        # Approve suggestion
                        if st.button("Approve", key=f"approve_{row_key}", use_container_width=True, type="primary"):
                            approve_mapping(ms.form_id, mapping.field_id)
                            st.rerun()

            # "Create New SF Field" for unmatched fields in this section
            unmatched_in_section = [
                m for m in section_mappings if not m.sf_field
            ]
            if unmatched_in_section:
                for m in unmatched_in_section:
                    create_key = f"_create_field_{ms.form_id}__{m.field_id}"
                    if st.session_state.get(create_key):
                        u_label = _display_label_for_field(schema_lookup, m.field_id)
                        ftype = _get_form_field_type(schema_lookup, m.field_id)
                        with st.expander(f"Create SF field for: {u_label}", expanded=True):
                            cf_cols = st.columns([1.5, 2, 1.5, 1])

                            with cf_cols[0]:
                                cf_obj = st.selectbox(
                                    "Target Object",
                                    options=obj_options,
                                    format_func=lambda x: SF_OBJECT_LABELS.get(x, x),
                                    key=f"cf_obj_{ms.form_id}__{m.field_id}",
                                )

                            with cf_cols[1]:
                                cf_label = st.text_input(
                                    "Field Label",
                                    key=f"cf_label_{ms.form_id}__{m.field_id}",
                                    placeholder=u_label,
                                )
                                if not cf_label:
                                    cf_label = u_label

                            suggested_sf_type, suggested_length = _FORM_TYPE_TO_SF_TYPE.get(
                                ftype, ("Text", 255)
                            )
                            sf_type_options = [
                                "Text", "Date", "Checkbox", "Picklist",
                                "LongTextArea", "Number", "Email", "Phone",
                            ]
                            default_idx = (
                                sf_type_options.index(suggested_sf_type)
                                if suggested_sf_type in sf_type_options
                                else 0
                            )

                            with cf_cols[2]:
                                cf_type = st.selectbox(
                                    "Field Type",
                                    options=sf_type_options,
                                    index=default_idx,
                                    key=f"cf_type_{ms.form_id}__{m.field_id}",
                                )

                            with cf_cols[3]:
                                if st.button(
                                    "Create",
                                    key=f"btn_cf_{ms.form_id}__{m.field_id}",
                                    use_container_width=True,
                                    type="primary",
                                ):
                                    try:
                                        pl_values = None
                                        if cf_type == "Picklist":
                                            pl_values = _get_form_field_options(
                                                schema_lookup, m.field_id,
                                            )
                                        result = create_custom_field(
                                            object_name=cf_obj,
                                            field_label=cf_label,
                                            field_type=cf_type,
                                            length=suggested_length or 255,
                                            picklist_values=pl_values,
                                        )
                                        api_name = result["apiName"]
                                        override_mapping(
                                            ms.form_id, m.field_id,
                                            api_name, sf_object=cf_obj,
                                        )
                                        st.session_state.pop(create_key, None)
                                        # Clear field cache so new field shows
                                        st.session_state.pop(f"_sf_fields_typed_{cf_obj}", None)
                                        st.toast(
                                            f"Created '{cf_label}' ({api_name}) on "
                                            f"{SF_OBJECT_LABELS.get(cf_obj, cf_obj)} and linked."
                                        )
                                        st.rerun()
                                    except Exception as exc:
                                        st.error(f"Failed to create field: {exc}")

                # "Create New" trigger button at the bottom of unmatched group
                if len(unmatched_in_section) > 0:
                    btn_key = f"btn_create_section_{ms.form_id}__{section_name}"
                    create_active = any(
                        st.session_state.get(f"_create_field_{ms.form_id}__{m.field_id}")
                        for m in unmatched_in_section
                    )
                    if not create_active:
                        c1, c2 = st.columns([6, 2])
                        with c2:
                            if st.button(
                                f"Create SF Field ({len(unmatched_in_section)} unmatched)",
                                key=btn_key,
                                use_container_width=True,
                            ):
                                # Open create form for the first unmatched field
                                first = unmatched_in_section[0]
                                st.session_state[f"_create_field_{ms.form_id}__{first.field_id}"] = True
                                st.rerun()

        # Warning if no SF fields could be loaded
        all_sf = _get_sf_fields_with_types("Contact")
        if not all_sf:
            st.warning(
                "Could not load Salesforce field list. "
                "Check your Salesforce connection or static field definitions."
            )
