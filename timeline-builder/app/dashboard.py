"""Streamlit dashboard for Timeline Builder."""

from __future__ import annotations

import requests
import streamlit as st

from app.events import EVENT_CATEGORIES, parse_approximate_date

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Timeline Builder",
    page_icon=None,
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------

if "current_timeline_id" not in st.session_state:
    st.session_state.current_timeline_id = None
if "events" not in st.session_state:
    st.session_state.events = []

# ---------------------------------------------------------------------------
# Sidebar: case selector, client info, timeline name
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Timeline Builder")
    st.caption("O'Brien Immigration Law")
    st.divider()

    # --- Select or create a timeline ----------------------------------------

    st.subheader("Case / Timeline")

    # TODO: Fetch existing timelines from API for the selector
    timeline_options: list[str] = []
    try:
        resp = requests.get(f"{API_BASE}/api/timelines", timeout=5)
        if resp.ok:
            for t in resp.json():
                timeline_options.append(f"{t['id']}|{t['name']}")
    except requests.ConnectionError:
        st.warning("API not reachable. Start the FastAPI server on port 8000.")

    selected = st.selectbox(
        "Select timeline",
        options=["-- New Timeline --"] + timeline_options,
        format_func=lambda x: x.split("|")[-1] if "|" in x else x,
    )

    st.divider()

    # --- Client info for new timelines -------------------------------------

    client_name = st.text_input("Client name")
    timeline_name = st.text_input("Timeline name")

    if st.button("Create Timeline", disabled=not timeline_name):
        # TODO: POST to /api/timelines and set session state
        try:
            resp = requests.post(
                f"{API_BASE}/api/timelines",
                json={"name": timeline_name, "client": client_name},
                timeout=5,
            )
            if resp.ok:
                data = resp.json()
                st.session_state.current_timeline_id = data["id"]
                st.session_state.events = []
                st.success(f"Created timeline: {data['name']}")
                st.rerun()
        except requests.ConnectionError:
            st.error("Cannot reach API server.")

    # --- Load selected timeline --------------------------------------------

    if selected and selected != "-- New Timeline --" and "|" in selected:
        tid = selected.split("|")[0]
        if tid != st.session_state.current_timeline_id:
            try:
                resp = requests.get(f"{API_BASE}/api/timelines/{tid}", timeout=5)
                if resp.ok:
                    data = resp.json()
                    st.session_state.current_timeline_id = data["id"]
                    st.session_state.events = data.get("events", [])
            except requests.ConnectionError:
                pass

    st.divider()

    # --- Export buttons -----------------------------------------------------

    st.subheader("Export")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Word Table"):
            # TODO: call /api/export/docx and offer download
            st.info("DOCX export coming soon.")
    with col_b:
        if st.button("Visual PDF"):
            # TODO: call /api/export/pdf and offer download
            st.info("PDF export coming soon.")


# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

st.title("Timeline Builder")

# ---------------------------------------------------------------------------
# Add Event form
# ---------------------------------------------------------------------------

with st.expander("Add Event", expanded=True):
    col1, col2 = st.columns([2, 1])

    with col1:
        event_date = st.text_input(
            "Date (can be approximate)",
            placeholder='e.g. "March 2019", "2018", "Summer 2020"',
        )
        event_desc = st.text_area("Event description")

    with col2:
        event_cat = st.selectbox("Category", options=list(EVENT_CATEGORIES.keys()))
        event_loc = st.text_input("Location", placeholder="City, Country")
        event_ref = st.text_input(
            "Supporting evidence",
            placeholder="Exhibit A-3, Declaration p.4",
        )

    if st.button("Add Event", type="primary", disabled=not (event_date and event_desc)):
        new_event = {
            "date_text": event_date,
            "date_sortable": parse_approximate_date(event_date),
            "description": event_desc,
            "category": event_cat,
            "location": event_loc,
            "evidence_ref": event_ref,
        }
        st.session_state.events.append(new_event)
        # Sort by date_sortable
        st.session_state.events.sort(key=lambda e: e.get("date_sortable", ""))

        # TODO: persist via PUT /api/timelines/{id}/events
        st.success("Event added.")
        st.rerun()


# ---------------------------------------------------------------------------
# Event list (chronological, color-coded)
# ---------------------------------------------------------------------------

st.subheader("Events")

if not st.session_state.events:
    st.info("No events yet. Use the form above to add the first event.")
else:
    for idx, ev in enumerate(st.session_state.events):
        cat = ev.get("category", "Personal")
        color = EVENT_CATEGORIES.get(cat, "#95a5a6")
        with st.container():
            cols = st.columns([0.5, 2, 3, 1.5, 1.5, 0.5])
            cols[0].markdown(
                f'<span style="color:{color}; font-size:1.5rem;">&#9679;</span>',
                unsafe_allow_html=True,
            )
            cols[1].markdown(f"**{ev.get('date_text', '')}**")
            cols[2].write(ev.get("description", ""))
            cols[3].caption(ev.get("location", ""))
            cols[4].caption(ev.get("evidence_ref", ""))
            if cols[5].button("X", key=f"del_{idx}"):
                st.session_state.events.pop(idx)
                st.rerun()
        st.divider()


# ---------------------------------------------------------------------------
# Visual timeline display
# ---------------------------------------------------------------------------

st.subheader("Visual Timeline")

if st.session_state.events:
    # Render a simple CSS-based vertical timeline
    timeline_html = '<div style="position:relative; padding:20px 0 20px 40px; border-left:3px solid #ccc;">'
    for ev in st.session_state.events:
        cat = ev.get("category", "Personal")
        color = EVENT_CATEGORIES.get(cat, "#95a5a6")
        date_text = ev.get("date_text", "")
        desc = ev.get("description", "")
        loc = ev.get("location", "")
        loc_span = f' <span style="color:#888;">({loc})</span>' if loc else ""

        timeline_html += f"""
        <div style="position:relative; margin-bottom:24px;">
            <div style="
                position:absolute; left:-49px; top:0;
                width:16px; height:16px; border-radius:50%;
                background:{color}; border:2px solid #fff;
            "></div>
            <div style="
                background:#f8f9fa; border-radius:8px; padding:12px 16px;
                border-left:4px solid {color};
            ">
                <strong style="color:{color};">{date_text}</strong>{loc_span}
                <br/>
                <span>{desc}</span>
            </div>
        </div>
        """
    timeline_html += "</div>"
    st.markdown(timeline_html, unsafe_allow_html=True)

    # TODO: Add drag-to-reorder for events that share the same date_sortable.
    #       Streamlit does not natively support drag-and-drop; consider
    #       streamlit-sortables or manual up/down buttons as a fallback.
else:
    st.caption("Add events above to see the visual timeline.")
