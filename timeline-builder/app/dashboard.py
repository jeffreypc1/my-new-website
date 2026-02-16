"""Timeline Builder — Streamlit dashboard.

Visual timeline creation for immigration case preparation. Attorneys can
build chronological timelines with approximate dates, color-coded categories,
and export to Word documents for hearing prep.
"""

from __future__ import annotations

import html as html_mod
import io
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import streamlit as st
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from app.events import (
    CATEGORY_DESCRIPTIONS,
    EVENT_CATEGORIES,
    TimelineEvent,
    add_event,
    delete_event,
    delete_timeline,
    list_timelines,
    load_timeline,
    new_timeline,
    new_timeline_id,
    parse_approximate_date,
    parsed_date_to_display,
    save_timeline,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared.google_upload import upload_to_google_docs
from shared.client_banner import render_client_banner

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Timeline Builder — O'Brien Immigration Law",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────────────────

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Hide Streamlit chrome */
#MainMenu, header[data-testid="stHeader"], footer,
div[data-testid="stToolbar"] { display: none !important; }

.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Navigation bar */
.nav-bar {
    display: flex;
    align-items: center;
    padding: 10px 4px;
    margin: -1rem 0 1.2rem 0;
    border-bottom: 1px solid rgba(0,0,0,0.07);
}
.nav-back {
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 500;
    color: #0066CC;
    text-decoration: none;
    min-width: 150px;
}
.nav-back:hover { color: #004499; text-decoration: underline; }
.nav-title {
    flex: 1;
    text-align: center;
    font-family: 'Inter', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: #1a2744;
    letter-spacing: -0.02em;
}
.nav-firm {
    font-weight: 400;
    color: #86868b;
    font-size: 0.85rem;
    margin-left: 8px;
}
.nav-spacer { min-width: 150px; }

/* Summary stats */
.stats-row {
    display: flex;
    gap: 16px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}
.stat-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 14px 20px;
    min-width: 140px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.stat-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1a2744;
    line-height: 1.2;
}
.stat-label {
    font-size: 0.78rem;
    color: #5a6a85;
    font-weight: 500;
    margin-top: 2px;
}

/* Category legend */
.cat-legend {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 20px;
}
.cat-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.8rem;
    color: #5a6a85;
    font-weight: 500;
}
.cat-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}
.cat-count {
    background: #f0f4fa;
    border-radius: 10px;
    padding: 1px 7px;
    font-size: 0.72rem;
    font-weight: 600;
    color: #4a7ddb;
    margin-left: 2px;
}

/* Timeline */
.timeline {
    position: relative;
    padding: 20px 0;
    margin-left: 8px;
}
.timeline::before {
    content: '';
    position: absolute;
    left: 30px;
    top: 0;
    bottom: 0;
    width: 3px;
    background: #e2e8f0;
    border-radius: 2px;
}
.timeline-event {
    position: relative;
    margin-left: 60px;
    margin-bottom: 20px;
    padding: 16px 20px;
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    transition: box-shadow 0.15s ease;
}
.timeline-event:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.timeline-dot {
    position: absolute;
    left: -38px;
    top: 20px;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    border: 3px solid #fff;
    box-shadow: 0 0 0 2px currentColor;
    background: currentColor;
}
.timeline-date {
    font-size: 0.82rem;
    font-weight: 600;
    margin-bottom: 4px;
}
.timeline-title {
    font-size: 1rem;
    font-weight: 700;
    color: #1a2744;
    margin-bottom: 4px;
    line-height: 1.3;
}
.timeline-desc {
    font-size: 0.88rem;
    color: #4a5568;
    line-height: 1.5;
    margin-bottom: 6px;
}
.timeline-badge {
    display: inline-block;
    padding: 2px 10px;
    font-size: 0.7rem;
    font-weight: 600;
    border-radius: 12px;
    color: #fff;
}
.timeline-date-range {
    font-size: 0.75rem;
    color: #86868b;
    font-weight: 500;
    margin-left: 8px;
}
.timeline-delete {
    position: absolute;
    top: 10px;
    right: 12px;
    background: none;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    color: #a0aec0;
    cursor: pointer;
    font-size: 0.75rem;
    padding: 2px 7px;
    line-height: 1;
    transition: all 0.15s ease;
}
.timeline-delete:hover {
    color: #dc3545;
    border-color: #dc3545;
    background: #fff5f5;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #a0aec0;
}
.empty-state-icon {
    font-size: 3rem;
    margin-bottom: 12px;
    opacity: 0.5;
}
.empty-state-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #5a6a85;
    margin-bottom: 4px;
}
.empty-state-text {
    font-size: 0.88rem;
    color: #a0aec0;
}

/* Saved toast */
.saved-toast {
    font-size: 0.8rem;
    color: #2e7d32;
    font-weight: 600;
}

/* Section header */
.section-header {
    color: #1a2744;
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid #e2e8f0;
}

/* Print-friendly styles */
@media print {
    .nav-bar, .stSidebar, .timeline-delete { display: none !important; }
    .timeline-event { break-inside: avoid; }
    .stApp { background: #fff !important; }
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Navigation bar ───────────────────────────────────────────────────────────

st.markdown(
    """
<div class="nav-bar">
    <a href="http://localhost:8502" class="nav-back">&#8592; Staff Dashboard</a>
    <div class="nav-title">Timeline Builder<span class="nav-firm">&mdash; O'Brien Immigration Law</span></div>
    <div class="nav-spacer"></div>
</div>
""",
    unsafe_allow_html=True,
)

render_client_banner()

# ── Session state defaults ───────────────────────────────────────────────────

_DEFAULTS: dict = {
    "timeline_id": None,
    "timeline": None,
    "last_saved_msg": "",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── Helpers ──────────────────────────────────────────────────────────────────


def _ensure_timeline() -> dict:
    """Make sure we have a current timeline in session state."""
    if st.session_state.timeline is None:
        tl = new_timeline()
        st.session_state.timeline_id = tl["id"]
        st.session_state.timeline = tl
    return st.session_state.timeline


def _do_save() -> None:
    """Save the current timeline to disk."""
    tl = _ensure_timeline()
    tl["case_name"] = st.session_state.get("inp_case_name", "")
    tl["client_name"] = st.session_state.get("inp_client_name", "")
    save_timeline(tl)
    label = tl["client_name"] or tl["case_name"] or "timeline"
    st.session_state.last_saved_msg = f"Saved — {label}"


def _do_new() -> None:
    """Start a fresh timeline."""
    tl = new_timeline()
    st.session_state.timeline_id = tl["id"]
    st.session_state.timeline = tl
    st.session_state.last_saved_msg = ""
    for k in ("inp_case_name", "inp_client_name"):
        if k in st.session_state:
            del st.session_state[k]


def _do_load(timeline_id: str) -> None:
    """Load a timeline from disk into session state."""
    tl = load_timeline(timeline_id)
    if tl is None:
        return
    st.session_state.timeline_id = tl["id"]
    st.session_state.timeline = tl
    st.session_state.last_saved_msg = ""
    st.session_state.inp_case_name = tl.get("case_name", "")
    st.session_state.inp_client_name = tl.get("client_name", "")


def _do_delete_event(event_id: str) -> None:
    """Delete an event from the current timeline."""
    tl = _ensure_timeline()
    delete_event(tl, event_id)


def _build_timeline_html(events: list[dict]) -> str:
    """Render a professional vertical timeline as HTML."""
    esc = html_mod.escape

    if not events:
        return (
            '<div class="empty-state">'
            '<div class="empty-state-icon">&#128197;</div>'
            '<div class="empty-state-title">No events yet</div>'
            '<div class="empty-state-text">Use the sidebar form to add the first event to this timeline.</div>'
            "</div>"
        )

    parts: list[str] = ['<div class="timeline">']

    for ev in events:
        cat = ev.get("category", "Personal")
        color = EVENT_CATEGORIES.get(cat, "#6c757d")
        date_text = esc(ev.get("date_text", ""))
        title = esc(ev.get("title", ""))
        desc = esc(ev.get("description", ""))
        end_date = ev.get("end_date_text", "")
        event_id = ev.get("id", "")

        date_range_html = ""
        if end_date:
            date_range_html = f'<span class="timeline-date-range">to {esc(end_date)}</span>'

        desc_html = ""
        if desc:
            desc_html = f'<div class="timeline-desc">{desc}</div>'

        parts.append(f"""
        <div class="timeline-event" style="border-left: 4px solid {color};" data-event-id="{event_id}">
            <div class="timeline-dot" style="color: {color};"></div>
            <div class="timeline-date" style="color: {color};">{date_text}{date_range_html}</div>
            <div class="timeline-title">{title}</div>
            {desc_html}
            <span class="timeline-badge" style="background: {color};">{esc(cat)}</span>
        </div>""")

    parts.append("</div>")
    return "\n".join(parts)


def _build_stats_html(events: list[dict]) -> str:
    """Build summary statistics HTML."""
    if not events:
        return ""

    total = len(events)

    # Date range
    dates = [e.get("parsed_date", "9999-99-99") for e in events]
    valid_dates = [d for d in dates if d != "9999-99-99"]
    if valid_dates:
        earliest = parsed_date_to_display(min(valid_dates))
        latest = parsed_date_to_display(max(valid_dates))
        date_range = f"{earliest} &mdash; {latest}"
    else:
        date_range = "No dates"

    # Category counts
    cat_counts = Counter(e.get("category", "Personal") for e in events)

    parts: list[str] = ['<div class="stats-row">']
    parts.append(
        f'<div class="stat-card">'
        f'<div class="stat-value">{total}</div>'
        f'<div class="stat-label">Total Events</div>'
        f"</div>"
    )
    parts.append(
        f'<div class="stat-card">'
        f'<div class="stat-value" style="font-size:1rem;">{date_range}</div>'
        f'<div class="stat-label">Date Range</div>'
        f"</div>"
    )
    parts.append("</div>")

    # Category legend with counts
    parts.append('<div class="cat-legend">')
    for cat, color in EVENT_CATEGORIES.items():
        count = cat_counts.get(cat, 0)
        if count > 0:
            parts.append(
                f'<div class="cat-item">'
                f'<span class="cat-dot" style="background:{color};"></span>'
                f"{html_mod.escape(cat)}"
                f'<span class="cat-count">{count}</span>'
                f"</div>"
            )
    parts.append("</div>")

    return "\n".join(parts)


def _build_docx(timeline: dict) -> bytes:
    """Build a Word document with a formatted event table."""
    doc = Document()

    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    def _run(para, text: str, size: int = 11, bold: bool = False, italic: bool = False):
        r = para.add_run(text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(size)
        r.bold = bold
        r.italic = italic
        return r

    # Title
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _run(p, "CASE TIMELINE", size=14, bold=True)

    # Client / case info
    client = timeline.get("client_name", "")
    case = timeline.get("case_name", "")
    if client or case:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        info_parts = []
        if client:
            info_parts.append(f"Client: {client}")
        if case:
            info_parts.append(f"Case: {case}")
        _run(p, " | ".join(info_parts), size=10)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _run(p, f"Prepared {date.today().strftime('%B %d, %Y')}", size=9, italic=True)

    doc.add_paragraph()  # spacer

    # Table
    events = timeline.get("events", [])
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"

    # Header row
    headers = ["Date", "Event", "Category", "Description"]
    for i, header_text in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        r = p.add_run(header_text)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)

    # Data rows
    for ev in events:
        row = table.add_row()
        date_display = ev.get("date_text", "")
        end_date = ev.get("end_date_text", "")
        if end_date:
            date_display += f" to {end_date}"

        values = [
            date_display,
            ev.get("title", ""),
            ev.get("category", ""),
            ev.get("description", ""),
        ]
        for i, val in enumerate(values):
            cell = row.cells[i]
            cell.text = ""
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            r.font.size = Pt(10)

    # Set column widths
    for row in table.rows:
        row.cells[0].width = Inches(1.3)
        row.cells[1].width = Inches(2.0)
        row.cells[2].width = Inches(1.0)
        row.cells[3].width = Inches(3.0)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _build_plain_text(timeline: dict) -> str:
    """Build a plain-text export of the timeline."""
    lines: list[str] = []
    client = timeline.get("client_name", "")
    case = timeline.get("case_name", "")

    lines.append("CASE TIMELINE")
    lines.append("=" * 60)
    if client:
        lines.append(f"Client: {client}")
    if case:
        lines.append(f"Case:   {case}")
    lines.append(f"Date:   {date.today().strftime('%B %d, %Y')}")
    lines.append("=" * 60)
    lines.append("")

    events = timeline.get("events", [])
    if not events:
        lines.append("(No events)")
    else:
        for ev in events:
            date_text = ev.get("date_text", "Unknown")
            end_date = ev.get("end_date_text", "")
            if end_date:
                date_text += f" to {end_date}"
            title = ev.get("title", "")
            cat = ev.get("category", "")
            desc = ev.get("description", "")

            lines.append(f"[{date_text}] [{cat}]")
            lines.append(f"  {title}")
            if desc:
                lines.append(f"  {desc}")
            lines.append("")

    lines.append("=" * 60)
    lines.append(f"Total events: {len(events)}")
    return "\n".join(lines)


# ── Sidebar ──────────────────────────────────────────────────────────────────

tl = _ensure_timeline()

with st.sidebar:
    # Timeline management
    st.markdown("#### Timelines")
    btn_cols = st.columns(2)
    with btn_cols[0]:
        if st.button("New", use_container_width=True):
            _do_new()
            st.rerun()
    with btn_cols[1]:
        save_clicked = st.button("Save", use_container_width=True, type="primary")

    saved_timelines = list_timelines()
    if saved_timelines:
        labels_map = {
            t["id"]: f"{t['client_name'] or 'Unnamed'} — {t['case_name'] or 'No case'} ({t['event_count']} events)"
            for t in saved_timelines
        }
        tl_ids = list(labels_map.keys())
        selected_tl = st.selectbox(
            "Load a saved timeline",
            options=[""] + tl_ids,
            format_func=lambda x: labels_map.get(x, "Select..."),
            label_visibility="collapsed",
        )
        load_cols = st.columns(2)
        with load_cols[0]:
            if selected_tl and st.button("Load", use_container_width=True):
                _do_load(selected_tl)
                st.rerun()
        with load_cols[1]:
            if selected_tl and st.button("Delete", use_container_width=True):
                delete_timeline(selected_tl)
                if st.session_state.timeline_id == selected_tl:
                    _do_new()
                st.rerun()

    if st.session_state.last_saved_msg:
        st.markdown(
            f'<div class="saved-toast">{html_mod.escape(st.session_state.last_saved_msg)}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # Client / case info
    st.markdown("#### Case Info")
    client_name = st.text_input(
        "Client Name",
        value=tl.get("client_name", ""),
        key="inp_client_name",
    )
    case_name = st.text_input(
        "Case Name",
        value=tl.get("case_name", ""),
        key="inp_case_name",
        placeholder="e.g. Asylum — Garcia",
    )

    st.divider()

    # Add Event form
    st.markdown("#### Add Event")

    event_title = st.text_input(
        "Event Title",
        key="inp_event_title",
        placeholder="e.g. Fled home country",
    )
    event_date = st.text_input(
        "Date",
        key="inp_event_date",
        placeholder='e.g. "March 2019", "Summer 2020"',
    )
    event_end_date = st.text_input(
        "End Date (optional, for ranges)",
        key="inp_event_end_date",
        placeholder='e.g. "June 2019"',
    )
    event_category = st.selectbox(
        "Category",
        options=list(EVENT_CATEGORIES.keys()),
        format_func=lambda x: f"{x} — {CATEGORY_DESCRIPTIONS.get(x, '')}",
        key="inp_event_category",
    )
    event_description = st.text_area(
        "Description",
        key="inp_event_desc",
        height=100,
        placeholder="Details about this event...",
    )

    add_disabled = not (event_title and event_date)
    if st.button("Add Event", type="primary", use_container_width=True, disabled=add_disabled):
        new_ev = TimelineEvent.create(
            title=event_title,
            date_text=event_date,
            category=event_category,
            description=event_description,
            end_date_text=event_end_date,
        )
        add_event(tl, new_ev)
        # Clear form fields
        for k in ("inp_event_title", "inp_event_date", "inp_event_end_date", "inp_event_desc"):
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

    if event_date:
        parsed = parse_approximate_date(event_date)
        display = parsed_date_to_display(parsed)
        st.caption(f"Parsed as: {display}")

    st.divider()

    # Export
    st.markdown("#### Export")


# ── Handle save (after sidebar widgets render) ───────────────────────────────

if save_clicked:
    _do_save()
    st.rerun()


# ── Main area ────────────────────────────────────────────────────────────────

events = tl.get("events", [])

# Summary stats
stats_html = _build_stats_html(events)
if stats_html:
    st.markdown(stats_html, unsafe_allow_html=True)

# Visual timeline
timeline_html = _build_timeline_html(events)
st.markdown(timeline_html, unsafe_allow_html=True)

# Delete buttons (rendered outside HTML because Streamlit buttons need Python)
if events:
    st.markdown(
        '<div class="section-header">Manage Events</div>',
        unsafe_allow_html=True,
    )
    for ev in events:
        event_id = ev.get("id", "")
        title = ev.get("title", "Untitled")
        date_text = ev.get("date_text", "")
        cat = ev.get("category", "Personal")
        color = EVENT_CATEGORIES.get(cat, "#6c757d")

        col_info, col_del = st.columns([6, 1])
        with col_info:
            st.markdown(
                f'<span style="color:{color}; font-weight:600;">{html_mod.escape(date_text)}</span> '
                f"&mdash; {html_mod.escape(title)}",
                unsafe_allow_html=True,
            )
        with col_del:
            if st.button("Delete", key=f"del_{event_id}", use_container_width=True):
                _do_delete_event(event_id)
                st.rerun()

# Export controls
st.markdown("---")
exp_cols = st.columns(2)

with exp_cols[0]:
    plain_text = _build_plain_text(tl)
    file_label = (client_name or "Timeline").replace(" ", "_")
    st.download_button(
        "Download .txt",
        data=plain_text,
        file_name=f"Timeline_{file_label}.txt",
        mime="text/plain",
        use_container_width=True,
        disabled=not events,
    )

with exp_cols[1]:
    if events:
        docx_bytes = _build_docx(tl)
        st.download_button(
            "Download .docx",
            data=docx_bytes,
            file_name=f"Timeline_{file_label}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
        if st.button("Upload to Google Docs", use_container_width=True):
            with st.spinner("Uploading to Google Docs..."):
                try:
                    url = upload_to_google_docs(docx_bytes, f"Timeline - {client_name or 'Timeline'}")
                    st.session_state.google_doc_url = url
                except Exception as e:
                    st.error(f"Upload failed: {e}")
        if st.session_state.get("google_doc_url"):
            st.markdown(f"[Open Google Doc]({st.session_state.google_doc_url})")
    else:
        st.button("Download .docx", disabled=True, use_container_width=True)
