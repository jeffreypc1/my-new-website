"""Tool Help — persistent 'About This Tool' popup for every dashboard.

Renders a small 'ℹ️ About' button that opens a dialog with:
- Tool description and feature list
- Editable admin notes section (training links, custom comments)

Content stored in data/config/tool-help.json. Defaults are hardcoded
and written on first access.
"""

from __future__ import annotations

import streamlit as st

from shared.config_store import load_config, save_config

_CONFIG_NAME = "tool-help"

# ── Default help content for every tool ─────────────────────────────────────

_DEFAULTS: dict[str, dict] = {
    "country-reports": {
        "title": "Country Reports",
        "icon": "🌍",
        "description": "Search indexed country condition reports, curate citations, and compile exhibit bundles for asylum and humanitarian cases.",
        "features": [
            "Semantic and keyword search across 1,700+ indexed PDFs from Box",
            "Visual PDF workbench with page-level citation selection",
            "Gold citation library for verified, reusable excerpts",
            "Exhibit compiler with Bates numbering and pinpoint references",
            "Brief export to .docx and Google Docs with exhibit index",
            "Report auto-discovery from State Dept, UNHCR, HRW, UK CPINs, and RSS feeds",
            "One-click ingestion: download → Box upload → ChromaDB indexing",
        ],
    },
    "cover-letters": {
        "title": "Cover Letter Generator",
        "icon": "✉️",
        "description": "Generate and customize professional cover letters for USCIS filings and immigration court correspondence.",
        "features": [
            "14 case types with pre-configured enclosed document checklists",
            "Live preview with formal letter formatting",
            "Custom document entries with optional descriptions",
            "Draft Box — AI-powered drafting with Claude",
            "Export to .txt, .docx, .pdf, or Google Docs with optional page numbers",
            "Draft persistence — save, load, and manage multiple drafts",
        ],
    },
    "brief-builder": {
        "title": "Brief Builder",
        "icon": "📜",
        "description": "Assemble legal briefs with templated sections, standard arguments, and citations for immigration proceedings.",
        "features": [
            "5 brief types: Asylum Merits, Motion to Reopen, Appeal, Bond, Cancellation of Removal",
            "Section-based editing with expandable subsections",
            "Boilerplate insertion for standard legal arguments",
            "Live preview matching legal brief formatting standards",
            "Draft Box — AI-powered drafting with Claude",
            "Export to .txt, .docx, .pdf, or Google Docs with optional page numbers",
            "Draft persistence with case info tracking",
        ],
    },
    "declaration-drafter": {
        "title": "Declaration Drafter",
        "icon": "🖊️",
        "description": "Guided templates for asylum declarations, personal statements, and witness affidavits with attorney coaching tips.",
        "features": [
            "Guided Q&A sections with attorney tips for each question",
            "Progress bar showing completion percentage",
            "Auto-generated numbered paragraphs with perjury clause",
            "Interpreter certification block (auto-detected from language selection)",
            "Draft Box — AI-powered drafting with Claude",
            "Export to .txt, .docx, .pdf, or Google Docs with optional page numbers",
            "22 supported languages with interpreter name tracking",
        ],
    },
    "timeline-builder": {
        "title": "Timeline Builder",
        "icon": "📅",
        "description": "Build visual chronologies of persecution events, travel history, and case milestones for hearing preparation.",
        "features": [
            "Visual color-coded timeline with category-based event organization",
            "Approximate date parsing (e.g. 'Summer 2019', 'March 2020')",
            "Date ranges for multi-day events",
            "Summary statistics: event count, date range, category breakdown",
            "Draft Box — AI-powered narrative summary with Claude",
            "Export to .txt, .docx, .pdf, or Google Docs with optional page numbers",
        ],
    },
    "legal-research": {
        "title": "Legal Research",
        "icon": "⚖️",
        "description": "Search case law, BIA decisions, and circuit court opinions for relevant precedent in immigration cases.",
        "features": [
            "Curated legal topics with key case references",
            "Case law summaries with citation information",
            "Export research notes to .txt, .docx, or Google Docs",
            "Draft persistence for ongoing research projects",
        ],
    },
    "forms-assistant": {
        "title": "Forms Assistant",
        "icon": "📝",
        "description": "Prepare and review I-589, I-130, I-485, and other immigration forms with auto-fill from Salesforce.",
        "features": [
            "16 supported immigration forms with field extraction",
            "PDF upload with automatic field detection",
            "Direct Salesforce field mapping for auto-population",
            "Preparer and attorney management with saved profiles",
            "Field-by-field editing with display labels",
            "Export completed forms as filled PDFs",
        ],
    },
    "case-checklist": {
        "title": "Case Checklist",
        "icon": "📋",
        "description": "Track filing requirements, deadlines, and document checklists per case type to ensure nothing is missed.",
        "features": [
            "14 case types with configurable checklist templates",
            "Check/uncheck items with progress tracking",
            "Customizable checklist items via Admin Panel",
            "Draft persistence per case",
            "Export checklists to .txt, .docx, or Google Docs",
        ],
    },
    "evidence-indexer": {
        "title": "Evidence Indexer",
        "icon": "🗂️",
        "description": "Organize and label supporting documents with auto-generated exhibit lists for court filings.",
        "features": [
            "Configurable document categories",
            "Drag-and-drop exhibit ordering",
            "Auto-generated exhibit index with Bates references",
            "Export index to .txt, .docx, or Google Docs",
        ],
    },
    "document-translator": {
        "title": "Document Translator",
        "icon": "🌐",
        "description": "Upload documents in any language, auto-translate to English with Google Translate, and export certified translations.",
        "features": [
            "Google Translate v2 API integration",
            "OCR support via pytesseract for scanned documents",
            "Side-by-side original and translated text view",
            "Configurable language list via Admin Panel",
            "Export translations to .docx or Google Docs",
        ],
    },
    "client-info": {
        "title": "Client Info",
        "icon": "👤",
        "description": "View and edit Salesforce contact data. Pull client details, update fields, and browse Box documents.",
        "features": [
            "Full Salesforce field editor with field-level permissions",
            "Box document browser with folder navigation",
            "Direct field push back to Salesforce",
            "Client search by Customer ID",
        ],
    },
    "admin-panel": {
        "title": "Admin Panel",
        "icon": "⚙️",
        "description": "Centralized configuration for all office tools — templates, lists, prompts, API budgets, and feature governance.",
        "features": [
            "Per-tool template and list editors",
            "Salesforce field permissions management",
            "Feature Registry — lock features as Final or keep as Update",
            "Components — edit Draft Box system prompts per tool",
            "API Usage — track Anthropic and Google spending with budget alerts",
            "Sidebar visibility toggle per tool",
        ],
    },
}


def _get_help(tool_name: str) -> dict:
    """Load help content for a tool, falling back to defaults."""
    all_help = load_config(_CONFIG_NAME) or {}
    saved = all_help.get(tool_name, {})
    defaults = _DEFAULTS.get(tool_name, {
        "title": tool_name.replace("-", " ").title(),
        "icon": "🔧",
        "description": "",
        "features": [],
    })
    return {
        "title": saved.get("title", defaults.get("title", "")),
        "icon": saved.get("icon", defaults.get("icon", "")),
        "description": saved.get("description", defaults.get("description", "")),
        "features": saved.get("features", defaults.get("features", [])),
        "admin_notes": saved.get("admin_notes", ""),
    }


def _save_admin_notes(tool_name: str, notes: str) -> None:
    """Persist admin notes for a tool."""
    all_help = load_config(_CONFIG_NAME) or {}
    if tool_name not in all_help:
        defaults = _DEFAULTS.get(tool_name, {})
        all_help[tool_name] = dict(defaults)
    all_help[tool_name]["admin_notes"] = notes
    save_config(_CONFIG_NAME, all_help)


@st.dialog("About This Tool", width="large")
def _show_help_dialog(tool_name: str) -> None:
    """Modal dialog with tool description, features, and editable admin notes."""
    info = _get_help(tool_name)

    # Header
    st.markdown(f"## {info['icon']} {info['title']}")
    st.markdown(info["description"])

    # Features
    if info["features"]:
        st.markdown("### What You Can Do")
        for feat in info["features"]:
            st.markdown(f"- {feat}")

    # Admin notes (editable)
    st.markdown("---")
    st.markdown("### Notes & Training")
    st.caption("Add instructions, training links, or notes for staff. This section is editable.")
    updated_notes = st.text_area(
        "Admin notes",
        value=info.get("admin_notes", ""),
        height=120,
        key=f"_tool_help_notes_{tool_name}",
        placeholder="Add training links, tips, or notes for your team...",
        label_visibility="collapsed",
    )
    if st.button("Save Notes", type="primary", key=f"_tool_help_save_{tool_name}"):
        _save_admin_notes(tool_name, updated_notes)
        st.toast("Notes saved!")


def render_tool_help(tool_name: str) -> None:
    """Render a compact right-aligned 'About' button that opens the help dialog."""
    _, spacer, btn_col = st.columns([5, 3, 1.5])
    with btn_col:
        if st.button("ℹ️ About", key=f"_tool_help_btn_{tool_name}", use_container_width=True):
            _show_help_dialog(tool_name)
