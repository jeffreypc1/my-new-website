"""Streamlit dashboard for the Legal Research tool.

Part of the O'Brien Immigration Law tool suite. Provides a UI for searching
case law and BIA decisions, filtering by legal topic, viewing holdings,
and saving collections of relevant decisions for a case.

Flow:
1. User enters a search query in the search bar.
2. Sidebar allows filtering by legal topics and case type.
3. Results display case name, citation, holding summary.
4. User can save relevant decisions to a case collection.
5. Citation formatter converts between BIA and federal reporter styles.
"""

import streamlit as st
import requests

API_BASE = "http://localhost:8000"

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Legal Research",
    page_icon=None,
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

if "saved_decisions" not in st.session_state:
    st.session_state.saved_decisions = []  # list of decision dicts
if "collection_saved" not in st.session_state:
    st.session_state.collection_saved = False

# ---------------------------------------------------------------------------
# Custom CSS (consistent with country-reports-tool)
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main-header {
        color: #1a2744;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0;
    }
    .sub-header {
        color: #5a6a85;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .case-name {
        font-size: 1.05rem;
        font-weight: 600;
        color: #1a2744;
    }
    .citation {
        font-size: 0.9rem;
        color: #2b5797;
        font-style: italic;
    }
    .court-badge {
        display: inline-block;
        background: #1a2744;
        color: #ffffff;
        padding: 2px 10px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 8px;
    }
    .topic-tag {
        display: inline-block;
        background: #e2e8f0;
        color: #334155;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        margin-right: 4px;
        margin-top: 4px;
    }
    .holding-text {
        font-size: 0.9rem;
        line-height: 1.6;
        color: #334155;
        margin-top: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="main-header">Legal Research</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">Search immigration case law, BIA decisions, and federal court holdings</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar: topic filters
# ---------------------------------------------------------------------------

st.sidebar.header("Filters")

# Fetch available topics from the API
topics: list[str] = []
try:
    resp = requests.get(f"{API_BASE}/api/topics", timeout=10)
    resp.raise_for_status()
    topics = resp.json()
except Exception:
    st.sidebar.warning(
        "Could not connect to API. Is the backend running on port 8000?"
    )

# Topic categories for the sidebar
TOPIC_GROUPS = {
    "Asylum Grounds": ["asylum", "withholding", "CAT"],
    "Procedural Issues": ["one-year bar", "firm resettlement", "credibility"],
    "Legal Standards": ["particular social group", "nexus"],
}

selected_topics: list[str] = []
for group_name, group_topics in TOPIC_GROUPS.items():
    available = [t for t in group_topics if t in topics]
    if available:
        selected = st.sidebar.multiselect(
            group_name,
            options=available,
            default=[],
        )
        selected_topics.extend(selected)

# Circuit-specific filter
# TODO: Add circuit selection when circuit data is indexed
st.sidebar.markdown("---")
st.sidebar.caption("Circuit-specific filtering coming soon.")

# ---------------------------------------------------------------------------
# Sidebar: citation formatter
# ---------------------------------------------------------------------------

st.sidebar.markdown("---")
st.sidebar.header("Citation Formatter")

citation_style = st.sidebar.radio(
    "Citation Style",
    ["BIA Style", "Federal Reporter Style"],
    horizontal=True,
)

format_input = st.sidebar.text_input(
    "Enter citation to format",
    placeholder="e.g. 19 I&N Dec. 211",
)
if format_input:
    # TODO: Implement actual citation format conversion
    if citation_style == "BIA Style":
        st.sidebar.code(format_input)
    else:
        st.sidebar.code(format_input)
    st.sidebar.caption("Citation formatting is a placeholder. Full conversion coming soon.")

# ---------------------------------------------------------------------------
# Sidebar: save collection
# ---------------------------------------------------------------------------

st.sidebar.markdown("---")
st.sidebar.header("Save to Case")

case_name = st.sidebar.text_input("Case Name", placeholder="e.g. Garcia-Lopez")
a_number = st.sidebar.text_input("A-Number", placeholder="e.g. A-123-456-789")

if st.sidebar.button(
    "Save Collection",
    disabled=not st.session_state.saved_decisions or not case_name,
):
    try:
        payload = {
            "case_name": case_name,
            "a_number": a_number,
            "decisions": [
                {
                    "decision_key": d.get("name", ""),
                    "citation": d.get("citation", ""),
                    "relevance_note": "",
                }
                for d in st.session_state.saved_decisions
            ],
        }
        resp = requests.post(
            f"{API_BASE}/api/collections",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        st.session_state.collection_saved = True
        st.sidebar.success(f"Saved {len(st.session_state.saved_decisions)} decisions to {case_name}")
    except Exception as e:
        st.sidebar.error(f"Failed to save: {e}")

if st.session_state.saved_decisions:
    st.sidebar.caption(
        f"{len(st.session_state.saved_decisions)} decision(s) in collection"
    )

# ---------------------------------------------------------------------------
# Main area: search bar
# ---------------------------------------------------------------------------

query = st.text_input(
    "Search case law",
    placeholder="e.g. particular social group, well-founded fear, domestic violence asylum",
)

# ---------------------------------------------------------------------------
# Main area: search results
# ---------------------------------------------------------------------------

if query:
    params: dict = {"q": query, "n": 20}
    if selected_topics:
        params["topics"] = selected_topics

    try:
        resp = requests.get(
            f"{API_BASE}/api/search",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        results = resp.json()
    except Exception as e:
        st.error(f"Search failed: {e}")
        results = []

    if results:
        st.markdown(f"**{len(results)} result(s)** for *{query}*")

        for idx, result in enumerate(results):
            name = result.get("name", "Unknown")
            citation = result.get("citation", "")
            court = result.get("court", "")
            decision_date = result.get("date", "")
            holding = result.get("holding", "")
            result_topics = result.get("topics", [])

            # Court badge and case name
            st.markdown(
                f'<span class="court-badge">{court}</span>'
                f'<span class="case-name">{name}</span>',
                unsafe_allow_html=True,
            )

            # Citation and date
            st.markdown(
                f'<span class="citation">{citation}</span>'
                f' ({decision_date})',
                unsafe_allow_html=True,
            )

            # Topic tags
            if result_topics:
                tags_html = " ".join(
                    f'<span class="topic-tag">{t}</span>' for t in result_topics
                )
                st.markdown(tags_html, unsafe_allow_html=True)

            # Holding summary
            st.markdown(
                f'<div class="holding-text">{holding}</div>',
                unsafe_allow_html=True,
            )

            # Save to Case button
            is_saved = any(
                d.get("citation") == citation
                for d in st.session_state.saved_decisions
            )
            col_save, col_view = st.columns([1, 1])
            with col_save:
                if is_saved:
                    st.button(
                        "Saved",
                        key=f"saved_{idx}",
                        disabled=True,
                    )
                else:
                    if st.button("Save to Case", key=f"save_{idx}"):
                        st.session_state.saved_decisions.append(result)
                        st.rerun()
            with col_view:
                # TODO: Link to full decision text view
                st.button("View Full Text", key=f"view_{idx}", disabled=True)

            st.markdown("---")
    else:
        st.info("No results found. Try different search terms or broaden your topic filters.")
elif not query:
    st.info(
        "Enter a search term above to find relevant case law, BIA decisions, "
        "and federal court holdings."
    )
