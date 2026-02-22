"""Document Assembler — Streamlit dashboard for exhibit package assembly.

Browse a client's Box folder, select documents, optionally translate
foreign-language docs via Claude, assemble them with tab dividers,
stamp page numbers, and generate a Table of Contents.

Part of the O'Brien Immigration Law tool suite.  Port 8515.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as st_components

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.client_banner import render_client_banner
from shared.tool_notes import render_tool_notes
from shared.box_client import get_file_content, parse_folder_id
from shared.box_folder_browser import render_box_folder_browser
from shared.salesforce_client import load_active_client, upload_file_to_contact
from shared.theme import render_theme_css, render_nav_bar

from app.box_browser import generate_thumbnail, get_thumbnail_b64, get_pdf_page_count
from app.pdf_compiler import (
    _exhibit_letter,
    _to_pdf_bytes,
    compile_exhibit_package,
    generate_toc_pdf,
    generate_toc_docx,
)
from app.translation_engine import create_translation_bundle

try:
    from shared.tool_help import render_tool_help
except ImportError:
    render_tool_help = None
try:
    from shared.feedback_button import render_feedback_button
except ImportError:
    render_feedback_button = None

# -- Canvas component ----------------------------------------------------------

_exhibit_canvas = st_components.declare_component(
    "exhibit_canvas",
    path=str(Path(__file__).resolve().parent / "exhibit_canvas"),
)

# -- Page config ---------------------------------------------------------------

st.set_page_config(
    page_title="Document Assembler -- O'Brien Immigration Law",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -- CSS -----------------------------------------------------------------------

_ASSEMBLER_EXTRA_CSS = """\
/* Exhibit row */
.exhibit-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    margin: 4px 0;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    background: #fff;
}
.exhibit-thumb {
    width: 48px;
    height: 48px;
    border-radius: 4px;
    overflow: hidden;
    background: #f1f5f9;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    border: 1px solid #e2e8f0;
}
.exhibit-thumb img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
.tab-letter {
    background: #1e40af;
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 3px;
    white-space: nowrap;
}
"""
render_theme_css(extra_css=_ASSEMBLER_EXTRA_CSS)

# -- Auth ----------------------------------------------------------------------

from shared.auth import require_auth, render_logout

require_auth()

# -- Navigation bar ------------------------------------------------------------

render_nav_bar("Document Assembler")
render_logout()

render_client_banner()
if render_tool_help:
    render_tool_help("evidence-indexer")
if render_feedback_button:
    render_feedback_button("evidence-indexer")


# -- Session state defaults ----------------------------------------------------

def _init_state(key, default):
    if key not in st.session_state:
        st.session_state[key] = default


_init_state("_asm_selected_docs", [])
_init_state("_asm_doc_bytes", {})
_init_state("_asm_thumbnails", {})
_init_state("_asm_exhibit_order", [])
_init_state("_asm_rename_map", {})
_init_state("_asm_translation_status", {})
_init_state("_asm_translation_bundles", {})
_init_state("_asm_compiled_pdf", None)
_init_state("_asm_toc_entries", [])


# -- Helpers -------------------------------------------------------------------

def _add_doc_to_exhibits(file_item: dict) -> None:
    """Download a Box file, generate thumbnail, and add to exhibits."""
    doc_id = file_item["id"]

    # Skip if already added
    if any(d["id"] == doc_id for d in st.session_state["_asm_selected_docs"]):
        return

    # Download file bytes
    file_bytes = get_file_content(doc_id)
    st.session_state["_asm_doc_bytes"][doc_id] = file_bytes

    # Generate thumbnail
    thumb = get_thumbnail_b64(file_bytes, file_item["name"])
    st.session_state["_asm_thumbnails"][doc_id] = thumb

    # Count pages (for PDFs)
    page_count = 0
    ext = file_item.get("extension", "").lower()
    if ext == "pdf":
        page_count = get_pdf_page_count(file_bytes)

    # Add to selected docs
    doc_entry = {
        "id": doc_id,
        "name": file_item["name"],
        "extension": ext,
        "page_count": page_count,
        "web_url": file_item.get("web_url", ""),
    }
    st.session_state["_asm_selected_docs"].append(doc_entry)
    st.session_state["_asm_exhibit_order"].append(doc_id)

    # Default rename = filename without extension
    title = file_item["name"].rsplit(".", 1)[0] if "." in file_item["name"] else file_item["name"]
    st.session_state["_asm_rename_map"][doc_id] = title

    st.session_state["_asm_translation_status"][doc_id] = "none"


def _remove_doc(doc_id: str) -> None:
    """Remove a document from exhibits."""
    st.session_state["_asm_selected_docs"] = [
        d for d in st.session_state["_asm_selected_docs"] if d["id"] != doc_id
    ]
    st.session_state["_asm_exhibit_order"] = [
        oid for oid in st.session_state["_asm_exhibit_order"] if oid != doc_id
    ]
    st.session_state["_asm_doc_bytes"].pop(doc_id, None)
    st.session_state["_asm_thumbnails"].pop(doc_id, None)
    st.session_state["_asm_rename_map"].pop(doc_id, None)
    st.session_state["_asm_translation_status"].pop(doc_id, None)
    st.session_state["_asm_translation_bundles"].pop(doc_id, None)


# -- Sidebar: Box Folder Browser -----------------------------------------------

# Load active client for Box folder ID (needed by sidebar and output tab)
active_client = load_active_client()
box_folder_raw = ""
client_name = ""
if active_client:
    box_folder_raw = active_client.get("Box_Folder_Id__c", "") or ""
    client_name = active_client.get("Name", "") or ""


def _on_box_files_selected(files: list[dict]) -> None:
    """Callback: download selected files and add to exhibits."""
    for f in files:
        _add_doc_to_exhibits(f)


with st.sidebar:
    if not box_folder_raw:
        st.markdown("#### Box Folder Browser")
        st.info("No Box folder linked to this client. Set `Box_Folder_Id__c` in Salesforce.")
    else:
        root_folder_id = parse_folder_id(box_folder_raw)
        _already = {d["id"] for d in st.session_state["_asm_selected_docs"]}

        render_box_folder_browser(
            root_folder_id,
            mode="picker",
            on_select=_on_box_files_selected,
            already_selected_ids=_already,
            key_prefix="_asm_box",
            add_button_label="Add Selected to Exhibits",
        )

    st.markdown("---")
    render_tool_notes("evidence-indexer")


# -- Main Area -----------------------------------------------------------------

tab_builder, tab_output = st.tabs(["Exhibit Builder", "Compiled Output"])

# ==============================================================================
# Tab 1: Exhibit Builder
# ==============================================================================

with tab_builder:
    exhibit_order = st.session_state["_asm_exhibit_order"]
    selected_docs = st.session_state["_asm_selected_docs"]
    docs_by_id = {d["id"]: d for d in selected_docs}

    if not exhibit_order:
        st.info("Select files from the Box folder browser in the sidebar to begin building your exhibit package.")
    else:
        # -- Per-document rows --
        st.markdown("##### Exhibit Documents")

        for idx, doc_id in enumerate(exhibit_order):
            doc = docs_by_id.get(doc_id)
            if not doc:
                continue

            letter = _exhibit_letter(idx)
            thumb_b64 = st.session_state["_asm_thumbnails"].get(doc_id, "")
            trans_status = st.session_state["_asm_translation_status"].get(doc_id, "none")
            page_count = doc.get("page_count", 0)

            # If there's a translation bundle, update page count to include all parts
            if doc_id in st.session_state["_asm_translation_bundles"]:
                bundle = st.session_state["_asm_translation_bundles"][doc_id]
                page_count = bundle.get("page_count", page_count)

            col_thumb, col_badge, col_title, col_orig, col_pages, col_trans, col_remove = st.columns(
                [0.6, 0.5, 3, 2, 0.8, 1.2, 0.5]
            )

            with col_thumb:
                if thumb_b64:
                    st.markdown(
                        f'<div class="exhibit-thumb"><img src="{thumb_b64}" alt=""></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div class="exhibit-thumb">📄</div>',
                        unsafe_allow_html=True,
                    )

            with col_badge:
                st.markdown(
                    f'<span class="tab-letter">Tab {letter}</span>',
                    unsafe_allow_html=True,
                )

            with col_title:
                new_title = st.text_input(
                    "Title",
                    key=f"_asm_title_{doc_id}",
                    label_visibility="collapsed",
                    value=st.session_state["_asm_rename_map"].get(doc_id, ""),
                )
                if new_title != st.session_state["_asm_rename_map"].get(doc_id):
                    st.session_state["_asm_rename_map"][doc_id] = new_title

            with col_orig:
                st.caption(doc["name"])

            with col_pages:
                if page_count:
                    st.caption(f"{page_count} pg{'s' if page_count != 1 else ''}")

            with col_trans:
                if trans_status == "none":
                    if st.button("Translate", key=f"_asm_trans_{doc_id}"):
                        st.session_state["_asm_translation_status"][doc_id] = "pending"
                        st.rerun()
                elif trans_status == "pending":
                    st.markdown("⏳ Pending...")
                elif trans_status == "translating":
                    st.markdown("🔵 Translating...")
                elif trans_status == "bundle":
                    st.markdown("🟢 Translated")
                elif trans_status == "error":
                    st.markdown("🔴 Error")
                    if st.button("Retry", key=f"_asm_retry_{doc_id}"):
                        st.session_state["_asm_translation_status"][doc_id] = "pending"
                        st.rerun()

            with col_remove:
                if st.button("✕", key=f"_asm_rm_{doc_id}", help="Remove from exhibits"):
                    _remove_doc(doc_id)
                    st.rerun()

        # -- Canvas for drag-and-drop reordering --
        st.markdown("---")
        st.markdown("##### Reorder Exhibits")

        canvas_blocks = []
        for idx, doc_id in enumerate(exhibit_order):
            doc = docs_by_id.get(doc_id)
            if not doc:
                continue
            canvas_blocks.append({
                "id": doc_id,
                "label": st.session_state["_asm_rename_map"].get(doc_id, doc["name"]),
                "thumbnail_b64": st.session_state["_asm_thumbnails"].get(doc_id, ""),
                "letter": _exhibit_letter(idx),
                "original_name": doc["name"],
                "page_count": doc.get("page_count", 0),
                "is_bundle": doc_id in st.session_state["_asm_translation_bundles"],
                "translation_status": st.session_state["_asm_translation_status"].get(doc_id, "none"),
            })

        canvas_result = _exhibit_canvas(
            blocks=canvas_blocks,
            block_order=exhibit_order,
            force_order=True,
            height=max(100, len(canvas_blocks) * 65 + 60),
            key="_asm_canvas",
        )

        if canvas_result:
            new_order = canvas_result.get("block_order")
            action = canvas_result.get("action")

            if action == "reset":
                # Reset to original add order
                st.session_state["_asm_exhibit_order"] = [
                    d["id"] for d in st.session_state["_asm_selected_docs"]
                ]
                st.rerun()
            elif new_order and new_order != exhibit_order:
                st.session_state["_asm_exhibit_order"] = new_order
                st.rerun()

        # -- Translation workflow --
        # Process any pending translations
        pending_translations = [
            doc_id for doc_id, status in st.session_state["_asm_translation_status"].items()
            if status == "pending"
        ]

        if pending_translations:
            # Translator info expander
            st.markdown("---")
            with st.expander("Translator Information", expanded=True):
                st.caption("Required for EOIR Certificate of Translation.")
                t_col1, t_col2 = st.columns(2)
                with t_col1:
                    _init_state("_asm_translator_name", "")
                    translator_name = st.text_input(
                        "Translator Name",
                        key="_asm_translator_name_input",
                        value=st.session_state.get("_asm_translator_name", ""),
                    )
                    st.session_state["_asm_translator_name"] = translator_name

                    _init_state("_asm_translator_phone", "")
                    translator_phone = st.text_input(
                        "Telephone",
                        key="_asm_translator_phone_input",
                        value=st.session_state.get("_asm_translator_phone", ""),
                    )
                    st.session_state["_asm_translator_phone"] = translator_phone

                with t_col2:
                    _init_state("_asm_translator_address", "")
                    translator_address = st.text_input(
                        "Address",
                        key="_asm_translator_address_input",
                        value=st.session_state.get("_asm_translator_address", ""),
                    )
                    st.session_state["_asm_translator_address"] = translator_address

                    _init_state("_asm_source_lang", "Spanish")
                    source_lang = st.text_input(
                        "Source Language",
                        key="_asm_source_lang_input",
                        value=st.session_state.get("_asm_source_lang", "Spanish"),
                    )
                    st.session_state["_asm_source_lang"] = source_lang

                if translator_name and translator_address:
                    if st.button("Start Translation", type="primary", key="_asm_start_trans"):
                        translator_info = {
                            "name": translator_name,
                            "address": translator_address,
                            "phone": translator_phone,
                        }
                        for doc_id in pending_translations:
                            st.session_state["_asm_translation_status"][doc_id] = "translating"

                        # Process translations
                        for doc_id in pending_translations:
                            doc = docs_by_id.get(doc_id)
                            if not doc:
                                continue
                            file_bytes = st.session_state["_asm_doc_bytes"].get(doc_id)
                            if not file_bytes:
                                st.session_state["_asm_translation_status"][doc_id] = "error"
                                continue

                            with st.spinner(f"Translating {doc['name']}..."):
                                try:
                                    bundle = create_translation_bundle(
                                        file_bytes=file_bytes,
                                        filename=doc["name"],
                                        source_lang=source_lang,
                                        translator_info=translator_info,
                                    )
                                    st.session_state["_asm_translation_bundles"][doc_id] = bundle
                                    st.session_state["_asm_translation_status"][doc_id] = "bundle"
                                except Exception as e:
                                    st.error(f"Translation failed for {doc['name']}: {e}")
                                    st.session_state["_asm_translation_status"][doc_id] = "error"

                        st.rerun()
                else:
                    st.warning("Please fill in translator name and address to proceed.")


# ==============================================================================
# Tab 2: Compiled Output
# ==============================================================================

with tab_output:
    exhibit_order = st.session_state["_asm_exhibit_order"]
    selected_docs = st.session_state["_asm_selected_docs"]
    docs_by_id = {d["id"]: d for d in selected_docs}

    if not exhibit_order:
        st.info("Add documents in the Exhibit Builder tab first.")
    else:
        # Case name for TOC
        _init_state("_asm_case_name", client_name)
        case_name = st.text_input(
            "Case Name (for Table of Contents)",
            key="_asm_case_name_input",
            value=st.session_state.get("_asm_case_name", ""),
        )
        st.session_state["_asm_case_name"] = case_name

        col_compile, col_options = st.columns([1, 2])
        with col_compile:
            include_toc = st.checkbox("Prepend Table of Contents", value=True, key="_asm_include_toc")

        if st.button("Compile Exhibit Package", type="primary", key="_asm_compile"):
            progress_bar = st.progress(0, text="Preparing exhibits...")

            # Build exhibit list
            exhibits = []
            total = len(exhibit_order)
            for idx, doc_id in enumerate(exhibit_order):
                doc = docs_by_id.get(doc_id)
                if not doc:
                    continue

                letter = _exhibit_letter(idx)
                title = st.session_state["_asm_rename_map"].get(doc_id, doc["name"])

                # Get PDF bytes — use translation bundle if available
                if doc_id in st.session_state["_asm_translation_bundles"]:
                    bundle = st.session_state["_asm_translation_bundles"][doc_id]
                    # Merge: Translation → Original → Certificate (single exhibit)
                    import pymupdf

                    merged_bundle = pymupdf.open()
                    for part_key in ("translated_pdf", "original_pdf", "certificate_pdf"):
                        part_bytes = bundle.get(part_key)
                        if part_bytes:
                            converted = _to_pdf_bytes(part_bytes, doc["name"])
                            if converted is None:
                                continue
                            part_doc = pymupdf.open(stream=converted, filetype="pdf")
                            merged_bundle.insert_pdf(part_doc)
                            part_doc.close()
                    pdf_bytes = merged_bundle.tobytes()
                    merged_bundle.close()
                else:
                    raw_bytes = st.session_state["_asm_doc_bytes"].get(doc_id, b"")
                    pdf_bytes = (_to_pdf_bytes(raw_bytes, doc["name"]) or b"") if raw_bytes else b""

                if not pdf_bytes:
                    progress_bar.progress(
                        (idx + 1) / total,
                        text=f"Skipping {doc['name']} (no PDF bytes)...",
                    )
                    continue

                exhibits.append({
                    "id": doc_id,
                    "letter": letter,
                    "title": title,
                    "pdf_bytes": pdf_bytes,
                })

                progress_bar.progress(
                    (idx + 1) / total,
                    text=f"Prepared {title}...",
                )

            if not exhibits:
                st.error("No valid exhibits to compile.")
            else:
                # Compile
                progress_bar.progress(0.5, text="Compiling exhibit package...")

                def _on_progress(msg):
                    progress_bar.progress(0.7, text=msg)

                try:
                    compiled_pdf, toc_entries = compile_exhibit_package(
                        exhibits,
                        on_progress=_on_progress,
                    )

                    # Optionally prepend TOC
                    if include_toc and toc_entries:
                        progress_bar.progress(0.9, text="Generating Table of Contents...")
                        toc_pdf = generate_toc_pdf(toc_entries, case_name=case_name)

                        import pymupdf

                        # Prepend TOC to compiled PDF
                        final = pymupdf.open(stream=toc_pdf, filetype="pdf")
                        compiled_doc = pymupdf.open(stream=compiled_pdf, filetype="pdf")
                        final.insert_pdf(compiled_doc)
                        compiled_doc.close()
                        compiled_pdf = final.tobytes()
                        final.close()

                    st.session_state["_asm_compiled_pdf"] = compiled_pdf
                    st.session_state["_asm_toc_entries"] = toc_entries

                    progress_bar.progress(1.0, text="Compilation complete!")
                    st.toast("Exhibit package compiled successfully!", icon="✅")

                except Exception as e:
                    st.error(f"Compilation failed: {e}")
                    progress_bar.empty()

        # -- Display results --
        compiled_pdf = st.session_state.get("_asm_compiled_pdf")
        toc_entries = st.session_state.get("_asm_toc_entries", [])

        if compiled_pdf:
            st.markdown("---")
            st.markdown("##### Compiled Package")

            # Stats
            import pymupdf

            stats_doc = pymupdf.open(stream=compiled_pdf, filetype="pdf")
            total_pages = len(stats_doc)
            stats_doc.close()
            pdf_size_mb = len(compiled_pdf) / (1024 * 1024)

            col_s1, col_s2, col_s3 = st.columns(3)
            col_s1.metric("Total Pages", total_pages)
            col_s2.metric("Exhibits", len(toc_entries))
            col_s3.metric("File Size", f"{pdf_size_mb:.1f} MB")

            # TOC preview
            if toc_entries:
                st.markdown("##### Table of Contents")
                toc_data = []
                for entry in toc_entries:
                    toc_data.append({
                        "Exhibit": f"Tab {entry['letter']}",
                        "Document Title": entry["title"],
                        "Start Page": entry["start_page"],
                        "End Page": entry["end_page"],
                        "Pages": entry["page_count"],
                    })
                st.dataframe(toc_data, use_container_width=True, hide_index=True)

            # Downloads
            st.markdown("##### Downloads")
            dl_col1, dl_col2, dl_col3 = st.columns(3)

            # Default filename
            safe_name = client_name.replace(" ", "_") if client_name else "exhibits"
            default_filename = f"{safe_name}_Exhibit_Package"

            file_name = st.text_input(
                "File name (without extension)",
                value=default_filename,
                key="_asm_filename",
            )

            with dl_col1:
                st.download_button(
                    "📥 Download Compiled PDF",
                    data=compiled_pdf,
                    file_name=f"{file_name}.pdf",
                    mime="application/pdf",
                    type="primary",
                    key="_asm_dl_pdf",
                )

            with dl_col2:
                if toc_entries:
                    toc_pdf_bytes = generate_toc_pdf(toc_entries, case_name=case_name)
                    st.download_button(
                        "📥 Download TOC (PDF)",
                        data=toc_pdf_bytes,
                        file_name=f"{file_name}_TOC.pdf",
                        mime="application/pdf",
                        key="_asm_dl_toc_pdf",
                    )

            with dl_col3:
                if toc_entries:
                    toc_docx_bytes = generate_toc_docx(toc_entries, case_name=case_name)
                    if toc_docx_bytes:
                        st.download_button(
                            "📥 Download TOC (Word)",
                            data=toc_docx_bytes,
                            file_name=f"{file_name}_TOC.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="_asm_dl_toc_docx",
                        )

            # Upload to Salesforce
            st.markdown("---")
            if active_client:
                contact_id = active_client.get("Id", "")
                if contact_id:
                    if st.button("Upload to Salesforce", key="_asm_upload_sf"):
                        with st.spinner("Uploading to Salesforce..."):
                            try:
                                upload_file_to_contact(
                                    contact_id=contact_id,
                                    file_name=f"{file_name}.pdf",
                                    file_bytes=compiled_pdf,
                                )
                                st.success("Uploaded to Salesforce successfully!")
                            except Exception as e:
                                st.error(f"Upload failed: {e}")
