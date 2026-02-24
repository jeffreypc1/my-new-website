"""Manage Forms tab -- form catalog browser and PDF upload ingestion.

Shows all available forms (hardcoded + uploaded) in the left column with
type badges, and an editable field table in the right column.  Uploading
a new PDF auto-detects fillable/nonfillable, extracts fields, runs role
suggestion and SF auto-mapping, and persists the result.

Exports a single function: ``render_ingest_tab()``.
"""

from __future__ import annotations

import html as html_mod
import sys
from pathlib import Path

import streamlit as st

from app.pdf_form_store import get_all_forms, get_all_fields, save_template_pdf, is_uploaded_form
from app.ingestion import ingest_pdf, save_form_schema, load_form_schema, compare_versions, list_form_schemas
from app.mapping_engine import auto_map_fields
from app.mapping_store import save_mapping_set, load_mapping_set
from app.audit_log import log_action
from app.schema import FormSchema

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.config_store import load_config, save_config
from shared.pdf_form_extractor import extract_form_fields, auto_suggest_roles


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _derive_form_id(filename: str) -> str:
    """Derive a form_id from an uploaded PDF filename.

    Strips the .pdf extension, replaces spaces and underscores with
    hyphens, and upper-cases the result so IDs look like "I-589" or
    "CUSTOM-FORM".
    """
    stem = Path(filename).stem
    form_id = stem.replace(" ", "-").replace("_", "-").upper()
    return form_id


def _badge_html(text: str, color: str, bg: str) -> str:
    """Return an inline HTML badge span."""
    return (
        f'<span style="display:inline-block; font-size:0.7rem; font-weight:600; '
        f'padding:2px 8px; border-radius:4px; color:{color}; background:{bg}; '
        f'margin-left:6px; vertical-align:middle;">{html_mod.escape(text)}</span>'
    )


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_ingest_tab() -> None:
    """Render the Manage Forms tab content."""

    # Session state defaults
    if "ingest_selected_form" not in st.session_state:
        st.session_state.ingest_selected_form = None

    left_col, right_col = st.columns([1, 2], gap="large")

    # ==================================================================
    # LEFT COLUMN -- Form catalog + PDF uploader
    # ==================================================================
    with left_col:
        st.markdown("##### Upload New Form")

        uploaded_file = st.file_uploader(
            "Upload PDF Form",
            type=["pdf"],
            key="pdf_uploader",
        )

        if uploaded_file is not None:
            _handle_pdf_upload(uploaded_file)

        st.markdown("---")
        st.markdown("##### Form Catalog")

        all_forms = get_all_forms()
        if not all_forms:
            st.info("No forms available.")
            return

        for form_id, meta in all_forms.items():
            title = meta.get("title", "")
            is_uploaded = meta.get("_uploaded", False)

            # Determine badge
            if not is_uploaded:
                badge = _badge_html("Built-in", "#555", "#e8e8e8")
            else:
                # Check if fillable by looking at stored schema source
                cfg = load_config("forms-assistant") or {}
                uploaded_cfg = cfg.get("uploaded_forms", {}).get(form_id, {})
                fields = uploaded_cfg.get("fields", [])
                # If it came through ingest_pdf as fillable, its schema source
                # would be "uploaded_fillable"; we can also check if fields
                # have real pdf_field_names vs block_* ids
                has_real_fields = any(
                    not f.get("pdf_field_name", "").startswith("block_")
                    for f in fields
                )
                if has_real_fields and fields:
                    badge = _badge_html("Fillable PDF", "#1565c0", "#e3f2fd")
                else:
                    badge = _badge_html("Non-fillable", "#e65100", "#fff3e0")

            # Selection button styled as expander-like row
            is_selected = st.session_state.ingest_selected_form == form_id
            label_prefix = ">> " if is_selected else ""

            col_btn, col_badge = st.columns([3, 1])
            with col_btn:
                if st.button(
                    f"{label_prefix}{form_id} -- {title}",
                    key=f"ingest_select_{form_id}",
                    use_container_width=True,
                ):
                    st.session_state.ingest_selected_form = form_id
                    st.rerun()
            with col_badge:
                st.markdown(badge, unsafe_allow_html=True)

    # ==================================================================
    # RIGHT COLUMN -- Field editor for selected form
    # ==================================================================
    with right_col:
        selected = st.session_state.ingest_selected_form
        if selected is None:
            st.info("Select a form from the catalog to view and edit its fields.")
            return

        all_forms = get_all_forms()
        if selected not in all_forms:
            st.warning(f"Form **{selected}** not found in catalog.")
            return

        meta = all_forms[selected]
        title = meta.get("title", "")
        is_uploaded = meta.get("_uploaded", False)
        is_hardcoded = not is_uploaded

        st.markdown(f"##### {html_mod.escape(selected)} -- {html_mod.escape(title)}")

        if is_hardcoded:
            st.caption("This is a built-in form. Fields are read-only.")

        # -- Re-ingest button (uploaded forms only) --
        if is_uploaded:
            reingest_cols = st.columns([1, 3])
            with reingest_cols[0]:
                if st.button("Re-ingest from PDF", key="btn_reingest"):
                    _handle_reingest(selected)

        # -- Load fields --
        fields_by_section = get_all_fields(selected)

        if not fields_by_section:
            st.info("No field definitions available for this form.")
            return

        # Load SF mappings for this form
        mapping_set = load_mapping_set(selected)
        mapping_lookup: dict[str, dict] = {}
        if mapping_set:
            for m in mapping_set.mappings:
                mapping_lookup[m.field_id] = {
                    "sf_field": m.sf_field,
                    "confidence": m.confidence,
                    "method": m.match_method,
                }

        # Build flat table data for st.data_editor
        table_rows: list[dict] = []
        for section_name, fields in fields_by_section.items():
            for f in fields:
                sf_info = mapping_lookup.get(f.name, {})
                table_rows.append({
                    "Field Name": f.name,
                    "Type": f.field_type,
                    "Section": section_name if section_name else (f.section or ""),
                    "Required": f.required,
                    "SF Mapping": sf_info.get("sf_field", ""),
                    "Confidence": round(sf_info.get("confidence", 0.0), 2),
                })

        if not table_rows:
            st.info("This form has no extracted fields.")
            return

        if is_hardcoded:
            # Read-only display
            st.dataframe(
                table_rows,
                use_container_width=True,
                hide_index=True,
            )
        else:
            # Editable table for uploaded forms
            import pandas as pd

            df = pd.DataFrame(table_rows)

            edited_df = st.data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                disabled=["Field Name", "SF Mapping", "Confidence"],
                column_config={
                    "Field Name": st.column_config.TextColumn("Field Name", width="medium"),
                    "Type": st.column_config.SelectboxColumn(
                        "Type",
                        options=["text", "date", "select", "checkbox", "textarea", "combo", "phone", "email"],
                        width="small",
                    ),
                    "Section": st.column_config.TextColumn("Section", width="small"),
                    "Required": st.column_config.CheckboxColumn("Required", width="small"),
                    "SF Mapping": st.column_config.TextColumn("SF Mapping", width="medium"),
                    "Confidence": st.column_config.NumberColumn(
                        "Confidence",
                        format="%.2f",
                        width="small",
                    ),
                },
                key=f"field_editor_{selected}",
            )

            # Save edits button
            if st.button("Save Field Edits", type="primary", key="btn_save_field_edits"):
                _save_field_edits(selected, edited_df)
                st.success("Field edits saved.")
                log_action(
                    action="fields_edited",
                    form_id=selected,
                    details={"field_count": len(edited_df)},
                )
                st.rerun()


# ---------------------------------------------------------------------------
# PDF upload handler
# ---------------------------------------------------------------------------

def _handle_pdf_upload(uploaded_file) -> None:
    """Process an uploaded PDF: detect, extract, map, and persist."""
    pdf_bytes = uploaded_file.read()
    filename = uploaded_file.name
    form_id = _derive_form_id(filename)
    title = Path(filename).stem.replace("_", " ").replace("-", " ").title()

    # Check if re-uploading an existing form
    existing_schema = load_form_schema(form_id)
    is_reupload = existing_schema is not None

    with st.spinner(f"Ingesting **{filename}**..."):
        # 1. Ingest: detect type + extract fields
        schema = ingest_pdf(pdf_bytes, form_id, title=title)

        # 2. Auto-suggest roles on raw fields (for fillable PDFs)
        if schema.source == "uploaded_fillable":
            raw_fields = extract_form_fields(pdf_bytes)
            raw_fields = auto_suggest_roles(raw_fields)

            # Update schema fields with role and sf_field from suggestions
            raw_lookup = {f["pdf_field_name"]: f for f in raw_fields}
            for fld in schema.fields:
                raw = raw_lookup.get(fld.field_id, {})
                if raw.get("role", "none") != "none":
                    fld.role = raw["role"]
                if raw.get("sf_field", ""):
                    fld.sf_field = raw["sf_field"]

        # 3. Auto-map fields to Salesforce
        mapping_set = auto_map_fields(schema.fields, form_id)

        # 4. Handle version comparison for re-uploads
        if is_reupload and existing_schema:
            schema.version = existing_schema.version + 1
            schema.version_hash = schema.compute_version_hash()

        # 5. Save schema to disk
        save_form_schema(schema)

        # 6. Save mapping set
        save_mapping_set(mapping_set)

        # 7. Save PDF template
        save_template_pdf(form_id, pdf_bytes)

        # 8. Save to config store (uploaded_forms)
        _save_to_config_store(form_id, title, schema)

        # 9. Log the action
        log_action(
            action="form_ingested",
            form_id=form_id,
            details={
                "filename": filename,
                "source": schema.source,
                "field_count": len(schema.fields),
                "version": schema.version,
                "is_reupload": is_reupload,
            },
        )

    # Show success
    field_count = len(schema.fields)
    st.success(
        f"Uploaded **{filename}** as **{form_id}** -- "
        f"{field_count} field(s) extracted ({schema.source})"
    )

    # Show version diff for re-uploads
    if is_reupload and existing_schema:
        diff = compare_versions(existing_schema, schema)
        if diff["is_different"]:
            st.markdown("**Version comparison:**")
            if diff["added_fields"]:
                st.markdown(
                    f"- **Added** ({len(diff['added_fields'])}): "
                    + ", ".join(f"`{f}`" for f in diff["added_fields"][:10])
                )
            if diff["removed_fields"]:
                st.markdown(
                    f"- **Removed** ({len(diff['removed_fields'])}): "
                    + ", ".join(f"`{f}`" for f in diff["removed_fields"][:10])
                )
            if diff["changed_fields"]:
                st.markdown(f"- **Changed**: {len(diff['changed_fields'])} field(s)")
        else:
            st.info("No field differences detected compared to the previous version.")

    # Auto-select the newly uploaded form
    st.session_state.ingest_selected_form = form_id


# ---------------------------------------------------------------------------
# Config store persistence
# ---------------------------------------------------------------------------

def _save_to_config_store(form_id: str, title: str, schema: FormSchema) -> None:
    """Save form metadata and fields to the config store in the format
    expected by pdf_form_store.
    """
    cfg = load_config("forms-assistant") or {}
    uploaded_forms = cfg.get("uploaded_forms", {})

    fields_list = []
    for fld in schema.fields:
        fields_list.append({
            "pdf_field_name": fld.field_id,
            "display_label": fld.display_label,
            "field_type": fld.field_type,
            "section": fld.section or "Page 1",
            "required": fld.required,
            "role": fld.role,
            "sf_field": fld.sf_field,
            "help_text": fld.help_text,
        })

    uploaded_forms[form_id] = {
        "title": title,
        "fields": fields_list,
    }

    cfg["uploaded_forms"] = uploaded_forms
    save_config("forms-assistant", cfg)


# ---------------------------------------------------------------------------
# Re-ingest handler
# ---------------------------------------------------------------------------

def _handle_reingest(form_id: str) -> None:
    """Re-extract fields from the saved PDF template for an uploaded form."""
    from app.pdf_form_store import get_template_pdf_bytes

    pdf_bytes = get_template_pdf_bytes(form_id)
    if not pdf_bytes:
        st.error(f"No PDF template found for **{form_id}**.")
        return

    existing_schema = load_form_schema(form_id)

    all_forms = get_all_forms()
    title = all_forms.get(form_id, {}).get("title", form_id)

    with st.spinner(f"Re-ingesting **{form_id}**..."):
        schema = ingest_pdf(pdf_bytes, form_id, title=title)

        # Auto-suggest roles
        if schema.source == "uploaded_fillable":
            raw_fields = extract_form_fields(pdf_bytes)
            raw_fields = auto_suggest_roles(raw_fields)
            raw_lookup = {f["pdf_field_name"]: f for f in raw_fields}
            for fld in schema.fields:
                raw = raw_lookup.get(fld.field_id, {})
                if raw.get("role", "none") != "none":
                    fld.role = raw["role"]
                if raw.get("sf_field", ""):
                    fld.sf_field = raw["sf_field"]

        # Auto-map
        mapping_set = auto_map_fields(schema.fields, form_id)

        # Bump version
        if existing_schema:
            schema.version = existing_schema.version + 1
        schema.version_hash = schema.compute_version_hash()

        save_form_schema(schema)
        save_mapping_set(mapping_set)
        _save_to_config_store(form_id, title, schema)

        log_action(
            action="form_reingested",
            form_id=form_id,
            details={
                "source": schema.source,
                "field_count": len(schema.fields),
                "version": schema.version,
            },
        )

    st.success(
        f"Re-ingested **{form_id}** -- "
        f"{len(schema.fields)} field(s) extracted (v{schema.version})"
    )

    # Show diff
    if existing_schema:
        diff = compare_versions(existing_schema, schema)
        if diff["is_different"]:
            st.markdown("**Changes from previous version:**")
            if diff["added_fields"]:
                st.markdown(
                    f"- **Added** ({len(diff['added_fields'])}): "
                    + ", ".join(f"`{f}`" for f in diff["added_fields"][:10])
                )
            if diff["removed_fields"]:
                st.markdown(
                    f"- **Removed** ({len(diff['removed_fields'])}): "
                    + ", ".join(f"`{f}`" for f in diff["removed_fields"][:10])
                )
            if diff["changed_fields"]:
                st.markdown(f"- **Changed**: {len(diff['changed_fields'])} field(s)")
        else:
            st.info("No changes detected.")


# ---------------------------------------------------------------------------
# Save field edits from data_editor
# ---------------------------------------------------------------------------

def _save_field_edits(form_id: str, edited_df) -> None:
    """Persist field edits from the data_editor back to the config store."""
    cfg = load_config("forms-assistant") or {}
    uploaded_forms = cfg.get("uploaded_forms", {})
    form_cfg = uploaded_forms.get(form_id, {})
    existing_fields = form_cfg.get("fields", [])

    # Build a lookup of existing fields by pdf_field_name for non-editable
    # attributes (role, sf_field, help_text, etc.)
    existing_lookup = {f["pdf_field_name"]: f for f in existing_fields}

    updated_fields = []
    for _, row in edited_df.iterrows():
        field_name = row["Field Name"]
        existing = existing_lookup.get(field_name, {})

        updated_fields.append({
            "pdf_field_name": field_name,
            "display_label": existing.get("display_label", field_name),
            "field_type": row.get("Type", existing.get("field_type", "text")),
            "section": row.get("Section", existing.get("section", "Page 1")),
            "required": bool(row.get("Required", existing.get("required", False))),
            "role": existing.get("role", "none"),
            "sf_field": existing.get("sf_field", ""),
            "help_text": existing.get("help_text", ""),
        })

    form_cfg["fields"] = updated_fields
    uploaded_forms[form_id] = form_cfg
    cfg["uploaded_forms"] = uploaded_forms
    save_config("forms-assistant", cfg)
