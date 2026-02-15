"""Streamlit dashboard for Country Conditions Assembler."""

import streamlit as st
import requests

from app.citations import format_citation

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Country Conditions Assembler",
    page_icon=None,
    layout="wide",
)

# --- Custom CSS ---
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
    .result-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    .country-tag {
        display: inline-block;
        background: #1a2744;
        color: #ffffff;
        padding: 2px 10px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 8px;
    }
    .source-label {
        color: #5a6a85;
        font-size: 0.85rem;
    }
    .score-label {
        color: #8896ab;
        font-size: 0.8rem;
        float: right;
    }
    .snippet-text {
        color: #2d3748;
        font-size: 0.95rem;
        line-height: 1.6;
        margin-top: 0.75rem;
    }
    .box-link {
        font-size: 0.85rem;
        margin-left: 8px;
    }
    .chunk-meta {
        color: #8896ab;
        font-size: 0.78rem;
        margin-bottom: 0.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Header ---
st.markdown('<div class="main-header">Country Conditions Assembler</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Search indexed country condition reports for immigration case support</div>',
    unsafe_allow_html=True,
)

# --- Sidebar: Country Filter ---
st.sidebar.header("Filters")

try:
    countries_resp = requests.get(f"{API_BASE}/api/countries", timeout=5)
    countries_resp.raise_for_status()
    available_countries = countries_resp.json()
except Exception:
    available_countries = []
    st.sidebar.warning("Could not connect to API. Is the backend running on port 8000?")

selected_countries = st.sidebar.multiselect(
    "Countries",
    options=available_countries,
    default=[],
    help="Leave empty to search all countries",
)

n_results = st.sidebar.slider("Source documents to return", min_value=5, max_value=100, value=20, step=5)

# --- Search ---
query = st.text_input("Search reports", placeholder="e.g. gang violence, political persecution, forced recruitment")

if query:
    params: dict = {"q": query, "n": n_results}
    if selected_countries:
        params["countries"] = selected_countries

    try:
        resp = requests.get(f"{API_BASE}/api/search/grouped", params=params, timeout=30)
        resp.raise_for_status()
        groups = resp.json()
    except Exception as e:
        st.error(f"Search failed: {e}")
        groups = []

    if groups:
        st.markdown(f"**{len(groups)} source documents** for *{query}*")

        for group in groups:
            source = group.get("source", "")
            country = group.get("country", "Unknown")
            best_distance = group.get("best_distance", 0)
            box_url = group.get("box_url")
            chunks = group.get("chunks", [])
            relevance = max(0, 1 - best_distance)

            # Box link HTML
            box_link_html = ""
            if box_url:
                box_link_html = f'<a class="box-link" href="{box_url}" target="_blank">View Original &rarr;</a>'

            st.markdown(
                f"""<div class="result-card">
                    <span class="country-tag">{country}</span>
                    <span class="source-label">{source}</span>
                    {box_link_html}
                    <span class="score-label">Relevance: {relevance:.0%} &middot; {len(chunks)} excerpt{"s" if len(chunks) != 1 else ""}</span>
                </div>""",
                unsafe_allow_html=True,
            )

            with st.expander(f"Excerpts from {source}", expanded=False):
                for chunk in chunks:
                    text = chunk.get("text", "")
                    chunk_index = chunk.get("chunk_index", 0)
                    distance = chunk.get("distance", 0)
                    chunk_rel = max(0, 1 - distance)
                    display_text = text[:500] + ("..." if len(text) > 500 else "")

                    st.markdown(
                        f'<div class="chunk-meta">Chunk {chunk_index} &middot; Relevance: {chunk_rel:.0%}</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="snippet-text">{display_text}</div>',
                        unsafe_allow_html=True,
                    )

                    citation = format_citation(text, source, country, chunk_index)
                    st.code(citation, language=None)
    else:
        st.info("No results found. Try a different query or broaden your filters.")
elif not query:
    st.info("Enter a search term above to find relevant country condition report excerpts.")
