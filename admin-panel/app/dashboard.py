"""Admin Panel — Centralized configuration for all office tools.

Port 8513. Allows editing templates, lists, and settings for each tool
through a single UI. Changes are saved to JSON files in data/config/
and loaded by each tool on startup.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import streamlit as st

# ── Shared imports ───────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.config_store import load_config, save_config
try:
    from shared.tool_help import render_tool_help
except ImportError:
    render_tool_help = None
try:
    from shared.feedback_button import render_feedback_button
except ImportError:
    render_feedback_button = None
try:
    from shared.recipient_manager import render_recipient_manager
except ImportError:
    render_recipient_manager = None

st.set_page_config(
    page_title="Admin Panel — O'Brien Immigration Law",
    page_icon="&#x2699;&#xFE0F;",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS (matches other tools) ────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
/* Hide Streamlit chrome */
#MainMenu, footer,
div[data-testid="stToolbar"] { display: none !important; }
.stApp { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
.nav-bar {
    display: flex;
    align-items: center;
    padding: 10px 4px;
    margin: -1rem 0 1.2rem 0;
    border-bottom: 1px solid rgba(0,0,0,0.07);
}
.nav-back {
    display: flex; align-items: center; gap: 6px;
    font-family: 'Inter', sans-serif; font-size: 0.85rem;
    font-weight: 500; color: #0066CC; text-decoration: none;
    min-width: 150px;
}
.nav-back:hover { color: #004499; text-decoration: underline; }
.nav-title {
    flex: 1; text-align: center;
    font-family: 'Inter', sans-serif; font-size: 1.15rem;
    font-weight: 700; color: #1a2744; letter-spacing: -0.02em;
}
.nav-firm { font-weight: 400; color: #86868b; font-size: 0.85rem; margin-left: 8px; }
.nav-spacer { min-width: 150px; }
</style>
""",
    unsafe_allow_html=True,
)

from shared.auth import require_auth, render_logout
require_auth()

# ── Nav bar ──────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="nav-bar">
    <a href="http://localhost:8502" class="nav-back">&#8592; Staff Dashboard</a>
    <div class="nav-title">Admin Panel<span class="nav-firm">&mdash; O'Brien Immigration Law</span></div>
    <div class="nav-spacer"></div>
</div>
""",
    unsafe_allow_html=True,
)
render_logout()

# ── Client banner ────────────────────────────────────────────────────────────
try:
    from shared.client_banner import render_client_banner
    render_client_banner()
    if render_tool_help:
        render_tool_help("admin-panel")
    if render_feedback_button:
        render_feedback_button("admin-panel")
except Exception:
    pass

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Admin Panel")
    st.markdown("[Staff Dashboard](http://localhost:8502)")
    st.markdown("[Client Info](http://localhost:8512)")
    st.markdown("---")
    st.caption("Configure templates, lists, and settings for all office tools.")
    try:
        from shared.tool_notes import render_tool_notes
        render_tool_notes("admin-panel")
    except Exception:
        pass

# ── Tab navigation (main area) ───────────────────────────────────────────────
tab_tools, tab_integrations, tab_governance, tab_usage = st.tabs([
    "Tool Configuration",
    "Integrations",
    "Governance",
    "Usage & Billing",
])


# ═══════════════════════════════════════════════════════════════════════════════
# Helper: load tool defaults by importing from the actual domain module.
# We do lazy imports inside functions so the admin panel only needs streamlit.
# If a module can't be imported (missing deps), we return empty defaults.
# ═══════════════════════════════════════════════════════════════════════════════


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_module(tool_dir: str, module_file: str):
    """Load a Python module by file path using importlib (avoids 'app' package collision)."""
    file_path = _PROJECT_ROOT / tool_dir / "app" / module_file
    if not file_path.exists():
        return None
    # Ensure the tool's parent and shared/ are importable
    tool_root = str(_PROJECT_ROOT / tool_dir)
    shared_root = str(_PROJECT_ROOT)
    for p in (tool_root, shared_root):
        if p not in sys.path:
            sys.path.insert(0, p)
    mod_name = f"_admin_{tool_dir.replace('-', '_')}_{module_file.replace('.py', '')}"
    spec = importlib.util.spec_from_file_location(mod_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod  # register before exec so @dataclass can find it
    spec.loader.exec_module(mod)
    return mod


def _load_defaults(tool_name: str) -> dict:
    """Load hardcoded defaults from the domain module for initial population."""
    try:
        if tool_name == "case-checklist":
            mod = _load_module("case-checklist", "checklists.py")
            return {"case_types": mod.CASE_TYPES, "templates": mod._TEMPLATES}
        elif tool_name == "cover-letters":
            mod = _load_module("cover-letters", "templates.py")
            return {"filing_offices": mod.FILING_OFFICES, "templates": mod.TEMPLATES}
        elif tool_name == "declaration-drafter":
            mod = _load_module("declaration-drafter", "prompts.py")
            return {"declaration_types": mod.DECLARATION_TYPES, "prompts": mod.DECLARATION_PROMPTS}
        elif tool_name == "legal-research":
            mod = _load_module("legal-research", "case_law.py")
            from dataclasses import asdict
            decisions = {k: asdict(v) for k, v in mod.KEY_DECISIONS.items()}
            return {"decisions": decisions, "topics": mod.LEGAL_TOPICS}
        elif tool_name == "forms-assistant":
            mod = _load_module("forms-assistant", "form_definitions.py")
            return {"supported_forms": mod.SUPPORTED_FORMS}
        elif tool_name == "evidence-indexer":
            mod = _load_module("evidence-indexer", "evidence.py")
            return {"document_categories": mod.DOCUMENT_CATEGORIES}
        elif tool_name == "timeline-builder":
            mod = _load_module("timeline-builder", "events.py")
            return {"event_categories": mod.EVENT_CATEGORIES, "category_descriptions": mod.CATEGORY_DESCRIPTIONS}
        elif tool_name == "document-translator":
            mod = _load_module("document-translator", "translator.py")
            return {"languages": mod.LANGUAGES}
    except Exception:
        pass
    return {}


def _get_tool_config(tool_name: str) -> dict:
    """Load saved config, falling back to domain-module defaults."""
    saved = load_config(tool_name)
    if saved is not None:
        return saved
    return _load_defaults(tool_name)


# ═══════════════════════════════════════════════════════════════════════════════
# CASE CHECKLIST
# ═══════════════════════════════════════════════════════════════════════════════

def _editor_case_checklist():
    cfg = _get_tool_config("case-checklist")
    case_types: list[str] = cfg.get("case_types", [])
    templates: dict = cfg.get("templates", {})

    st.subheader("Case Types")

    # --- Editable list of case types ---
    edited_types = list(case_types)

    # Add new
    c1, c2 = st.columns([4, 1])
    with c1:
        new_type = st.text_input("New case type", key="cc_new_type", placeholder="e.g. TPS Application")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", key="cc_add_type") and new_type.strip():
            if new_type.strip() not in edited_types:
                edited_types.append(new_type.strip())
                templates.setdefault(new_type.strip(), [])

    # Show / delete existing
    to_delete = []
    for i, ct in enumerate(edited_types):
        c1, c2 = st.columns([8, 1])
        with c1:
            st.text(ct)
        with c2:
            if st.button("X", key=f"cc_del_{i}"):
                to_delete.append(ct)
    for d in to_delete:
        edited_types.remove(d)
        templates.pop(d, None)

    st.divider()
    st.subheader("Checklist Templates")

    if edited_types:
        sel_type = st.selectbox("Select case type", edited_types, key="cc_sel_type")
        items = templates.get(sel_type, [])

        # Show items in a table-like format
        st.caption(f"{len(items)} template items")
        updated_items = []
        items_to_remove = []
        for j, item in enumerate(items):
            c1, c2, c3 = st.columns([5, 3, 1])
            with c1:
                title = st.text_input("Title", value=item.get("title", ""), key=f"cc_item_t_{sel_type}_{j}", label_visibility="collapsed")
            with c2:
                cats = ["Filing", "Evidence", "Preparation", "Administrative"]
                cur_cat = item.get("category", "Filing")
                idx = cats.index(cur_cat) if cur_cat in cats else 0
                cat = st.selectbox("Cat", cats, index=idx, key=f"cc_item_c_{sel_type}_{j}", label_visibility="collapsed")
            with c3:
                if st.button("X", key=f"cc_item_del_{sel_type}_{j}"):
                    items_to_remove.append(j)
            if j not in items_to_remove:
                updated_items.append({"title": title, "category": cat})

        # Add new item
        c1, c2, c3 = st.columns([5, 3, 1])
        with c1:
            new_title = st.text_input("New item title", key=f"cc_new_item_{sel_type}", placeholder="New checklist item")
        with c2:
            new_cat = st.selectbox("Category", ["Filing", "Evidence", "Preparation", "Administrative"], key=f"cc_new_cat_{sel_type}")
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("+", key=f"cc_add_item_{sel_type}") and new_title.strip():
                updated_items.append({"title": new_title.strip(), "category": new_cat})

        templates[sel_type] = updated_items

    if st.button("Save Case Checklist Config", type="primary", key="cc_save"):
        save_config("case-checklist", {"case_types": edited_types, "templates": templates})
        st.toast("Case Checklist config saved!")


# ═══════════════════════════════════════════════════════════════════════════════
# COVER PAGES
# ═══════════════════════════════════════════════════════════════════════════════

def _editor_cover_letters():
    cfg = _get_tool_config("cover-letters")
    filing_offices: dict = cfg.get("filing_offices", {})
    templates: dict = cfg.get("templates", {})

    st.subheader("Filing Offices")

    office_names = list(filing_offices.keys())

    # Add new office
    c1, c2 = st.columns([3, 1])
    with c1:
        new_office = st.text_input("New office name", key="cl_new_office")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", key="cl_add_office") and new_office.strip():
            if new_office.strip() not in office_names:
                office_names.append(new_office.strip())
                filing_offices[new_office.strip()] = ""

    offices_to_delete = []
    for i, name in enumerate(office_names):
        with st.expander(name):
            addr = st.text_area("Address", value=filing_offices.get(name, ""), key=f"cl_addr_{i}", height=80)
            filing_offices[name] = addr
            if st.button("Delete office", key=f"cl_del_office_{i}"):
                offices_to_delete.append(name)
    for d in offices_to_delete:
        office_names.remove(d)
        del filing_offices[d]

    st.divider()
    st.subheader("Templates by Case Type")

    case_types = list(templates.keys())

    if case_types:
        sel_ct = st.selectbox("Select case type", case_types, key="cl_sel_ct")
        tpl = templates.get(sel_ct, {})

        # Form numbers
        form_nums = tpl.get("form_numbers", [])
        forms_str = st.text_input("Form numbers (comma-separated)", value=", ".join(form_nums), key=f"cl_forms_{sel_ct}")
        tpl["form_numbers"] = [f.strip() for f in forms_str.split(",") if f.strip()]

        # Filing offices for this type
        tpl_offices = tpl.get("filing_offices", [])
        sel_offices = st.multiselect("Filing offices", options=office_names, default=[o for o in tpl_offices if o in office_names], key=f"cl_tpl_offices_{sel_ct}")
        tpl["filing_offices"] = sel_offices

        # Standard enclosed docs
        docs = tpl.get("standard_enclosed_docs", [])
        docs_text = st.text_area("Standard enclosed docs (one per line)", value="\n".join(docs), key=f"cl_docs_{sel_ct}", height=150)
        tpl["standard_enclosed_docs"] = [d.strip() for d in docs_text.strip().splitlines() if d.strip()]

        # Paragraphs
        tpl["purpose_paragraph"] = st.text_area("Purpose paragraph", value=tpl.get("purpose_paragraph", ""), key=f"cl_purpose_{sel_ct}", height=100)
        tpl["closing_paragraph"] = st.text_area("Closing paragraph", value=tpl.get("closing_paragraph", ""), key=f"cl_closing_{sel_ct}", height=100)

        # Preserve extra fields (confidentiality_notice, certificate_of_service, etc.)
        templates[sel_ct] = tpl

    if st.button("Save Cover Pages Config", type="primary", key="cl_save"):
        save_config("cover-letters", {"filing_offices": filing_offices, "templates": templates})
        st.toast("Cover Pages config saved!")


# ═══════════════════════════════════════════════════════════════════════════════
# DECLARATION DRAFTER
# ═══════════════════════════════════════════════════════════════════════════════

def _editor_declaration_drafter():
    cfg = _get_tool_config("declaration-drafter")
    decl_types: list = cfg.get("declaration_types", [])
    prompts: dict = cfg.get("prompts", {})

    st.subheader("Declaration Types")

    edited_types = list(decl_types)
    c1, c2 = st.columns([4, 1])
    with c1:
        new_dt = st.text_input("New declaration type", key="dd_new_type")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", key="dd_add_type") and new_dt.strip():
            if new_dt.strip() not in edited_types:
                edited_types.append(new_dt.strip())
                prompts.setdefault(new_dt.strip(), [])

    to_delete = []
    for i, dt in enumerate(edited_types):
        c1, c2 = st.columns([8, 1])
        with c1:
            st.text(dt)
        with c2:
            if st.button("X", key=f"dd_del_{i}"):
                to_delete.append(dt)
    for d in to_delete:
        edited_types.remove(d)
        prompts.pop(d, None)

    st.divider()
    st.subheader("Prompts")

    if edited_types:
        sel_dt = st.selectbox("Select declaration type", edited_types, key="dd_sel_type")
        sections = prompts.get(sel_dt, [])

        sec_to_delete = []
        for si, section in enumerate(sections):
            with st.expander(section.get("title", f"Section {si + 1}")):
                section["title"] = st.text_input("Section title", value=section.get("title", ""), key=f"dd_sec_t_{sel_dt}_{si}")
                section["instructions"] = st.text_area("Instructions", value=section.get("instructions", ""), key=f"dd_sec_i_{sel_dt}_{si}", height=80)

                questions = section.get("questions", [])
                q_to_remove = []
                for qi, q in enumerate(questions):
                    st.markdown(f"**Q{qi + 1}**")
                    q["id"] = st.text_input("ID", value=q.get("id", ""), key=f"dd_q_id_{sel_dt}_{si}_{qi}")
                    q["label"] = st.text_input("Label", value=q.get("label", ""), key=f"dd_q_l_{sel_dt}_{si}_{qi}")
                    q["tip"] = st.text_area("Attorney tip", value=q.get("tip", ""), key=f"dd_q_tip_{sel_dt}_{si}_{qi}", height=80)
                    if st.button("Delete question", key=f"dd_q_del_{sel_dt}_{si}_{qi}"):
                        q_to_remove.append(qi)
                    st.markdown("---")

                for qi in sorted(q_to_remove, reverse=True):
                    questions.pop(qi)

                # Add question
                if st.button("+ Add question", key=f"dd_q_add_{sel_dt}_{si}"):
                    questions.append({"id": "", "label": "", "tip": ""})
                section["questions"] = questions

                # Delete section
                if st.button("Delete section", key=f"dd_sec_del_{sel_dt}_{si}"):
                    sec_to_delete.append(si)

        for si in sorted(sec_to_delete, reverse=True):
            sections.pop(si)

        # Add section
        if st.button("+ Add section", key=f"dd_sec_add_{sel_dt}"):
            sections.append({"title": "", "instructions": "", "questions": []})
        prompts[sel_dt] = sections

    if st.button("Save Declaration Drafter Config", type="primary", key="dd_save"):
        save_config("declaration-drafter", {"declaration_types": edited_types, "prompts": prompts})
        st.toast("Declaration Drafter config saved!")


# ═══════════════════════════════════════════════════════════════════════════════
# LEGAL RESEARCH
# ═══════════════════════════════════════════════════════════════════════════════

def _editor_legal_research():
    cfg = _get_tool_config("legal-research")
    decisions: dict = cfg.get("decisions", {})
    topics: list = cfg.get("topics", [])

    st.subheader("Legal Topics")

    edited_topics = list(topics)
    c1, c2 = st.columns([4, 1])
    with c1:
        new_topic = st.text_input("New topic", key="lr_new_topic")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", key="lr_add_topic") and new_topic.strip():
            if new_topic.strip() not in edited_topics:
                edited_topics.append(new_topic.strip())

    topics_to_del = []
    for i, t in enumerate(edited_topics):
        c1, c2 = st.columns([8, 1])
        with c1:
            st.text(t)
        with c2:
            if st.button("X", key=f"lr_del_topic_{i}"):
                topics_to_del.append(t)
    for d in topics_to_del:
        edited_topics.remove(d)

    st.divider()
    st.subheader("Key Decisions")

    dec_keys = list(decisions.keys())
    decs_to_delete = []

    for dk in dec_keys:
        dec = decisions[dk]
        with st.expander(f"{dec.get('name', dk)} — {dec.get('citation', '')}"):
            dec["name"] = st.text_input("Name", value=dec.get("name", ""), key=f"lr_name_{dk}")
            dec["citation"] = st.text_input("Citation", value=dec.get("citation", ""), key=f"lr_cite_{dk}")
            dec["court"] = st.text_input("Court", value=dec.get("court", ""), key=f"lr_court_{dk}")
            dec["date"] = st.text_input("Date", value=dec.get("date", ""), key=f"lr_date_{dk}")
            dec["holding"] = st.text_area("Holding", value=dec.get("holding", ""), key=f"lr_hold_{dk}", height=120)
            dec_topics = dec.get("topics", [])
            dec["topics"] = st.multiselect("Topics", options=edited_topics, default=[t for t in dec_topics if t in edited_topics], key=f"lr_topics_{dk}")
            if st.button("Delete decision", key=f"lr_del_{dk}"):
                decs_to_delete.append(dk)

    for dk in decs_to_delete:
        del decisions[dk]

    # Add new decision
    st.markdown("---")
    st.caption("Add new decision")
    new_key = st.text_input("Key (slug)", key="lr_new_key", placeholder="e.g. matter-of-xyz")
    new_name = st.text_input("Case name", key="lr_new_name")
    new_cite = st.text_input("Citation", key="lr_new_cite")
    if st.button("Add decision", key="lr_add_dec") and new_key.strip() and new_name.strip():
        decisions[new_key.strip()] = {
            "name": new_name.strip(),
            "citation": new_cite.strip(),
            "court": "",
            "date": "",
            "holding": "",
            "full_text": "",
            "topics": [],
        }

    if st.button("Save Legal Research Config", type="primary", key="lr_save"):
        save_config("legal-research", {"decisions": decisions, "topics": edited_topics})
        st.toast("Legal Research config saved!")


# ═══════════════════════════════════════════════════════════════════════════════
# FORMS ASSISTANT
# ═══════════════════════════════════════════════════════════════════════════════

def _editor_forms_assistant():
    cfg = _get_tool_config("forms-assistant")
    forms: dict = cfg.get("supported_forms", {})
    uploaded_forms: dict = cfg.get("uploaded_forms", {})
    deleted_forms: list = cfg.get("deleted_forms", [])

    # Load preparer and attorney stores
    sys.path.insert(0, str(_PROJECT_ROOT))
    from shared.preparer_store import load_preparers, save_preparers, new_preparer_id
    from shared.attorney_store import load_attorneys, save_attorneys, new_attorney_id
    from shared.pdf_form_extractor import ALL_ROLES, SF_FIELD_LABELS

    # --- Tabs for sub-sections ---
    tab_forms, tab_upload, tab_fields, tab_preparers, tab_attorneys = st.tabs(
        ["Forms", "Upload PDF", "Field Editor", "Preparers", "Attorneys"]
    )

    # ── Tab 1: Form List with Delete ────────────────────────────────────────
    with tab_forms:
        st.subheader("All Forms")
        st.caption("Hardcoded forms and uploaded PDF forms. Delete removes uploaded forms entirely; hardcoded forms are hidden.")

        # Hardcoded forms
        st.markdown("**Hardcoded Forms**")
        hardcoded_ids = list(forms.keys())
        for fid in hardcoded_ids:
            fm = forms[fid]
            is_deleted = fid in deleted_forms
            c1, c2, c3 = st.columns([5, 2, 1])
            with c1:
                label = f"~~{fid} — {fm.get('title', '')}~~" if is_deleted else f"{fid} — {fm.get('title', '')}"
                st.markdown(label)
            with c2:
                st.caption("Hidden" if is_deleted else "Active")
            with c3:
                if is_deleted:
                    if st.button("Restore", key=f"fa_restore_{fid}"):
                        deleted_forms.remove(fid)
                        st.rerun()
                else:
                    if st.button("Hide", key=f"fa_hide_{fid}"):
                        deleted_forms.append(fid)
                        st.rerun()

        # Uploaded forms
        if uploaded_forms:
            st.markdown("---")
            st.markdown("**Uploaded PDF Forms**")
            uploaded_to_delete = []
            for fid, fm in uploaded_forms.items():
                is_deleted = fid in deleted_forms
                c1, c2, c3 = st.columns([5, 2, 1])
                with c1:
                    field_count = len(fm.get("fields", []))
                    label = f"{fid} — {fm.get('title', '')} ({field_count} fields)"
                    if is_deleted:
                        label = f"~~{label}~~"
                    st.markdown(label)
                with c2:
                    st.caption("Hidden" if is_deleted else "Active")
                with c3:
                    if st.button("Delete", key=f"fa_del_uploaded_{fid}"):
                        uploaded_to_delete.append(fid)

            if uploaded_to_delete:
                for fid in uploaded_to_delete:
                    del uploaded_forms[fid]
                    if fid in deleted_forms:
                        deleted_forms.remove(fid)
                    # Delete template PDF
                    tpl_path = _PROJECT_ROOT / "forms-assistant" / "data" / "form_templates" / f"{fid}.pdf"
                    if tpl_path.exists():
                        tpl_path.unlink()
                st.rerun()

        # Hardcoded form metadata editor
        st.markdown("---")
        st.subheader("Edit Form Metadata")
        active_hardcoded = [fid for fid in hardcoded_ids if fid not in deleted_forms]
        if active_hardcoded:
            for fid in active_hardcoded:
                fm = forms[fid]
                with st.expander(f"{fid} — {fm.get('title', '')}"):
                    fm["title"] = st.text_input("Title", value=fm.get("title", ""), key=f"fa_title_{fid}")
                    fm["agency"] = st.text_input("Agency", value=fm.get("agency", ""), key=f"fa_agency_{fid}")
                    fm["filing_fee"] = st.text_input("Filing fee", value=fm.get("filing_fee", ""), key=f"fa_fee_{fid}")
                    fm["processing_time"] = st.text_input("Processing time", value=fm.get("processing_time", ""), key=f"fa_proc_{fid}")
                    sections = fm.get("sections", [])
                    sections_text = st.text_area("Sections (one per line)", value="\n".join(sections), key=f"fa_secs_{fid}", height=120)
                    fm["sections"] = [s.strip() for s in sections_text.strip().splitlines() if s.strip()]

        if st.button("Save Forms Config", type="primary", key="fa_save"):
            save_config("forms-assistant", {
                "supported_forms": forms,
                "uploaded_forms": uploaded_forms,
                "deleted_forms": deleted_forms,
            })
            st.toast("Forms config saved!")

    # ── Tab 2: PDF Upload ───────────────────────────────────────────────────
    with tab_upload:
        st.subheader("Upload USCIS PDF Form")
        st.caption("Upload a fillable PDF to auto-extract its fields. The form will appear in the Forms Assistant.")

        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], key="fa_pdf_upload")

        if uploaded_file is not None:
            pdf_bytes = uploaded_file.read()

            # Extract fields
            try:
                from shared.pdf_form_extractor import extract_form_fields, auto_suggest_roles
                fields = extract_form_fields(pdf_bytes)
                # Auto-suggest roles based on field labels
                if fields:
                    auto_suggest_roles(fields)
            except Exception as e:
                st.error(f"Failed to extract fields: {e}")
                fields = []

            if fields:
                # Summary
                type_counts: dict[str, int] = {}
                for f in fields:
                    ft = f["field_type"]
                    type_counts[ft] = type_counts.get(ft, 0) + 1
                summary_parts = [f"{count} {ftype}" for ftype, count in type_counts.items()]
                st.success(f"Extracted {len(fields)} fields: {', '.join(summary_parts)}")

                # Auto-suggest summary
                role_count = sum(1 for f in fields if f.get("role", "none") != "none")
                sf_count = sum(1 for f in fields if f.get("sf_field", ""))
                suggested_count = role_count + sf_count
                if suggested_count:
                    pct = round(suggested_count / len(fields) * 100)
                    parts = []
                    if sf_count:
                        parts.append(f"{sf_count} SF field(s)")
                    if role_count:
                        parts.append(f"{role_count} role(s)")
                    st.info(f"Auto-mapped {suggested_count} fields ({pct}%): {', '.join(parts)}")

                # Show preview of first 20 fields
                with st.expander(f"Preview fields (showing first {min(20, len(fields))} of {len(fields)})"):
                    for f in fields[:20]:
                        st.text(f"{f['display_label']} ({f['field_type']}) — {f['pdf_field_name']}")

                # Form metadata input
                st.markdown("---")
                st.markdown("**Form Details**")
                form_id = st.text_input("Form ID", placeholder="e.g. I-589-PDF", key="fa_upload_id")
                form_title = st.text_input("Title", placeholder="e.g. Application for Asylum", key="fa_upload_title")
                form_agency = st.text_input("Agency", value="USCIS", key="fa_upload_agency")
                form_fee = st.text_input("Filing Fee", key="fa_upload_fee")
                form_proc = st.text_input("Processing Time", key="fa_upload_proc")

                if st.button("Save Uploaded Form", type="primary", key="fa_upload_save"):
                    if not form_id.strip():
                        st.error("Form ID is required.")
                    elif not form_title.strip():
                        st.error("Title is required.")
                    elif form_id.strip() in uploaded_forms or form_id.strip() in forms:
                        st.error(f"Form ID '{form_id.strip()}' already exists.")
                    else:
                        fid = form_id.strip()

                        # Save PDF template
                        tpl_dir = _PROJECT_ROOT / "forms-assistant" / "data" / "form_templates"
                        tpl_dir.mkdir(parents=True, exist_ok=True)
                        (tpl_dir / f"{fid}.pdf").write_bytes(pdf_bytes)

                        # Save form config
                        uploaded_forms[fid] = {
                            "title": form_title.strip(),
                            "agency": form_agency.strip(),
                            "filing_fee": form_fee.strip(),
                            "processing_time": form_proc.strip(),
                            "sections": sorted(set(f["section"] for f in fields)),
                            "fields": fields,
                            "_uploaded": True,
                        }
                        save_config("forms-assistant", {
                            "supported_forms": forms,
                            "uploaded_forms": uploaded_forms,
                            "deleted_forms": deleted_forms,
                        })
                        st.toast(f"Form {fid} saved with {len(fields)} fields!")
                        st.rerun()
            elif uploaded_file:
                st.warning("No fillable fields found in this PDF. Make sure it's an AcroForm PDF.")

    # ── Tab 3: Field Editor ─────────────────────────────────────────────────
    with tab_fields:
        st.subheader("Edit Uploaded Form Fields")
        st.caption("Rename labels, assign sections, map to Salesforce fields, tag preparer/attorney roles, and delete individual fields.")

        if not uploaded_forms:
            st.info("No uploaded forms yet. Upload a PDF first.")
        else:
            upload_ids = list(uploaded_forms.keys())
            sel_form = st.selectbox("Select uploaded form", upload_ids, key="fa_field_sel")
            form_cfg = uploaded_forms[sel_form]
            fields = form_cfg.get("fields", [])

            if not fields:
                st.info("This form has no extracted fields.")
            else:
                # Migrate old client_* roles to sf_field
                _OLD_ROLE_TO_SF = {
                    "client_first_name": "FirstName",
                    "client_last_name": "LastName",
                    "client_middle_name": "",
                    "client_dob": "Birthdate",
                    "client_a_number": "A_Number__c",
                    "client_ssn": "",
                    "client_gender": "Gender__c",
                    "client_marital_status": "Marital_status__c",
                    "client_country_of_nationality": "Country__c",
                    "client_country_of_birth": "Country__c",
                    "client_city_of_birth": "City_of_Birth__c",
                    "client_email": "Email",
                    "client_phone": "Phone",
                    "client_mobile": "MobilePhone",
                    "client_street": "MailingStreet",
                    "client_city": "MailingCity",
                    "client_state": "MailingState",
                    "client_zip": "MailingPostalCode",
                    "client_immigration_status": "Immigration_Status__c",
                    "client_last_entry_date": "Date_of_Most_Recent_US_Entry__c",
                    "client_entry_status": "Status_of_Last_Arrival__c",
                    "client_entry_place": "Place_of_Last_Arrival__c",
                    "client_language": "Best_Language__c",
                    "client_spouse_name": "Spouse_Name__c",
                }
                migrated = 0
                for fd in fields:
                    old_role = fd.get("role", "none")
                    if old_role.startswith("client_") and not fd.get("sf_field"):
                        sf = _OLD_ROLE_TO_SF.get(old_role, "")
                        if sf:
                            fd["sf_field"] = sf
                        fd["role"] = "none"
                        migrated += 1
                    # Ensure sf_field key exists on older records
                    if "sf_field" not in fd:
                        fd["sf_field"] = ""
                if migrated:
                    st.info(f"Migrated {migrated} client role(s) to direct SF field mappings.")

                role_options = ALL_ROLES
                sf_options = [""] + sorted(SF_FIELD_LABELS.keys())

                st.caption(f"{len(fields)} fields")

                # Bulk assign sections by page
                if st.button("Auto-assign sections by page", key="fa_auto_sections"):
                    for f in fields:
                        f["section"] = f"Page {f.get('page_number', 0) + 1}"
                    st.rerun()

                fields_to_delete: list[int] = []

                for idx, fd in enumerate(fields):
                    with st.expander(f"{fd.get('display_label', '')} — {fd.get('field_type', 'text')} ({fd['pdf_field_name']})"):
                        c1, c2 = st.columns(2)
                        with c1:
                            fd["display_label"] = st.text_input(
                                "Display Label",
                                value=fd.get("display_label", ""),
                                key=f"fa_fl_{sel_form}_{idx}",
                            )
                        with c2:
                            fd["section"] = st.text_input(
                                "Section",
                                value=fd.get("section", "Page 1"),
                                key=f"fa_fs_{sel_form}_{idx}",
                            )
                        c3, c4 = st.columns(2)
                        with c3:
                            cur_sf = fd.get("sf_field", "")
                            sf_idx = sf_options.index(cur_sf) if cur_sf in sf_options else 0
                            fd["sf_field"] = st.selectbox(
                                "Salesforce Field",
                                sf_options,
                                index=sf_idx,
                                format_func=lambda x: f"{SF_FIELD_LABELS[x]} ({x})" if x else "(none)",
                                key=f"fa_fsf_{sel_form}_{idx}",
                            )
                        with c4:
                            cur_role = fd.get("role", "none")
                            role_idx = role_options.index(cur_role) if cur_role in role_options else 0
                            fd["role"] = st.selectbox(
                                "Role (preparer/attorney)",
                                role_options,
                                index=role_idx,
                                key=f"fa_fr_{sel_form}_{idx}",
                            )
                        c5, c6, c7 = st.columns(3)
                        with c5:
                            fd["required"] = st.checkbox(
                                "Required",
                                value=fd.get("required", False),
                                key=f"fa_freq_{sel_form}_{idx}",
                            )
                        with c6:
                            fd["help_text"] = st.text_input(
                                "Help text",
                                value=fd.get("help_text", ""),
                                key=f"fa_fh_{sel_form}_{idx}",
                            )
                        with c7:
                            if st.button("Delete field", key=f"fa_fdel_{sel_form}_{idx}"):
                                fields_to_delete.append(idx)

                # Process deletions in reverse to preserve indices
                if fields_to_delete:
                    for idx in sorted(fields_to_delete, reverse=True):
                        fields.pop(idx)
                    form_cfg["fields"] = fields
                    form_cfg["sections"] = sorted(set(f.get("section", "Page 1") for f in fields))
                    save_config("forms-assistant", {
                        "supported_forms": forms,
                        "uploaded_forms": uploaded_forms,
                        "deleted_forms": deleted_forms,
                    })
                    st.toast(f"Deleted {len(fields_to_delete)} field(s).")
                    st.rerun()

                form_cfg["fields"] = fields
                # Update sections list from fields
                form_cfg["sections"] = sorted(set(f.get("section", "Page 1") for f in fields))

                if st.button("Save Field Changes", type="primary", key="fa_field_save"):
                    save_config("forms-assistant", {
                        "supported_forms": forms,
                        "uploaded_forms": uploaded_forms,
                        "deleted_forms": deleted_forms,
                    })
                    st.toast("Field changes saved!")

    # ── Tab 4: Preparers ────────────────────────────────────────────────────
    with tab_preparers:
        st.subheader("Office Preparers")
        st.caption("Manage preparers whose info auto-fills preparer-tagged fields on uploaded forms.")

        preparers = load_preparers()

        # Add new preparer
        st.markdown("**Add New Preparer**")
        c1, c2 = st.columns(2)
        with c1:
            new_p_name = st.text_input("Name", key="fa_prep_name")
            new_p_firm = st.text_input("Firm", key="fa_prep_firm")
            new_p_bar = st.text_input("Bar Number", key="fa_prep_bar")
        with c2:
            new_p_phone = st.text_input("Phone", key="fa_prep_phone")
            new_p_email = st.text_input("Email", key="fa_prep_email")
            new_p_addr = st.text_input("Address", key="fa_prep_addr")

        if st.button("Add Preparer", key="fa_prep_add") and new_p_name.strip():
            preparers.append({
                "id": new_preparer_id(),
                "name": new_p_name.strip(),
                "firm": new_p_firm.strip(),
                "bar_number": new_p_bar.strip(),
                "phone": new_p_phone.strip(),
                "email": new_p_email.strip(),
                "address": new_p_addr.strip(),
            })
            save_preparers(preparers)
            st.toast(f"Added preparer: {new_p_name.strip()}")
            st.rerun()

        # List existing preparers
        if preparers:
            st.markdown("---")
            st.markdown("**Existing Preparers**")
            preps_to_delete = []
            for pi, prep in enumerate(preparers):
                with st.expander(f"{prep.get('name', 'Unnamed')} — {prep.get('firm', '')}"):
                    prep["name"] = st.text_input("Name", value=prep.get("name", ""), key=f"fa_pe_n_{pi}")
                    prep["firm"] = st.text_input("Firm", value=prep.get("firm", ""), key=f"fa_pe_f_{pi}")
                    prep["bar_number"] = st.text_input("Bar Number", value=prep.get("bar_number", ""), key=f"fa_pe_b_{pi}")
                    prep["phone"] = st.text_input("Phone", value=prep.get("phone", ""), key=f"fa_pe_p_{pi}")
                    prep["email"] = st.text_input("Email", value=prep.get("email", ""), key=f"fa_pe_e_{pi}")
                    prep["address"] = st.text_input("Address", value=prep.get("address", ""), key=f"fa_pe_a_{pi}")
                    if st.button("Delete", key=f"fa_pe_del_{pi}"):
                        preps_to_delete.append(pi)

            for pi in sorted(preps_to_delete, reverse=True):
                preparers.pop(pi)

            if st.button("Save Preparers", type="primary", key="fa_prep_save"):
                save_preparers(preparers)
                st.toast("Preparers saved!")

    # ── Tab 5: Attorneys ────────────────────────────────────────────────────
    with tab_attorneys:
        st.subheader("Office Attorneys")
        st.caption("Manage attorneys of record whose info auto-fills attorney-tagged fields on uploaded forms.")

        attorneys = load_attorneys()

        # Add new attorney
        st.markdown("**Add New Attorney**")
        c1, c2 = st.columns(2)
        with c1:
            new_a_name = st.text_input("Name", key="fa_atty_name")
            new_a_firm = st.text_input("Firm", key="fa_atty_firm")
            new_a_bar = st.text_input("Bar Number", key="fa_atty_bar")
        with c2:
            new_a_phone = st.text_input("Phone", key="fa_atty_phone")
            new_a_email = st.text_input("Email", key="fa_atty_email")
            new_a_addr = st.text_input("Address", key="fa_atty_addr")

        if st.button("Add Attorney", key="fa_atty_add") and new_a_name.strip():
            attorneys.append({
                "id": new_attorney_id(),
                "name": new_a_name.strip(),
                "firm": new_a_firm.strip(),
                "bar_number": new_a_bar.strip(),
                "phone": new_a_phone.strip(),
                "email": new_a_email.strip(),
                "address": new_a_addr.strip(),
            })
            save_attorneys(attorneys)
            st.toast(f"Added attorney: {new_a_name.strip()}")
            st.rerun()

        # List existing attorneys
        if attorneys:
            st.markdown("---")
            st.markdown("**Existing Attorneys**")
            attys_to_delete = []
            for ai, atty in enumerate(attorneys):
                with st.expander(f"{atty.get('name', 'Unnamed')} — {atty.get('firm', '')}"):
                    atty["name"] = st.text_input("Name", value=atty.get("name", ""), key=f"fa_ae_n_{ai}")
                    atty["firm"] = st.text_input("Firm", value=atty.get("firm", ""), key=f"fa_ae_f_{ai}")
                    atty["bar_number"] = st.text_input("Bar Number", value=atty.get("bar_number", ""), key=f"fa_ae_b_{ai}")
                    atty["phone"] = st.text_input("Phone", value=atty.get("phone", ""), key=f"fa_ae_p_{ai}")
                    atty["email"] = st.text_input("Email", value=atty.get("email", ""), key=f"fa_ae_e_{ai}")
                    atty["address"] = st.text_input("Address", value=atty.get("address", ""), key=f"fa_ae_a_{ai}")
                    if st.button("Delete", key=f"fa_ae_del_{ai}"):
                        attys_to_delete.append(ai)

            for ai in sorted(attys_to_delete, reverse=True):
                attorneys.pop(ai)

            if st.button("Save Attorneys", type="primary", key="fa_atty_save"):
                save_attorneys(attorneys)
                st.toast("Attorneys saved!")


# ═══════════════════════════════════════════════════════════════════════════════
# EVIDENCE INDEXER
# ═══════════════════════════════════════════════════════════════════════════════

def _editor_evidence_indexer():
    cfg = _get_tool_config("evidence-indexer")
    categories: list = cfg.get("document_categories", [])

    st.subheader("Document Categories")

    edited_cats = list(categories)

    c1, c2 = st.columns([4, 1])
    with c1:
        new_cat = st.text_input("New category", key="ei_new_cat", placeholder="e.g. News Articles")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", key="ei_add_cat") and new_cat.strip():
            if new_cat.strip() not in edited_cats:
                edited_cats.append(new_cat.strip())

    cats_to_del = []
    for i, cat in enumerate(edited_cats):
        c1, c2, c3 = st.columns([1, 7, 1])
        with c1:
            st.text(f"{i + 1}.")
        with c2:
            st.text(cat)
        with c3:
            if st.button("X", key=f"ei_del_{i}"):
                cats_to_del.append(cat)
    for d in cats_to_del:
        edited_cats.remove(d)

    if st.button("Save Evidence Indexer Config", type="primary", key="ei_save"):
        save_config("evidence-indexer", {"document_categories": edited_cats})
        st.toast("Evidence Indexer config saved!")


# ═══════════════════════════════════════════════════════════════════════════════
# TIMELINE BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def _editor_timeline_builder():
    cfg = _get_tool_config("timeline-builder")
    event_cats: dict = cfg.get("event_categories", {})
    cat_descs: dict = cfg.get("category_descriptions", {})

    st.subheader("Event Categories")

    cat_names = list(event_cats.keys())

    # Add new category
    c1, c2 = st.columns([3, 1])
    with c1:
        new_cat_name = st.text_input("New category name", key="tb_new_cat")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", key="tb_add_cat") and new_cat_name.strip():
            if new_cat_name.strip() not in cat_names:
                cat_names.append(new_cat_name.strip())
                event_cats[new_cat_name.strip()] = "#6c757d"
                cat_descs[new_cat_name.strip()] = ""

    cats_to_del = []
    for i, cn in enumerate(cat_names):
        c1, c2, c3, c4 = st.columns([3, 1, 4, 1])
        with c1:
            st.text(cn)
        with c2:
            color = st.color_picker("Color", value=event_cats.get(cn, "#6c757d"), key=f"tb_color_{i}")
            event_cats[cn] = color
        with c3:
            desc = st.text_input("Description", value=cat_descs.get(cn, ""), key=f"tb_desc_{i}", label_visibility="collapsed")
            cat_descs[cn] = desc
        with c4:
            if st.button("X", key=f"tb_del_{i}"):
                cats_to_del.append(cn)

    for d in cats_to_del:
        cat_names.remove(d)
        event_cats.pop(d, None)
        cat_descs.pop(d, None)

    if st.button("Save Timeline Builder Config", type="primary", key="tb_save"):
        save_config("timeline-builder", {"event_categories": event_cats, "category_descriptions": cat_descs})
        st.toast("Timeline Builder config saved!")


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENT TRANSLATOR
# ═══════════════════════════════════════════════════════════════════════════════

def _editor_document_translator():
    cfg = _get_tool_config("document-translator")
    languages: dict = cfg.get("languages", {})

    st.subheader("Languages")

    codes = list(languages.keys())

    # Add new language
    c1, c2, c3 = st.columns([2, 3, 1])
    with c1:
        new_code = st.text_input("Code", key="dt_new_code", placeholder="e.g. ml")
    with c2:
        new_name = st.text_input("Display name", key="dt_new_name", placeholder="e.g. Malayalam")
    with c3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", key="dt_add_lang") and new_code.strip() and new_name.strip():
            if new_code.strip() not in codes:
                codes.append(new_code.strip())
                languages[new_code.strip()] = new_name.strip()

    langs_to_del = []
    for i, code in enumerate(codes):
        c1, c2, c3 = st.columns([2, 6, 1])
        with c1:
            st.code(code)
        with c2:
            display = st.text_input("Name", value=languages[code], key=f"dt_name_{i}", label_visibility="collapsed")
            languages[code] = display
        with c3:
            if st.button("X", key=f"dt_del_{i}"):
                langs_to_del.append(code)
    for d in langs_to_del:
        codes.remove(d)
        del languages[d]

    if st.button("Save Document Translator Config", type="primary", key="dt_save"):
        save_config("document-translator", {"languages": languages})
        st.toast("Document Translator config saved!")


# ═══════════════════════════════════════════════════════════════════════════════
# SALESFORCE FIELDS
# ═══════════════════════════════════════════════════════════════════════════════

# Fields currently shown in Client Info, grouped the same way
_CLIENT_INFO_FIELD_GROUPS = {
    "Identity": [
        "FirstName", "LastName", "A_Number__c", "Birthdate",
        "Gender__c", "Pronoun__c", "Marital_status__c",
    ],
    "Contact Information": [
        "Email", "MobilePhone", "Phone",
        "MailingStreet", "MailingCity", "MailingState",
        "MailingPostalCode", "MailingCountry",
    ],
    "Immigration Details": [
        "Country__c", "City_of_Birth__c", "Best_Language__c",
        "Immigration_Status__c", "Immigration_Court__c",
        "Legal_Case_Type__c", "Client_Status__c",
        "Date_of_First_Entry_to_US__c", "Date_of_Most_Recent_US_Entry__c",
        "Status_of_Last_Arrival__c", "Place_of_Last_Arrival__c",
    ],
    "Family": [
        "Spouse_Name__c", "Mother_s_First_Name__c", "Mother_s_Last_Name__c",
        "Father_s_First_Name__c", "Father_s_Last_Name__c",
    ],
    "Case Information": [
        "CaseNumber__c", "Client_Case_Strategy__c", "Nexus__c", "PSG__c",
        "Box_Folder_Id__c",
    ],
}


def _editor_salesforce_fields():
    cfg = load_config("salesforce") or {}
    disabled_fields: list[str] = cfg.get("disabled_fields", [])

    st.subheader("Salesforce Field Permissions")
    st.caption(
        "Control which Contact fields the Client Info tool can push back to Salesforce. "
        "Turn off any field that causes permission errors. Changes take effect immediately on save."
    )

    # Try to pull live field metadata from Salesforce
    sf_meta = {}
    if st.button("Refresh field metadata from Salesforce", key="sf_refresh"):
        try:
            sys.path.insert(0, str(_PROJECT_ROOT))
            from shared.salesforce_client import get_field_metadata
            sf_meta = get_field_metadata()
            st.session_state._sf_field_meta = sf_meta
            st.toast(f"Loaded metadata for {len(sf_meta)} fields")
        except Exception as e:
            st.error(f"Could not connect to Salesforce: {e}")

    if "_sf_field_meta" in st.session_state:
        sf_meta = st.session_state._sf_field_meta

    # Show fields by group
    updated_disabled = list(disabled_fields)

    for group_name, api_names in _CLIENT_INFO_FIELD_GROUPS.items():
        st.markdown(f"**{group_name}**")
        for api_name in api_names:
            meta = sf_meta.get(api_name, {})
            label = meta.get("label", api_name)
            ftype = meta.get("type", "")
            sf_updateable = meta.get("updateable", None)

            # Build display string
            info_parts = [f"`{api_name}`"]
            if ftype:
                info_parts.append(f"({ftype})")
            if sf_updateable is False:
                info_parts.append("**[read-only in SF]**")

            is_enabled = api_name not in updated_disabled

            col1, col2 = st.columns([6, 2])
            with col1:
                st.markdown(f"{label} — {' '.join(info_parts)}")
            with col2:
                toggled = st.toggle(
                    "Editable",
                    value=is_enabled,
                    key=f"sf_toggle_{api_name}",
                    label_visibility="collapsed",
                )
                if toggled and api_name in updated_disabled:
                    updated_disabled.remove(api_name)
                elif not toggled and api_name not in updated_disabled:
                    updated_disabled.append(api_name)
        st.markdown("---")

    # Summary
    if updated_disabled:
        st.warning(f"{len(updated_disabled)} field(s) disabled: {', '.join(updated_disabled)}")
    else:
        st.success("All fields are enabled for editing.")

    if st.button("Save Salesforce Config", type="primary", key="sf_save"):
        save_config("salesforce", {"disabled_fields": updated_disabled})
        st.toast("Salesforce field config saved!")


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

# Display names → JSON keys
_TOOL_KEY_MAP = {
    "Country Reports": "country-reports",
    "Filing Assembler": "cover-letters",
    "Brief Builder": "brief-builder",
    "Declaration Drafter": "declaration-drafter",
    "Timeline Builder": "timeline-builder",
    "Legal Research": "legal-research",
    "Forms Assistant": "forms-assistant",
    "Case Checklist": "case-checklist",
    "Templates": "evidence-indexer",
    "Document Translator": "document-translator",
    "Client Info": "client-info",
    "Staff Dashboard": "staff-dashboard",
    "Admin Panel": "admin-panel",
}


def _editor_feature_registry():
    registry = load_config("feature-registry") or {}

    st.subheader("Feature Registry")
    st.caption(
        "Track the status of every feature across all tools. "
        '**Final** = locked (do not modify). **Update** = open for changes. '
        "New features should be registered here when built."
    )

    tool_names = list(_TOOL_KEY_MAP.keys())
    selected_reg_tool = st.selectbox("Select tool", tool_names, key="fr_tool_select")
    tool_key = _TOOL_KEY_MAP[selected_reg_tool]

    features: dict = registry.get(tool_key, {})

    st.divider()

    # Summary counts
    final_count = sum(1 for v in features.values() if v == "Final")
    update_count = sum(1 for v in features.values() if v == "Update")
    st.caption(f"{len(features)} features — {final_count} Final, {update_count} Update")

    # Feature list with status dropdowns
    updated_features = {}
    features_to_delete = []

    for idx, (fname, fstatus) in enumerate(features.items()):
        c1, c2, c3 = st.columns([5, 2, 1])
        with c1:
            st.markdown(f"**{fname}**")
        with c2:
            status_options = ["Final", "Update"]
            cur_idx = status_options.index(fstatus) if fstatus in status_options else 0
            new_status = st.selectbox(
                "Status",
                options=status_options,
                index=cur_idx,
                key=f"fr_status_{tool_key}_{idx}",
                label_visibility="collapsed",
            )
        with c3:
            if st.button("X", key=f"fr_del_{tool_key}_{idx}"):
                features_to_delete.append(fname)

        if fname not in features_to_delete:
            updated_features[fname] = new_status

    # Add new feature
    st.markdown("---")
    c1, c2, c3 = st.columns([5, 2, 1])
    with c1:
        new_fname = st.text_input(
            "New feature name",
            key=f"fr_new_name_{tool_key}",
            placeholder="e.g. PDF preview",
        )
    with c2:
        new_fstatus = st.selectbox(
            "Status",
            options=["Update", "Final"],
            key=f"fr_new_status_{tool_key}",
            label_visibility="collapsed",
        )
    with c3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("+", key=f"fr_add_{tool_key}") and new_fname.strip():
            if new_fname.strip() not in updated_features:
                updated_features[new_fname.strip()] = new_fstatus

    registry[tool_key] = updated_features

    if st.button("Save Feature Registry", type="primary", key="fr_save"):
        save_config("feature-registry", registry)
        st.toast("Feature registry saved!")


# ═══════════════════════════════════════════════════════════════════════════════
# Components (shared UI components like Draft Box)
# ═══════════════════════════════════════════════════════════════════════════════


def _editor_components():
    """Edit shared component configuration — tabbed interface."""
    st.subheader("Components")
    st.caption("Configure shared UI components that appear across multiple tools.")

    comp_tab_db, comp_tab_sp, comp_tab_recip, comp_tab_docs, comp_tab_cd, comp_tab_eoir = st.tabs([
        "Draft Box", "System Prompts", "Recipients", "Document Manager", "Case Details",
        "EOIR Cover Template",
    ])

    with comp_tab_db:
        _editor_comp_draft_box()

    with comp_tab_sp:
        _editor_comp_system_prompts()

    with comp_tab_recip:
        _editor_comp_recipients()

    with comp_tab_docs:
        _editor_comp_document_manager()

    with comp_tab_cd:
        _editor_comp_case_details()

    with comp_tab_eoir:
        _editor_comp_eoir_template()


def _editor_comp_eoir_template():
    """Configure the EOIR cover page template used by the Filing Assembler."""
    _DEFAULT_EOIR_TPL = """\
{attorney_name}
{bar_number}
{firm_name}
{firm_address}
{contact_line}
{email_line}

UNITED STATES DEPARTMENT OF JUSTICE
EXECUTIVE OFFICE FOR IMMIGRATION REVIEW
IMMIGRATION COURT
{court_location}
{court_address}

IN THE MATTERS OF:

{party_block}

RESPONDENT'S SUBMISSION
{submission_line_1}
{submission_sub_line}

{submission_type}

{date}

The following documents are respectfully submitted to the Immigration Court
on behalf of the above-named respondent:

{document_list}

Respectfully submitted,

____________________________
{attorney_name}
{firm_name}
Counsel for Respondent


CERTIFICATE OF SERVICE

I hereby certify that on {date}, a copy of the foregoing submission and all
enclosed documents was served upon the Office of the Chief Counsel,
Department of Homeland Security, by {service_method}, at the following address:

{dhs_address}

____________________________
{served_by_name}
{served_by_bar}
"""

    st.markdown("### EOIR Cover Page Template")
    st.caption(
        "Customize the EOIR submission cover page layout using `{variable}` placeholders. "
        "The Filing Assembler replaces placeholders with live case data."
    )

    config = load_config("components") or {}
    saved_tpl = config.get("eoir_cover_template", "") or ""
    current_tpl = saved_tpl if saved_tpl else _DEFAULT_EOIR_TPL

    _reset_col, _ = st.columns([1, 3])
    with _reset_col:
        if st.button("Reset to Default Template", key="_eoir_tpl_reset"):
            config.pop("eoir_cover_template", None)
            save_config("components", config)
            st.toast("Template reset to default. Restart Filing Assembler to apply.")
            st.rerun()

    if "inp_admin_eoir_tpl" not in st.session_state:
        st.session_state["inp_admin_eoir_tpl"] = current_tpl
    _edited_tpl = st.text_area(
        "Template",
        key="inp_admin_eoir_tpl",
        height=600,
        label_visibility="collapsed",
    )

    with st.expander("Available Variables"):
        st.markdown(
            "| Placeholder | Description |\n"
            "|---|---|\n"
            "| `{attorney_name}` | Attorney full name |\n"
            "| `{bar_number}` | Bar number (formatted as 'Bar No. X') |\n"
            "| `{firm_name}` | Firm name |\n"
            "| `{firm_address}` | Firm street address (multi-line) |\n"
            "| `{firm_phone}` | Firm phone number |\n"
            "| `{firm_fax}` | Firm fax number |\n"
            "| `{firm_email}` | Firm email address |\n"
            "| `{contact_line}` | Auto: 'Tel: X \\| Fax: Y' (omits blanks) |\n"
            "| `{email_line}` | Auto: 'Email: X' or blank |\n"
            "| `{court_location}` | Court city from Verify Case Details |\n"
            "| `{court_address}` | Court address from case data |\n"
            "| `{applicant_name}` | Primary applicant name |\n"
            "| `{a_number}` | A-Number |\n"
            "| `{case_type}` | Legal case type |\n"
            "| `{party_block}` | Auto: formatted applicant + beneficiaries block |\n"
            "| `{submission_type}` | Submission description text |\n"
            "| `{submission_line_1}` | Submission Line 1 (SF picklist: EOIR_Submission_Line_1__c) |\n"
            "| `{submission_sub_line}` | Custom sub-line / motion title (local field) |\n"
            "| `{date}` | Today's date (MM/DD/YYYY) |\n"
            "| `{document_list}` | Auto: numbered list of enclosed documents |\n"
            "| `{dhs_address}` | DHS office address for certificate of service |\n"
            "| `{service_method}` | Service method (mail, hand delivery, etc.) |\n"
            "| `{served_by_name}` | Name of person serving documents |\n"
            "| `{served_by_bar}` | Bar number of person serving documents |\n"
        )
        st.info(
            "The EOIR preview in Filing Assembler detects EOIR content by looking for "
            "'EXECUTIVE OFFICE FOR IMMIGRATION REVIEW' in the output. Make sure your "
            "template includes this text."
        )

    if st.button("Save Template", type="primary", key="_eoir_tpl_save"):
        # Save only if different from default; clear if matches default
        if _edited_tpl.strip() == _DEFAULT_EOIR_TPL.strip():
            config.pop("eoir_cover_template", None)
        else:
            config["eoir_cover_template"] = _edited_tpl
        save_config("components", config)
        st.toast("EOIR cover template saved! Restart Filing Assembler to apply.")


_CASE_DETAIL_FIELD_OPTIONS = [
    ("Editable", [
        ("Location_City__c", "City", "picklist"),
        ("Type_of_next_date__c", "Next Date Type", "picklist"),
        ("Next_Government_Date__c", "Next Govt Date", "date"),
        ("Immigration_Judge__c", "Immigration Judge", "picklist"),
        ("EOIR_Submission_Type__c", "EOIR Submission Type", "picklist"),
        ("EOIR_Submission_Line_1__c", "Submission Line 1", "picklist"),
        ("Paper_or_eRop__c", "Filing Method", "picklist"),
    ]),
    ("Read-Only", [
        ("Primary_Applicant__r_Name", "Primary Applicant", "readonly"),
        ("Primary_Attorney__r_Name", "Primary Attorney", "readonly"),
        ("A_number_dashed__c", "A-Number (Dashed)", "readonly"),
    ]),
]

_CASE_DETAIL_DEFAULTS = [
    "Location_City__c", "Type_of_next_date__c", "Next_Government_Date__c",
    "Immigration_Judge__c",
    "EOIR_Submission_Type__c", "EOIR_Submission_Line_1__c", "Paper_or_eRop__c",
    "Primary_Applicant__r_Name", "Primary_Attorney__r_Name", "A_number_dashed__c",
]


def _editor_comp_case_details():
    """Configure which Legal_Case__c fields appear in the EOIR Verify Case Details section."""
    st.markdown("### Case Details Fields")
    st.caption(
        "Choose which Legal Case fields appear in the 'Verify Case Details' section "
        "of the EOIR Submission tab. Read-only fields are always shown as locked."
    )

    config = load_config("components") or {}
    current_fields: list[str] = config.get("case_detail_fields", _CASE_DETAIL_DEFAULTS)

    updated_fields: list[str] = []
    for group_name, fields in _CASE_DETAIL_FIELD_OPTIONS:
        st.markdown(f"**{group_name}**")
        for api_name, label, ftype in fields:
            is_on = api_name in current_fields
            icon = "🔒" if ftype == "readonly" else "✏️"
            toggled = st.toggle(
                f"{icon} {label}  `{api_name}`",
                value=is_on,
                key=f"_cd_fld_{api_name}",
            )
            if toggled:
                updated_fields.append(api_name)
        st.markdown("")

    if updated_fields != current_fields:
        if st.button("Save Case Detail Settings", type="primary", key="_cd_fields_save"):
            config["case_detail_fields"] = updated_fields
            save_config("components", config)
            st.toast("Case detail settings saved! Restart Filing Assembler to see changes.")
            st.rerun()
    else:
        st.caption("No changes to save.")


def _editor_comp_draft_box():
    """Draft Box AI prompt configuration (global + per-tool overrides)."""
    config = load_config("components") or {}
    draft_box = config.get("draft-box", {})

    st.markdown("### Draft Box")
    st.markdown(
        "AI-powered document drafting assistant using Claude. "
        "Appears on Cover Pages, Brief Builder, Declaration Drafter, and Timeline Builder."
    )

    st.markdown("---")

    # Global prompt
    st.markdown("#### Global System Prompt")
    st.caption("Applied to all Draft Box requests across all tools.")
    _DEFAULT_GLOBAL = (
        "You are a legal drafting assistant for O'Brien Immigration Law. "
        "Draft professional, well-structured legal documents. Use formal legal "
        "language appropriate for USCIS filings and immigration court proceedings. "
        "Be thorough but concise. Do not include placeholder text — use the "
        "provided case details to produce a complete, ready-to-review draft."
    )
    global_prompt = st.text_area(
        "Global prompt",
        value=draft_box.get("global_prompt", _DEFAULT_GLOBAL),
        height=150,
        key="_comp_global_prompt",
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("#### Per-Tool Prompt Overrides")
    st.caption("These are appended to the global prompt for each specific tool.")

    _TOOL_DEFAULTS = {
        "cover-letters": (
            "Draft a professional cover letter addressed to USCIS or the "
            "immigration court. Include attorney information, client identification, "
            "case type, enclosed documents, and a formal closing."
        ),
        "brief-builder": (
            "Draft a legal brief section for immigration proceedings. Use proper "
            "legal citation format, reference relevant INA sections and case law, "
            "and present arguments persuasively with clear headings."
        ),
        "declaration-drafter": (
            "Draft a declaration in the first person based on the provided answers. "
            "Use clear, specific language. Organize chronologically. Include standard "
            "declaration preamble and signature block."
        ),
        "timeline-builder": (
            "Draft a narrative summary connecting the timeline events. Highlight key "
            "dates, patterns, and cumulative impact. Use transitional language that "
            "tells the client's story cohesively."
        ),
    }

    tool_prompts = draft_box.get("tool_prompts", {})
    _TOOL_LABELS = {
        "cover-letters": "Filing Assembler",
        "brief-builder": "Brief Builder",
        "declaration-drafter": "Declaration Drafter",
        "timeline-builder": "Timeline Builder",
    }

    updated_tool_prompts = {}
    for tool_key, label in _TOOL_LABELS.items():
        st.markdown(f"**{label}**")
        updated_tool_prompts[tool_key] = st.text_area(
            f"{label} prompt",
            value=tool_prompts.get(tool_key, _TOOL_DEFAULTS.get(tool_key, "")),
            height=100,
            key=f"_comp_tool_prompt_{tool_key}",
            label_visibility="collapsed",
        )

    if st.button("Save Component Settings", type="primary", key="_comp_save"):
        config["draft-box"] = {
            "description": "AI-powered document drafting assistant using Claude",
            "global_prompt": global_prompt,
            "tool_prompts": updated_tool_prompts,
        }
        save_config("components", config)
        st.toast("Component settings saved!")


def _editor_comp_system_prompts():
    """Placeholder for future system prompt management."""
    st.info("System prompt management coming soon.")


def _editor_comp_recipients():
    """Admin recipient address book — add / edit / delete addresses."""
    st.markdown("### Recipient Address Book")
    st.caption(
        "Manage the shared address book used by the Filing Assembler's recipient picker "
        "and other tools."
    )
    if render_recipient_manager is not None:
        render_recipient_manager()
    else:
        st.error("Could not load `shared/recipient_manager.py`.")


def _editor_comp_document_manager():
    """Reference for standard enclosed document templates per case type."""
    st.markdown("### Document Manager")
    st.caption(
        "View the standard enclosed document lists configured for each case type. "
        "To edit case-type-specific document lists, go to "
        "**Tool Configuration → Filing Assembler**."
    )

    # Load templates from cover-letters config
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "cover-letters"))
        from app.templates import get_govt_cover_letter_templates, TEMPLATES
    except ImportError:
        st.error("Could not load cover-letter templates.")
        return

    templates = get_govt_cover_letter_templates()
    if not templates:
        templates = TEMPLATES

    for case_type, tpl in templates.items():
        docs = tpl.get("standard_enclosed_docs", [])
        if not docs:
            continue
        with st.expander(f"{case_type} ({len(docs)} documents)", expanded=False):
            for i, doc in enumerate(docs, 1):
                st.markdown(f"{i}. {doc}")


# ═══════════════════════════════════════════════════════════════════════════════
# Client Banner Fields
# ═══════════════════════════════════════════════════════════════════════════════

# All available fields for the client banner, grouped logically.
# Name and Customer_ID__c are always shown (not toggleable).
_BANNER_FIELD_OPTIONS = [
    ("Identity", [
        ("A_Number__c", "A Number"),
        ("Birthdate", "Date of Birth"),
        ("Gender__c", "Gender"),
        ("Pronoun__c", "Pronouns"),
        ("Marital_status__c", "Marital Status"),
    ]),
    ("Contact", [
        ("Email", "Email"),
        ("Phone", "Phone"),
        ("MobilePhone", "Mobile Phone"),
    ]),
    ("Immigration", [
        ("Country__c", "Country of Origin"),
        ("City_of_Birth__c", "City of Birth"),
        ("Best_Language__c", "Language"),
        ("Immigration_Status__c", "Immigration Status"),
        ("Immigration_Court__c", "Immigration Court"),
        ("Legal_Case_Type__c", "Case Type"),
        ("Client_Status__c", "Client Status"),
    ]),
    ("Case", [
        ("CaseNumber__c", "Case Number"),
        ("Nexus__c", "Nexus"),
        ("PSG__c", "Particular Social Group"),
    ]),
    ("Dates", [
        ("Date_of_First_Entry_to_US__c", "First US Entry"),
        ("Date_of_Most_Recent_US_Entry__c", "Last US Entry"),
        ("Status_of_Last_Arrival__c", "Arrival Status"),
        ("Place_of_Last_Arrival__c", "Arrival Place"),
    ]),
    ("Family", [
        ("Spouse_Name__c", "Spouse Name"),
    ]),
]

# Default fields shown (matches the original hardcoded banner)
_BANNER_DEFAULTS = [
    "A_Number__c", "Country__c", "Best_Language__c", "Immigration_Status__c",
]


def _editor_client_banner():
    """Configure which fields appear in the client info banner across all tools."""
    st.subheader("Client Banner Fields")
    st.caption(
        "Choose which client fields appear in the blue info bar at the top of every tool page. "
        "Name and Client # are always shown."
    )

    _global = load_config("global-settings") or {}
    current_fields: list[str] = _global.get("banner_fields", _BANNER_DEFAULTS)

    # ── Pull bar toggle ──
    st.markdown("**Pull Bar**")
    _cur_pull_bar = _global.get("show_pull_bar", False)
    _new_pull_bar = st.toggle(
        "Show pull bar on tool pages",
        value=_cur_pull_bar,
        key="_banner_pull_bar_toggle",
        help="When enabled, each tool page shows a client input with Pull, Files, and Email buttons. "
             "When disabled, only the read-only info ribbon is shown.",
    )
    if _new_pull_bar != _cur_pull_bar:
        _global["show_pull_bar"] = _new_pull_bar
        save_config("global-settings", _global)
        st.toast("Pull bar setting saved!")
        st.rerun()

    st.markdown("")

    # ── Font size ──
    st.markdown("**Font Size**")
    current_size = _global.get("banner_font_size", 13)
    new_size = st.slider(
        "Banner font size (px)",
        min_value=10,
        max_value=20,
        value=current_size,
        step=1,
        key="_banner_font_size",
        help="Controls the font size of the client info banner across all tools.",
    )
    _preview_size = f"{new_size}px"
    _preview_name_size = f"{new_size + 1}px"
    st.markdown(
        f'<div style="display:flex;align-items:center;flex-wrap:wrap;gap:6px 16px;'
        f'padding:8px 16px;background:#f0f4ff;border-radius:8px;font-size:{_preview_size};color:#3a4a6b;">'
        f'<span style="font-weight:700;color:#1a2744;font-size:{_preview_name_size};">Jane Doe</span>'
        f'<span style="color:#c0c8d8;">|</span>'
        f'<span style="color:#5a6a85;"><strong style="color:#1a2744;font-weight:600;">#</strong>12345</span>'
        f'<span style="color:#5a6a85;"><strong style="color:#1a2744;font-weight:600;">A#</strong> 123-456-789</span>'
        f'<span style="color:#5a6a85;">Guatemala</span>'
        f'<span style="color:#5a6a85;">Spanish</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    st.info("Client name and Customer ID are always displayed.")

    updated_fields: list[str] = []

    for group_name, fields in _BANNER_FIELD_OPTIONS:
        st.markdown(f"**{group_name}**")
        for api_name, label in fields:
            is_on = api_name in current_fields
            toggled = st.toggle(
                f"{label}  `{api_name}`",
                value=is_on,
                key=f"_banner_fld_{api_name}",
            )
            if toggled:
                updated_fields.append(api_name)
        st.markdown("")

    _fields_changed = updated_fields != current_fields
    _size_changed = new_size != current_size

    if _fields_changed or _size_changed:
        if st.button("Save Banner Settings", type="primary", key="_banner_fields_save"):
            _global["banner_fields"] = updated_fields
            _global["banner_font_size"] = new_size
            save_config("global-settings", _global)
            st.toast("Banner settings saved! Restart tools to see changes.")
            st.rerun()
    else:
        st.caption("No changes to save.")


# ═══════════════════════════════════════════════════════════════════════════════
# Firm Info
# ═══════════════════════════════════════════════════════════════════════════════


_DEFAULT_FIRM_HEADER_TEMPLATE = """\
{attorney_name}
{bar_number}
{firm_name}
{firm_address}
{contact_line}
{email_line}"""

_DEFAULT_COURT_CAPTION_TEMPLATE = """\
UNITED STATES DEPARTMENT OF JUSTICE
EXECUTIVE OFFICE FOR IMMIGRATION REVIEW
IMMIGRATION COURT
{court_location}
{court_address}"""

_DOC_TEMPLATE_VARIABLES = {
    "Firm Header": [
        ("{attorney_name}", "Attorney full name"),
        ("{bar_number}", "Bar number (formatted as 'Bar No. X')"),
        ("{firm_name}", "Firm name from global settings"),
        ("{firm_address}", "Firm street address (multi-line)"),
        ("{firm_phone}", "Firm phone number"),
        ("{firm_fax}", "Firm fax number"),
        ("{firm_email}", "Firm email address"),
        ("{contact_line}", "Auto: 'Tel: X | Fax: Y' (omits blanks)"),
        ("{email_line}", "Auto: 'Email: X' or blank"),
    ],
    "Court Caption": [
        ("{court_location}", "Court city from Verify Case Details"),
        ("{court_address}", "Court address from case data"),
    ],
}


def _editor_document_templates():
    """Edit global document block templates used across filings."""
    st.subheader("Document Templates")
    st.caption(
        "Define the layout for reusable document blocks. These templates use "
        "`{variable}` placeholders and are applied globally to all new filings."
    )

    config = load_config("document-templates") or {}

    # ── Firm Header block ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Firm Header Block")
    st.caption("Attorney/firm header that appears at the top of EOIR cover pages and filings.")

    _saved_fh = config.get("firm_header_template", "")
    _current_fh = _saved_fh if _saved_fh else _DEFAULT_FIRM_HEADER_TEMPLATE

    if "inp_admin_fh_tpl" not in st.session_state:
        st.session_state["inp_admin_fh_tpl"] = _current_fh

    # Layout settings
    _fh_layout = config.get("firm_header_layout", {})
    _fh_lc, _fh_rc = st.columns(2)
    with _fh_lc:
        _fh_align = st.selectbox(
            "Text Alignment",
            ["left", "center", "right"],
            index=["left", "center", "right"].index(_fh_layout.get("align", "left")),
            key="_fh_align",
        )
    with _fh_rc:
        _fh_margin = st.number_input(
            "Top Margin (px)",
            min_value=0, max_value=100,
            value=_fh_layout.get("margin_top", 0),
            key="_fh_margin",
        )

    _edited_fh = st.text_area(
        "Firm Header Template",
        key="inp_admin_fh_tpl",
        height=200,
        label_visibility="collapsed",
    )

    with st.expander("Available Variables — Firm Header"):
        _rows = "\n".join(
            f"| `{v}` | {d} |" for v, d in _DOC_TEMPLATE_VARIABLES["Firm Header"]
        )
        st.markdown(f"| Variable | Description |\n|---|---|\n{_rows}")

    _fh_c1, _fh_c2, _ = st.columns([1, 1, 3])
    with _fh_c1:
        if st.button("Save Firm Header", type="primary", key="_fh_save"):
            if _edited_fh.strip() == _DEFAULT_FIRM_HEADER_TEMPLATE.strip():
                config.pop("firm_header_template", None)
            else:
                config["firm_header_template"] = _edited_fh
            config["firm_header_layout"] = {
                "align": _fh_align,
                "margin_top": _fh_margin,
            }
            save_config("document-templates", config)
            st.toast("Firm header template saved! Restart Filing Assembler to apply.")
    with _fh_c2:
        if st.button("Reset to Default", key="_fh_reset"):
            config.pop("firm_header_template", None)
            config.pop("firm_header_layout", None)
            save_config("document-templates", config)
            if "inp_admin_fh_tpl" in st.session_state:
                del st.session_state["inp_admin_fh_tpl"]
            st.toast("Firm header reset to default.")
            st.rerun()

    # ── Court Caption block ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Court Caption Block")
    st.caption("Court header that appears on EOIR submission cover pages.")

    _saved_cc = config.get("court_caption_template", "")
    _current_cc = _saved_cc if _saved_cc else _DEFAULT_COURT_CAPTION_TEMPLATE

    if "inp_admin_cc_tpl" not in st.session_state:
        st.session_state["inp_admin_cc_tpl"] = _current_cc

    # Layout settings
    _cc_layout = config.get("court_caption_layout", {})
    _cc_lc, _cc_rc = st.columns(2)
    with _cc_lc:
        _cc_align = st.selectbox(
            "Text Alignment",
            ["left", "center", "right"],
            index=["left", "center", "right"].index(_cc_layout.get("align", "center")),
            key="_cc_align",
        )
    with _cc_rc:
        _cc_margin = st.number_input(
            "Top Margin (px)",
            min_value=0, max_value=100,
            value=_cc_layout.get("margin_top", 0),
            key="_cc_margin",
        )

    _edited_cc = st.text_area(
        "Court Caption Template",
        key="inp_admin_cc_tpl",
        height=180,
        label_visibility="collapsed",
    )

    with st.expander("Available Variables — Court Caption"):
        _rows = "\n".join(
            f"| `{v}` | {d} |" for v, d in _DOC_TEMPLATE_VARIABLES["Court Caption"]
        )
        st.markdown(f"| Variable | Description |\n|---|---|\n{_rows}")

    _cc_c1, _cc_c2, _ = st.columns([1, 1, 3])
    with _cc_c1:
        if st.button("Save Court Caption", type="primary", key="_cc_save"):
            if _edited_cc.strip() == _DEFAULT_COURT_CAPTION_TEMPLATE.strip():
                config.pop("court_caption_template", None)
            else:
                config["court_caption_template"] = _edited_cc
            config["court_caption_layout"] = {
                "align": _cc_align,
                "margin_top": _cc_margin,
            }
            save_config("document-templates", config)
            st.toast("Court caption template saved! Restart Filing Assembler to apply.")
    with _cc_c2:
        if st.button("Reset to Default", key="_cc_reset"):
            config.pop("court_caption_template", None)
            config.pop("court_caption_layout", None)
            save_config("document-templates", config)
            if "inp_admin_cc_tpl" in st.session_state:
                del st.session_state["inp_admin_cc_tpl"]
            st.toast("Court caption reset to default.")
            st.rerun()

    # ── Layout persistence note ──────────────────────────────────────────
    st.markdown("---")
    st.info(
        "Layout settings (alignment, margins) are saved to "
        "`data/config/document-templates.json` and persist across sessions. "
        "These settings affect export formatting for DOCX and PDF output."
    )


def _editor_firm_info():
    """Manage firm-level settings used across tools (cover pages, briefs, etc.)."""
    import time

    st.subheader("Firm Info")
    st.caption(
        "Firm name and address are used in cover pages, briefs, and other documents. "
        "Changes are shared across all tools."
    )

    _global = load_config("global-settings") or {}
    cur_name = _global.get("firm_name", "O'Brien Immigration Law")

    new_name = st.text_input("Firm Name", value=cur_name, key="_firm_name")
    if new_name != cur_name:
        if st.button("Save Firm Name", type="primary", key="_firm_name_save"):
            _global["firm_name"] = new_name
            save_config("global-settings", _global)
            st.toast("Firm name saved!")
            st.rerun()

    # ── Locations manager ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**Office Locations**")
    st.caption("Manage office locations. The first location's address is used as the default firm address.")

    locations = load_config("firm-locations") or []

    # Seed from existing firm_address on first load
    if not locations and _global.get("firm_address", "").strip():
        locations = [{
            "id": f"loc_{int(time.time() * 1000)}",
            "name": "Main Office",
            "address": _global["firm_address"].strip(),
        }]
        save_config("firm-locations", locations)
        st.rerun()

    # Add new location
    with st.expander("Add Location", expanded=not locations):
        loc_name = st.text_input("Location Name", key="_loc_new_name", placeholder="e.g. Stockton")
        loc_addr = st.text_area("Address", key="_loc_new_addr", height=80)
        if st.button("Add Location", type="primary", key="_loc_add"):
            if not loc_name.strip():
                st.warning("Location name is required.")
            else:
                locations.append({
                    "id": f"loc_{int(time.time() * 1000)}",
                    "name": loc_name.strip(),
                    "address": loc_addr.strip(),
                })
                save_config("firm-locations", locations)
                # Keep firm_address in sync with first location
                _global["firm_address"] = locations[0]["address"]
                save_config("global-settings", _global)
                st.toast(f"Added location: {loc_name.strip()}")
                st.rerun()

    # List existing locations
    loc_changed = False
    locs_to_delete = []

    for li, loc in enumerate(locations):
        with st.expander(f"{loc.get('name', 'Unnamed')}"):
            ln = st.text_input("Name", value=loc.get("name", ""), key=f"_loc_n_{li}")
            la = st.text_area("Address", value=loc.get("address", ""), key=f"_loc_a_{li}", height=80)
            if ln != loc.get("name", "") or la != loc.get("address", ""):
                loc["name"] = ln
                loc["address"] = la
                loc_changed = True
            if st.button("Delete Location", key=f"_loc_del_{li}"):
                locs_to_delete.append(li)

    if locs_to_delete:
        for li in sorted(locs_to_delete, reverse=True):
            removed = locations.pop(li)
            st.toast(f"Removed location: {removed.get('name', '')}")
        save_config("firm-locations", locations)
        _global["firm_address"] = locations[0]["address"] if locations else ""
        save_config("global-settings", _global)
        st.rerun()

    if loc_changed:
        if st.button("Save Location Changes", type="primary", key="_loc_save"):
            save_config("firm-locations", locations)
            _global["firm_address"] = locations[0]["address"] if locations else ""
            save_config("global-settings", _global)
            st.toast("Locations saved!")
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# Staff Directory
# ═══════════════════════════════════════════════════════════════════════════════


def _editor_staff_directory():
    """Manage office staff members — names, contact info for document generation."""
    import time

    st.subheader("Staff Directory")
    st.caption(
        "Add staff members so their info can be pulled into cover pages, briefs, "
        "and other documents. Changes are saved immediately."
    )

    staff = load_config("staff-directory") or []
    locations = load_config("firm-locations") or []
    loc_names = ["(None)"] + [loc.get("name", "Unnamed") for loc in locations]
    loc_ids = [""] + [loc.get("id", "") for loc in locations]

    # --- Sync from Salesforce ---
    if st.button("Sync Staff from Salesforce", key="_staff_sync"):
        with st.spinner("Pulling active users from Salesforce..."):
            try:
                from shared.salesforce_client import get_sf_users
                sf_users = get_sf_users()
            except Exception as e:
                st.error(f"Salesforce sync failed: {e}")
                sf_users = []

            if sf_users:
                added, updated = 0, 0
                for sfu in sf_users:
                    sf_id = sfu.get("Id", "")
                    sf_email = (sfu.get("Email") or "").strip().lower()
                    # Match by sf_user_id first, then by email
                    match = None
                    for m in staff:
                        if m.get("sf_user_id") and m["sf_user_id"] == sf_id:
                            match = m
                            break
                    if not match and sf_email:
                        for m in staff:
                            if (m.get("email") or "").strip().lower() == sf_email:
                                match = m
                                break
                    if match:
                        match["first_name"] = sfu.get("FirstName") or match.get("first_name", "")
                        match["last_name"] = sfu.get("LastName") or match.get("last_name", "")
                        match["email"] = sfu.get("Email") or match.get("email", "")
                        match["phone"] = sfu.get("Phone") or match.get("phone", "")
                        match["bar_number"] = sfu.get("Bar_Number__c") or match.get("bar_number", "")
                        match["sf_user_id"] = sf_id
                        updated += 1
                    else:
                        staff.append({
                            "id": f"staff_{int(time.time() * 1000)}",
                            "first_name": sfu.get("FirstName") or "",
                            "last_name": sfu.get("LastName") or "",
                            "email": sfu.get("Email") or "",
                            "phone": sfu.get("Phone") or "",
                            "bar_number": sfu.get("Bar_Number__c") or "",
                            "address": "",
                            "location_id": "",
                            "visible": True,
                            "sf_user_id": sf_id,
                        })
                        added += 1
                        time.sleep(0.001)  # ensure unique timestamp ids
                save_config("staff-directory", staff)
                st.success(f"Sync complete — added {added}, updated {updated} staff members.")
                st.rerun()
            elif not sf_users:
                st.info("No active Salesforce users found.")

    # --- Add new staff member ---
    with st.expander("Add New Staff Member", expanded=not staff):
        c1, c2 = st.columns(2)
        with c1:
            new_first = st.text_input("First Name", key="_staff_new_first")
            new_last = st.text_input("Last Name", key="_staff_new_last")
            new_email = st.text_input("Email", key="_staff_new_email")
        with c2:
            new_phone = st.text_input("Phone", key="_staff_new_phone")
            new_bar = st.text_input("Bar Number", key="_staff_new_bar")
            new_address = st.text_area("Address", key="_staff_new_address", height=100)
        new_loc_idx = st.selectbox("Location", range(len(loc_names)), format_func=lambda i: loc_names[i], key="_staff_new_loc")
        new_visible = st.toggle("Visible in app picklists", value=True, key="_staff_new_visible")

        if st.button("Add Staff Member", type="primary", key="_staff_add"):
            if not new_first.strip() or not new_last.strip():
                st.warning("First and last name are required.")
            else:
                staff.append({
                    "id": f"staff_{int(time.time() * 1000)}",
                    "first_name": new_first.strip(),
                    "last_name": new_last.strip(),
                    "email": new_email.strip(),
                    "phone": new_phone.strip(),
                    "bar_number": new_bar.strip(),
                    "address": new_address.strip(),
                    "location_id": loc_ids[new_loc_idx],
                    "visible": new_visible,
                    "sf_user_id": "",
                })
                save_config("staff-directory", staff)
                st.toast(f"Added {new_first.strip()} {new_last.strip()}")
                st.rerun()

    # --- List existing staff ---
    if not staff:
        st.info("No staff members yet. Add one above or sync from Salesforce.")
        return

    st.markdown(f"**{len(staff)} staff member{'s' if len(staff) != 1 else ''}**")

    staff_to_delete = []
    staff_changed = False

    for idx, member in enumerate(staff):
        display_name = f"{member.get('first_name', '')} {member.get('last_name', '')}".strip() or "Unnamed"
        badge = " (SF)" if member.get("sf_user_id") else ""
        vis_label = "" if member.get("visible", True) else " [Hidden]"
        with st.expander(f"{display_name}{badge}{vis_label} — {member.get('email', '')}"):
            c1, c2 = st.columns(2)
            with c1:
                first = st.text_input("First Name", value=member.get("first_name", ""), key=f"_staff_f_{idx}")
                last = st.text_input("Last Name", value=member.get("last_name", ""), key=f"_staff_l_{idx}")
                email = st.text_input("Email", value=member.get("email", ""), key=f"_staff_e_{idx}")
            with c2:
                phone = st.text_input("Phone", value=member.get("phone", ""), key=f"_staff_p_{idx}")
                bar_num = st.text_input("Bar Number", value=member.get("bar_number", ""), key=f"_staff_b_{idx}")
                address = st.text_area("Address", value=member.get("address", ""), key=f"_staff_a_{idx}", height=100)

            # Location picklist
            cur_loc_id = member.get("location_id", "")
            try:
                sel_loc_idx = loc_ids.index(cur_loc_id)
            except ValueError:
                sel_loc_idx = 0
            new_loc_idx = st.selectbox(
                "Location", range(len(loc_names)),
                format_func=lambda i: loc_names[i],
                index=sel_loc_idx,
                key=f"_staff_loc_{idx}",
            )

            # Visible toggle
            vis = st.toggle("Visible in app picklists", value=member.get("visible", True), key=f"_staff_vis_{idx}")

            if member.get("sf_user_id"):
                st.caption("Synced from Salesforce")

            if (first != member.get("first_name", "") or last != member.get("last_name", "") or
                    email != member.get("email", "") or phone != member.get("phone", "") or
                    bar_num != member.get("bar_number", "") or
                    address != member.get("address", "") or
                    loc_ids[new_loc_idx] != cur_loc_id or
                    vis != member.get("visible", True)):
                member["first_name"] = first
                member["last_name"] = last
                member["email"] = email
                member["phone"] = phone
                member["bar_number"] = bar_num
                member["address"] = address
                member["location_id"] = loc_ids[new_loc_idx]
                member["visible"] = vis
                staff_changed = True

            if st.button("Delete", key=f"_staff_del_{idx}"):
                staff_to_delete.append(idx)

    if staff_to_delete:
        for idx in sorted(staff_to_delete, reverse=True):
            removed = staff.pop(idx)
            st.toast(f"Removed {removed.get('first_name', '')} {removed.get('last_name', '')}")
        save_config("staff-directory", staff)
        st.rerun()

    if staff_changed:
        if st.button("Save Changes", type="primary", key="_staff_save"):
            save_config("staff-directory", staff)
            st.toast("Staff directory saved!")


# ═══════════════════════════════════════════════════════════════════════════════
# API Usage & Budgets
# ═══════════════════════════════════════════════════════════════════════════════


def _editor_api_usage():
    """Dashboard showing API usage, costs, and budget tracking."""
    from datetime import datetime

    try:
        from shared.usage_tracker import (
            get_daily_breakdown,
            get_entries_since,
            get_monthly_summary,
            get_per_tool_breakdown,
            load_budgets,
            save_budgets,
        )
    except ImportError:
        st.error("Usage tracker module not found.")
        return

    st.subheader("API Usage & Budgets")
    now = datetime.now()
    st.caption(f"Current billing period: {now.strftime('%B %Y')}")

    summary = get_monthly_summary()
    budgets = load_budgets()

    # ── Summary cards ───────────────────────────────────────────────────────
    st.markdown("### This Month")
    m1, m2, m3, m4 = st.columns(4)

    anth = summary["anthropic"]
    with m1:
        st.metric("Anthropic Calls", f"{anth['calls']}")
    with m2:
        total_tokens = anth["input_tokens"] + anth["output_tokens"]
        if total_tokens >= 1_000_000:
            st.metric("Tokens Used", f"{total_tokens / 1_000_000:.2f}M")
        elif total_tokens >= 1_000:
            st.metric("Tokens Used", f"{total_tokens / 1_000:.1f}K")
        else:
            st.metric("Tokens Used", f"{total_tokens}")
    with m3:
        st.metric("Estimated Cost", f"${anth['cost_usd']:.2f}")
    with m4:
        gdocs = summary["google_docs"]
        gtrans = summary["google_translate"]
        google_total = gdocs["calls"] + gtrans["calls"]
        st.metric("Google API Calls", f"{google_total}")

    # ── Budget tracking ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Budget Tracking")

    b1, b2 = st.columns(2)

    with b1:
        st.markdown("**Anthropic (Claude)**")
        anth_budget = budgets.get("anthropic_monthly_usd", 50.0)
        anth_spent = anth["cost_usd"]
        anth_pct = min(anth_spent / anth_budget, 1.0) if anth_budget > 0 else 0
        st.progress(anth_pct)

        if anth_pct >= 0.9:
            st.error(f"${anth_spent:.2f} / ${anth_budget:.2f} — approaching limit!")
        elif anth_pct >= 0.7:
            st.warning(f"${anth_spent:.2f} / ${anth_budget:.2f}")
        else:
            st.caption(f"${anth_spent:.2f} / ${anth_budget:.2f}")

        remaining = max(anth_budget - anth_spent, 0)
        days_left = (datetime(now.year, now.month % 12 + 1, 1) - now).days if now.month < 12 else (datetime(now.year + 1, 1, 1) - now).days
        if days_left > 0 and anth["calls"] > 0:
            days_elapsed = now.day
            daily_avg = anth_spent / days_elapsed if days_elapsed > 0 else 0
            projected = daily_avg * (days_elapsed + days_left)
            st.caption(f"Daily avg: ${daily_avg:.2f} — Projected month-end: ${projected:.2f}")

    with b2:
        st.markdown("**Google (Translate + Docs)**")
        google_budget = budgets.get("google_monthly_usd", 10.0)
        google_spent = summary["google_translate"]["cost_usd"]
        google_pct = min(google_spent / google_budget, 1.0) if google_budget > 0 else 0
        st.progress(google_pct)

        if google_pct >= 0.9:
            st.error(f"${google_spent:.2f} / ${google_budget:.2f} — approaching limit!")
        elif google_pct >= 0.7:
            st.warning(f"${google_spent:.2f} / ${google_budget:.2f}")
        else:
            st.caption(f"${google_spent:.2f} / ${google_budget:.2f}")

        st.caption(f"Google Docs uploads: {gdocs['calls']} (free)")
        if gtrans["calls"] > 0:
            st.caption(f"Translate calls: {gtrans['calls']} ({gtrans['characters']:,} chars)")

    # ── Budget settings ─────────────────────────────────────────────────────
    with st.expander("Edit Monthly Budgets"):
        new_anth = st.number_input(
            "Anthropic monthly budget (USD)",
            value=float(budgets.get("anthropic_monthly_usd", 50.0)),
            min_value=0.0,
            step=5.0,
            key="_budget_anthropic",
        )
        new_google = st.number_input(
            "Google monthly budget (USD)",
            value=float(budgets.get("google_monthly_usd", 10.0)),
            min_value=0.0,
            step=5.0,
            key="_budget_google",
        )
        if st.button("Save Budgets", type="primary", key="_budget_save"):
            save_budgets({
                "anthropic_monthly_usd": new_anth,
                "google_monthly_usd": new_google,
            })
            st.toast("Budgets saved!")
            st.rerun()

    # ── Per-tool breakdown ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Usage by Tool")

    tool_data = get_per_tool_breakdown()
    if tool_data:
        _TOOL_LABELS = {
            "cover-letters": "Filing Assembler",
            "brief-builder": "Brief Builder",
            "declaration-drafter": "Declaration Drafter",
            "timeline-builder": "Timeline Builder",
            "unknown": "Other",
        }
        for row in tool_data:
            tool_label = _TOOL_LABELS.get(row["tool"], row["tool"])
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"**{tool_label}**")
            with c2:
                st.caption(f"{row['calls']} calls")
            with c3:
                st.caption(f"${row['cost_usd']:.3f}")
    else:
        st.info("No API calls recorded this month.")

    # ── Daily trend ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Daily Trend (Last 30 Days)")

    daily = get_daily_breakdown(30)
    if daily:
        import pandas as pd

        df = pd.DataFrame(daily)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

        tab_cost, tab_calls, tab_tokens = st.tabs(["Cost", "Calls", "Tokens"])
        with tab_cost:
            st.bar_chart(df["cost_usd"], color="#0066CC")
        with tab_calls:
            st.bar_chart(df["calls"], color="#34a853")
        with tab_tokens:
            st.bar_chart(df["tokens"], color="#ea4335")
    else:
        st.info("No usage data yet.")

    # ── Recent activity ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Recent Activity")

    recent = get_entries_since(7)[:25]
    if recent:
        for entry in recent:
            ts = entry.get("timestamp", "")[:16].replace("T", " ")
            svc = entry.get("service", "")
            tool = entry.get("tool", "")
            op = entry.get("operation", "")
            cost = entry.get("estimated_cost_usd", 0)
            inp = entry.get("input_tokens", 0)
            out = entry.get("output_tokens", 0)

            if svc == "anthropic":
                st.markdown(
                    f"**{ts}** &nbsp; `{svc}` &nbsp; {tool} &nbsp; "
                    f"{inp:,}+{out:,} tokens &nbsp; **${cost:.4f}**"
                )
            else:
                detail = entry.get("details", op)
                st.markdown(f"**{ts}** &nbsp; `{svc}` &nbsp; {detail}")
    else:
        st.info("No recent API calls.")

    # ── Pricing reference ───────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("Pricing Reference"):
        st.markdown(
            "| Model | Input | Output |\n"
            "|-------|-------|--------|\n"
            "| Claude Sonnet 4.5 | $3.00 / MTok | $15.00 / MTok |\n"
            "| Claude Haiku 3.5 | $0.80 / MTok | $4.00 / MTok |\n"
            "| Google Translate v2 | $20.00 / M chars | — |\n"
            "| Google Docs upload | Free | — |"
        )
        st.caption(
            "Costs are estimated locally based on token counts from API responses. "
            "Actual billing may differ slightly. Check console.anthropic.com for your real balance."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

_DEFAULT_EMAIL_TEMPLATES = [
    {
        "id": "blank",
        "name": "Blank",
        "subject": "",
        "body": "",
    },
    {
        "id": "appointment_reminder",
        "name": "Appointment Reminder",
        "subject": "Appointment Reminder — {first_name} {last_name}",
        "body": (
            "Dear {first_name},\n\n"
            "This is a reminder about your upcoming appointment with our office. "
            "Please bring all relevant documents, including your photo ID and any "
            "correspondence from USCIS or the immigration court.\n\n"
            "If you need to reschedule, please call our office as soon as possible.\n\n"
            "Thank you,\n"
            "O'Brien Immigration Law"
        ),
    },
    {
        "id": "document_request",
        "name": "Document Request",
        "subject": "Documents Needed — {first_name} {last_name} (#{customer_id})",
        "body": (
            "Dear {first_name},\n\n"
            "We are writing to request the following documents for your case:\n\n"
            "1. \n"
            "2. \n"
            "3. \n\n"
            "Please provide these documents at your earliest convenience. You may "
            "email scanned copies to our office or bring the originals to your next "
            "appointment.\n\n"
            "If you have any questions, please do not hesitate to contact us.\n\n"
            "Thank you,\n"
            "O'Brien Immigration Law"
        ),
    },
    {
        "id": "case_status_update",
        "name": "Case Status Update",
        "subject": "Case Update — {first_name} {last_name}",
        "body": (
            "Dear {first_name},\n\n"
            "We are writing to provide an update on your {case_type} case.\n\n"
            "[Update details here]\n\n"
            "Please do not hesitate to contact our office if you have any questions.\n\n"
            "Thank you,\n"
            "O'Brien Immigration Law"
        ),
    },
    {
        "id": "welcome_new_client",
        "name": "Welcome New Client",
        "subject": "Welcome to O'Brien Immigration Law — {first_name} {last_name}",
        "body": (
            "Dear {first_name},\n\n"
            "Welcome to O'Brien Immigration Law. We are pleased to represent you in "
            "your immigration matter.\n\n"
            "Your client number is #{customer_id}. Please reference this number in "
            "all communications with our office.\n\n"
            "We will be in touch soon to schedule your initial consultation and discuss "
            "next steps. In the meantime, please gather any documents related to your "
            "immigration history.\n\n"
            "Thank you for choosing our firm.\n\n"
            "Sincerely,\n"
            "O'Brien Immigration Law"
        ),
    },
]


def _editor_email_templates():
    """Manage reusable email templates with merge field placeholders."""
    st.subheader("Email Templates")
    st.caption(
        "Create and edit email templates. Use {field_name} placeholders that will "
        "be filled with client data when composing. Templates are available in the "
        "Email button on every tool."
    )

    templates = load_config("email-templates")
    if templates is None:
        templates = copy.deepcopy(_DEFAULT_EMAIL_TEMPLATES)

    # Merge field reference
    with st.expander("Available merge fields"):
        st.markdown(
            "| Placeholder | Description |\n"
            "|---|---|\n"
            "| `{first_name}` | Client first name |\n"
            "| `{last_name}` | Client last name |\n"
            "| `{name}` | Full name |\n"
            "| `{customer_id}` | Client number |\n"
            "| `{a_number}` | Alien registration number |\n"
            "| `{email}` | Client email |\n"
            "| `{phone}` | Phone number |\n"
            "| `{country}` | Country of origin |\n"
            "| `{language}` | Preferred language |\n"
            "| `{immigration_status}` | Immigration status |\n"
            "| `{case_type}` | Legal case type |\n"
            "| `{case_number}` | Case number |\n"
            "| `{court}` | Immigration court |\n"
            "| `{dob}` | Date of birth |\n"
            "| `{spouse}` | Spouse name |\n"
        )

    # Add new template
    with st.expander("Add New Template"):
        new_name = st.text_input("Template Name", key="_et_new_name", placeholder="e.g. Hearing Reminder")
        new_subject = st.text_input("Subject", key="_et_new_subject")
        new_body = st.text_area("Body", key="_et_new_body", height=150)
        if st.button("Add Template", type="primary", key="_et_add"):
            if not new_name.strip():
                st.warning("Template name is required.")
            else:
                import time as _time
                templates.append({
                    "id": f"custom_{int(_time.time() * 1000)}",
                    "name": new_name.strip(),
                    "subject": new_subject,
                    "body": new_body,
                })
                save_config("email-templates", templates)
                st.toast(f"Added template: {new_name.strip()}")
                st.rerun()

    # List / edit existing templates
    if not templates:
        st.info("No templates. Add one above.")
        return

    st.markdown(f"**{len(templates)} template{'s' if len(templates) != 1 else ''}**")

    templates_to_delete: list[int] = []

    for idx, tpl in enumerate(templates):
        with st.expander(tpl.get("name", f"Template {idx + 1}")):
            tpl["name"] = st.text_input("Name", value=tpl.get("name", ""), key=f"_et_name_{idx}")
            tpl["subject"] = st.text_input("Subject", value=tpl.get("subject", ""), key=f"_et_subj_{idx}")
            tpl["body"] = st.text_area("Body", value=tpl.get("body", ""), key=f"_et_body_{idx}", height=200)
            if st.button("Delete", key=f"_et_del_{idx}"):
                templates_to_delete.append(idx)

    if templates_to_delete:
        for idx in sorted(templates_to_delete, reverse=True):
            removed = templates.pop(idx)
            st.toast(f"Removed template: {removed.get('name', '')}")
        save_config("email-templates", templates)
        st.rerun()

    if st.button("Save Email Templates", type="primary", key="_et_save"):
        save_config("email-templates", templates)
        st.toast("Email templates saved!")


# ═══════════════════════════════════════════════════════════════════════════════
# Tab 1: Tool Configuration
# ═══════════════════════════════════════════════════════════════════════════════

_TOOL_EDITORS = {
    "Case Checklist": _editor_case_checklist,
    "Filing Assembler": _editor_cover_letters,
    "Declaration Drafter": _editor_declaration_drafter,
    "Legal Research": _editor_legal_research,
    "Forms Assistant": _editor_forms_assistant,
    "Templates": _editor_evidence_indexer,
    "Timeline Builder": _editor_timeline_builder,
    "Document Translator": _editor_document_translator,
}

with tab_tools:
    st.caption("Edit templates, lists, and settings for individual tools.")
    selected_tool = st.selectbox(
        "Select tool to configure",
        list(_TOOL_EDITORS.keys()),
        key="_tab_tools_select",
    )
    st.divider()
    _TOOL_EDITORS[selected_tool]()

# ═══════════════════════════════════════════════════════════════════════════════
# Tab 2: Integrations
# ═══════════════════════════════════════════════════════════════════════════════

with tab_integrations:
    st.caption("Configure external service connections, shared components, and office data.")
    int_sub = st.radio(
        "Section",
        ["Firm Info", "Staff Directory", "Client Banner", "Salesforce Fields", "Components", "Document Templates"],
        horizontal=True,
        key="_tab_int_radio",
        label_visibility="collapsed",
    )
    st.divider()
    if int_sub == "Firm Info":
        _editor_firm_info()
    elif int_sub == "Staff Directory":
        _editor_staff_directory()
    elif int_sub == "Client Banner":
        _editor_client_banner()
    elif int_sub == "Salesforce Fields":
        _editor_salesforce_fields()
    elif int_sub == "Document Templates":
        _editor_document_templates()
    else:
        _editor_components()

# ═══════════════════════════════════════════════════════════════════════════════
# Tab 3: Governance
# ═══════════════════════════════════════════════════════════════════════════════

_SIDEBAR_TOOLS = [
    ("country-reports", "Country Reports"),
    ("cover-letters", "Filing Assembler"),
    ("brief-builder", "Brief Builder"),
    ("declaration-drafter", "Declaration Drafter"),
    ("timeline-builder", "Timeline Builder"),
    ("legal-research", "Legal Research"),
    ("forms-assistant", "Forms Assistant"),
    ("case-checklist", "Case Checklist"),
    ("evidence-indexer", "Templates"),
    ("document-translator", "Document Translator"),
    ("client-info", "Client Info"),
]

with tab_governance:
    st.caption("Feature locking, sidebar visibility, navigation, component toggles, and security.")
    gov_sub = st.radio(
        "Section",
        ["Feature Registry", "Sidebar Visibility", "Navigation", "Component Toggles", "Security"],
        horizontal=True,
        key="_tab_gov_radio",
        label_visibility="collapsed",
    )
    st.divider()

    if gov_sub == "Feature Registry":
        _editor_feature_registry()
    elif gov_sub == "Navigation":
        # ── Navigation Manager ────────────────────────────────────────
        st.subheader("Navigation Manager")
        st.caption(
            "Configure which tools appear on the Staff Dashboard, their display order, "
            "icons, descriptions, and visibility. Changes take effect on dashboard restart."
        )

        _global_nav = load_config("global-settings") or {}
        _nav_cfg = _global_nav.get("navigation", {})
        _nav_tools = _nav_cfg.get("tools", [])

        # Default tool definitions (used when no config exists)
        _DEFAULT_NAV_TOOLS = [
            {"key": "country-reports", "name": "Country Reports", "icon": "&#x1F30D;", "desc": "Search indexed country condition reports, curate citations, and compile exhibit bundles.", "url": "http://localhost:8501", "sort_order": 1, "visible": True, "status": "live"},
            {"key": "cover-letters", "name": "Filing Assembler", "icon": "&#x2709;&#xFE0F;", "desc": "Generate and customize cover pages for filings and correspondence.", "url": "http://localhost:8504", "sort_order": 2, "visible": True, "status": "live"},
            {"key": "brief-builder", "name": "Brief Builder", "icon": "&#x1F4DC;", "desc": "Assemble legal briefs with templated sections, arguments, and citations.", "url": "http://localhost:8507", "sort_order": 3, "visible": True, "status": "live"},
            {"key": "declaration-drafter", "name": "Declaration Drafter", "icon": "&#x1F58A;&#xFE0F;", "desc": "Guided templates for asylum declarations, personal statements, and witness affidavits.", "url": "http://localhost:8503", "sort_order": 4, "visible": True, "status": "live"},
            {"key": "timeline-builder", "name": "Timeline Builder", "icon": "&#x1F4C5;", "desc": "Build visual chronologies of persecution events, travel history, and case milestones.", "url": "http://localhost:8505", "sort_order": 5, "visible": True, "status": "live"},
            {"key": "legal-research", "name": "Legal Research", "icon": "&#x2696;&#xFE0F;", "desc": "Search case law, BIA decisions, and circuit court opinions for relevant precedent.", "url": "http://localhost:8508", "sort_order": 6, "visible": True, "status": "live"},
            {"key": "forms-assistant", "name": "Forms Assistant", "icon": "&#x1F4DD;", "desc": "Prepare and review I-589, I-130, I-485, and other immigration forms.", "url": "http://localhost:8509", "sort_order": 7, "visible": True, "status": "live"},
            {"key": "case-checklist", "name": "Case Checklist", "icon": "&#x1F4CB;", "desc": "Track filing requirements, deadlines, and document checklists per case type.", "url": "http://localhost:8506", "sort_order": 8, "visible": True, "status": "live"},
            {"key": "templates", "name": "Templates", "icon": "&#x1F4C4;", "desc": "Manage email, cover letter, government filing, and EOIR templates.", "url": "http://localhost:8510", "sort_order": 9, "visible": True, "status": "live"},
            {"key": "document-translator", "name": "Document Translator", "icon": "&#x1F310;", "desc": "Upload documents in any language, auto-translate to English, and export to Google Docs.", "url": "http://localhost:8511", "sort_order": 10, "visible": True, "status": "live"},
            {"key": "client-info", "name": "Client Info", "icon": "&#x1F464;", "desc": "View and edit Salesforce contact data. Pull client details and push updates back.", "url": "http://localhost:8512", "sort_order": 11, "visible": True, "status": "live"},
            {"key": "hearing-prep", "name": "Hearing Prep", "icon": "&#x1F3A4;", "desc": "Oral Q&A simulation for ICE cross-examination practice with audio recording and AI evaluation.", "url": "http://localhost:8514", "sort_order": 12, "visible": True, "status": "live"},
            {"key": "document-assembler", "name": "Document Assembler", "icon": "&#x1F4E6;", "desc": "Browse Box files, translate documents, assemble and paginate exhibit packages.", "url": "http://localhost:8515", "sort_order": 13, "visible": True, "status": "live"},
            {"key": "admin-panel", "name": "Admin Panel", "icon": "&#x2699;&#xFE0F;", "desc": "Configure tool settings, templates, and lists.", "url": "http://localhost:8513", "sort_order": 14, "visible": True, "status": "live"},
        ]

        if not _nav_tools:
            _nav_tools = [dict(t) for t in _DEFAULT_NAV_TOOLS]

        _STATUS_OPTIONS = ["live", "planned", "idea"]

        _nav_changed = False
        for _nt in sorted(_nav_tools, key=lambda t: t.get("sort_order", 99)):
            _nk = _nt["key"]
            with st.expander(f"{_nt.get('name', _nk)}", expanded=False):
                _c1, _c2 = st.columns(2)
                with _c1:
                    _new_name = st.text_input("Display Name", value=_nt.get("name", ""), key=f"_nav_name_{_nk}")
                    _new_icon = st.text_input("Icon (HTML entity)", value=_nt.get("icon", ""), key=f"_nav_icon_{_nk}")
                with _c2:
                    _new_order = st.number_input("Sort Order", value=_nt.get("sort_order", 99), min_value=1, max_value=99, key=f"_nav_order_{_nk}")
                    _cur_status = _nt.get("status", "live")
                    _si = _STATUS_OPTIONS.index(_cur_status) if _cur_status in _STATUS_OPTIONS else 0
                    _new_status = st.selectbox("Status", options=_STATUS_OPTIONS, index=_si, key=f"_nav_status_{_nk}")
                _new_desc = st.text_area("Description", value=_nt.get("desc", ""), height=68, key=f"_nav_desc_{_nk}")
                _new_vis = st.toggle("Visible on Dashboard", value=_nt.get("visible", True), key=f"_nav_vis_{_nk}")

                if (
                    _new_name != _nt.get("name", "")
                    or _new_icon != _nt.get("icon", "")
                    or _new_order != _nt.get("sort_order", 99)
                    or _new_status != _nt.get("status", "live")
                    or _new_desc != _nt.get("desc", "")
                    or _new_vis != _nt.get("visible", True)
                ):
                    _nt["name"] = _new_name
                    _nt["icon"] = _new_icon
                    _nt["sort_order"] = _new_order
                    _nt["status"] = _new_status
                    _nt["desc"] = _new_desc
                    _nt["visible"] = _new_vis
                    _nav_changed = True

        if _nav_changed:
            _global_nav.setdefault("navigation", {})["tools"] = _nav_tools
            save_config("global-settings", _global_nav)
            st.toast("Navigation settings saved!")
            st.rerun()

    elif gov_sub == "Component Toggles":
        # ── Component Toggles ────────────────────────────────────────
        st.subheader("Component Toggles")
        st.caption(
            "Enable or disable shared UI components per tool. "
            "Changes take effect on tool restart."
        )

        _COMPONENTS = [
            ("draft_box", "Draft Box"),
            ("preview_modal", "Preview Modal"),
            ("feedback_button", "Feedback Button"),
            ("tool_help", "Tool Help"),
            ("tool_notes", "Tool Notes"),
        ]
        _TOGGLE_TOOLS = [
            ("country-reports", "Country Reports"),
            ("cover-letters", "Filing Assembler"),
            ("brief-builder", "Brief Builder"),
            ("declaration-drafter", "Declaration Drafter"),
            ("timeline-builder", "Timeline Builder"),
            ("legal-research", "Legal Research"),
            ("forms-assistant", "Forms Assistant"),
            ("case-checklist", "Case Checklist"),
            ("evidence-indexer", "Templates"),
            ("document-translator", "Document Translator"),
            ("client-info", "Client Info"),
            ("hearing-prep", "Hearing Prep"),
            ("document-assembler", "Document Assembler"),
        ]

        _global_ct = load_config("global-settings") or {}
        _ct = _global_ct.get("component_toggles", {})
        _ct_changed = False

        for _comp_key, _comp_label in _COMPONENTS:
            with st.expander(_comp_label, expanded=False):
                _comp_cfg = _ct.get(_comp_key, {})
                for _tk, _tl in _TOGGLE_TOOLS:
                    _val = st.toggle(
                        _tl,
                        value=_comp_cfg.get(_tk, True),
                        key=f"_ct_{_comp_key}_{_tk}",
                    )
                    if _val != _comp_cfg.get(_tk, True):
                        _comp_cfg[_tk] = _val
                        _ct_changed = True
                _ct[_comp_key] = _comp_cfg

        if _ct_changed:
            _global_ct["component_toggles"] = _ct
            save_config("global-settings", _global_ct)
            st.toast("Component toggle settings saved!")
            st.rerun()

    elif gov_sub == "Sidebar Visibility":
        st.subheader("Sidebar Visibility")
        st.caption(
            "Toggle which tools show their sidebar panel. "
            "Changes take effect on tool restart."
        )
        _global = load_config("global-settings") or {}
        _sidebars = _global.get("sidebars", {})
        _changed = False
        for _tool_key, _tool_label in _SIDEBAR_TOOLS:
            _val = st.toggle(
                _tool_label,
                value=_sidebars.get(_tool_key, True),
                key=f"_adm_sb_{_tool_key}",
            )
            if _val != _sidebars.get(_tool_key, True):
                _sidebars[_tool_key] = _val
                _changed = True
        if _changed:
            _global["sidebars"] = _sidebars
            save_config("global-settings", _global)
            st.toast("Sidebar settings saved!")
            st.rerun()
    else:
        # ── Security ────────────────────────────────────────────────────
        from shared.auth import (
            is_password_set,
            is_auth_enabled,
            set_auth_enabled,
            change_password,
            reset_password,
            invalidate_all_sessions,
            get_session_hours,
            set_session_hours,
            active_session_count,
        )

        st.subheader("Security")

        # Enable/disable toggle
        _auth_on = st.toggle(
            "Enable password authentication",
            value=is_auth_enabled(),
            key="_sec_enabled",
        )
        if _auth_on != is_auth_enabled():
            set_auth_enabled(_auth_on)
            st.toast("Authentication enabled." if _auth_on else "Authentication disabled.")
            st.rerun()

        # Status indicator
        if is_password_set():
            st.success("Password is set")
        else:
            st.warning("No password configured yet.")

        st.caption(f"Active sessions: {active_session_count()}")

        # Change password (requires current password)
        @st.dialog("Change Password")
        def _change_password_dialog():
            current = st.text_input("Current Password", type="password", key="_sec_cur_pw")
            new_pw = st.text_input("New Password", type="password", key="_sec_new_pw")
            confirm = st.text_input("Confirm New Password", type="password", key="_sec_conf_pw")
            if st.button("Change Password", use_container_width=True, key="_sec_change_btn"):
                if not current or not new_pw:
                    st.error("All fields are required.")
                elif new_pw != confirm:
                    st.error("New passwords do not match.")
                else:
                    ok, msg = change_password(current, new_pw)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

        # Reset password (no current password needed — admin override)
        @st.dialog("Reset Password")
        def _reset_password_dialog():
            st.warning("This sets a new password without requiring the current one.")
            new_pw = st.text_input("New Password", type="password", key="_sec_reset_pw")
            confirm = st.text_input("Confirm New Password", type="password", key="_sec_reset_conf")
            if st.button("Reset Password", use_container_width=True, key="_sec_reset_btn"):
                if not new_pw:
                    st.error("Password cannot be empty.")
                elif new_pw != confirm:
                    st.error("Passwords do not match.")
                else:
                    reset_password(new_pw)
                    st.success("Password has been reset.")

        _sec_c1, _sec_c2, _sec_c3 = st.columns(3)
        with _sec_c1:
            if st.button("Change Password", key="_sec_open_change"):
                _change_password_dialog()
        with _sec_c2:
            if st.button("Reset Password", key="_sec_open_reset"):
                _reset_password_dialog()
        with _sec_c3:
            if st.button("Invalidate All Sessions", key="_sec_invalidate"):
                invalidate_all_sessions()
                st.toast("All sessions invalidated. Staff must re-login.")
                st.rerun()

        # Session duration
        st.markdown("---")
        st.markdown("**Session Duration**")
        _cur_hours = get_session_hours()
        _new_hours = st.slider(
            "Hours before session expires",
            min_value=1,
            max_value=72,
            value=_cur_hours,
            key="_sec_session_hours",
        )
        if _new_hours != _cur_hours:
            set_session_hours(_new_hours)
            st.toast(f"Session duration set to {_new_hours} hours.")
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# Tab 4: Usage & Billing
# ═══════════════════════════════════════════════════════════════════════════════

with tab_usage:
    _editor_api_usage()
