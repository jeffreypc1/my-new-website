"""O'Brien Immigration Law — Staff Tools Dashboard."""

from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Staff Tools — O'Brien Immigration Law",
    page_icon="<img src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>&#9878;</text></svg>' />",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Load mission doc ──
MISSION_PATH = Path(__file__).resolve().parent.parent / "MISSION.md"


def _load_mission() -> str:
    if MISSION_PATH.exists():
        return MISSION_PATH.read_text()
    return "_No mission document found._"


# ── Custom CSS for a polished look ──
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Hide Streamlit chrome */
#MainMenu, header[data-testid="stHeader"], footer,
div[data-testid="stToolbar"] { display: none !important; }
div[data-testid="stSidebarCollapsedControl"] { display: none !important; }

/* Root */
.stApp {
    background: linear-gradient(160deg, #f8f9fc 0%, #eef1f8 50%, #e8edf6 100%);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Hero section */
.hero-container {
    text-align: center;
    padding: 3.5rem 1rem 1rem;
}

.hero-badge {
    display: inline-block;
    padding: 6px 18px;
    background: rgba(0, 102, 204, 0.08);
    color: #0066CC;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    border-radius: 980px;
    margin-bottom: 1rem;
}

.hero-title {
    font-family: 'Inter', sans-serif;
    font-size: clamp(2rem, 5vw, 3.25rem);
    font-weight: 800;
    letter-spacing: -0.04em;
    line-height: 1.08;
    color: #1d1d1f;
    margin: 0 0 0.5rem;
}

.hero-sub {
    font-size: clamp(0.95rem, 2vw, 1.15rem);
    color: #86868b;
    max-width: 520px;
    margin: 0 auto;
    line-height: 1.6;
}

/* Tool cards */
.tool-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    max-width: 1000px;
    margin: 0 auto;
    padding: 0 1rem;
}

.tool-card {
    background: rgba(255, 255, 255, 0.72);
    backdrop-filter: saturate(160%) blur(20px);
    -webkit-backdrop-filter: saturate(160%) blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.8);
    border-radius: 20px;
    padding: 32px 28px;
    text-align: center;
    transition: transform 0.25s cubic-bezier(0.25, 0.1, 0.25, 1),
                box-shadow 0.25s cubic-bezier(0.25, 0.1, 0.25, 1),
                border-color 0.25s;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03),
                0 6px 24px rgba(0,0,0,0.04);
    text-decoration: none;
    display: block;
    cursor: pointer;
}

.tool-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.08),
                0 2px 8px rgba(0,0,0,0.04);
    border-color: rgba(0, 102, 204, 0.2);
}

.tool-icon {
    font-size: 2.5rem;
    margin-bottom: 16px;
    display: block;
}

.tool-name {
    font-family: 'Inter', sans-serif;
    font-size: 1.2rem;
    font-weight: 700;
    color: #1d1d1f;
    letter-spacing: -0.02em;
    margin-bottom: 6px;
}

.tool-desc {
    font-size: 0.875rem;
    color: #86868b;
    line-height: 1.5;
    margin-bottom: 16px;
}

.tool-status {
    display: inline-block;
    padding: 4px 14px;
    font-size: 0.6875rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    border-radius: 980px;
}

.status-live {
    color: #34C759;
    background: rgba(52, 199, 89, 0.1);
}

.status-planned {
    color: #FF9500;
    background: rgba(255, 149, 0, 0.1);
}

.status-idea {
    color: #AF52DE;
    background: rgba(175, 82, 222, 0.1);
}

/* Divider */
.section-divider {
    max-width: 1000px;
    margin: 2.5rem auto 1.5rem;
    padding: 0 1rem;
}

.section-divider hr {
    border: none;
    border-top: 1px solid rgba(0,0,0,0.06);
}

.section-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #86868b;
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
}

/* Mission section */
.mission-container {
    max-width: 1000px;
    margin: 0 auto 3rem;
    padding: 0 1rem;
}

.mission-card {
    background: rgba(255, 255, 255, 0.72);
    backdrop-filter: saturate(160%) blur(20px);
    -webkit-backdrop-filter: saturate(160%) blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.8);
    border-radius: 20px;
    padding: 36px 32px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03),
                0 6px 24px rgba(0,0,0,0.04);
}

/* Footer */
.dash-footer {
    text-align: center;
    padding: 2rem 1rem 3rem;
    font-size: 0.8rem;
    color: #86868b;
}

/* Streamlit overrides */
.stExpander {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
}

div[data-testid="stExpander"] > details {
    border: none !important;
}

div[data-testid="stExpander"] > details > summary {
    padding: 0 !important;
}

/* Hide anchor links on headings inside mission */
.mission-card h1 a, .mission-card h2 a, .mission-card h3 a {
    display: none !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Hero ──
st.markdown(
    """
<div class="hero-container">
    <div class="hero-badge">Internal Tools</div>
    <h1 class="hero-title">O'Brien Immigration Law</h1>
    <p class="hero-sub">Staff toolkit for research, document assembly, and case preparation.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Tool definitions ──
tools = [
    {
        "icon": "&#x1F30D;",  # globe
        "name": "Country Reports",
        "desc": "Search indexed country condition reports, curate citations, and compile exhibit bundles.",
        "status": "live",
        "status_label": "Live",
        "url": "http://localhost:8501",
    },
    {
        "icon": "&#x2709;&#xFE0F;",  # envelope
        "name": "Cover Letters",
        "desc": "Generate and customize cover letters for filings and correspondence.",
        "status": "planned",
        "status_label": "Coming Soon",
        "url": None,
    },
    {
        "icon": "&#x1F4DC;",  # scroll
        "name": "Brief Builder",
        "desc": "Assemble legal briefs with templated sections, arguments, and citations.",
        "status": "planned",
        "status_label": "Coming Soon",
        "url": None,
    },
    {
        "icon": "&#x1F4CB;",  # clipboard
        "name": "Case Checklist",
        "desc": "Track filing requirements, deadlines, and document checklists per case type.",
        "status": "idea",
        "status_label": "Idea",
        "url": None,
    },
]

# ── Render tool cards ──
cards_html = '<div class="tool-grid">'
for tool in tools:
    status_class = f"status-{tool['status']}"
    if tool["url"]:
        cards_html += f"""
        <a href="{tool['url']}" target="_blank" class="tool-card" style="text-decoration:none;">
            <span class="tool-icon">{tool['icon']}</span>
            <div class="tool-name">{tool['name']}</div>
            <div class="tool-desc">{tool['desc']}</div>
            <span class="tool-status {status_class}">{tool['status_label']}</span>
        </a>"""
    else:
        cards_html += f"""
        <div class="tool-card" style="cursor:default;">
            <span class="tool-icon">{tool['icon']}</span>
            <div class="tool-name">{tool['name']}</div>
            <div class="tool-desc">{tool['desc']}</div>
            <span class="tool-status {status_class}">{tool['status_label']}</span>
        </div>"""
cards_html += "</div>"

st.markdown(cards_html, unsafe_allow_html=True)

# ── Mission & Goals section ──
st.markdown(
    """
<div class="section-divider"><hr></div>
<div class="mission-container">
    <p class="section-label">Mission &amp; Roadmap</p>
</div>
""",
    unsafe_allow_html=True,
)

# Editable mission doc
col_l, col_center, col_r = st.columns([1, 10, 1])
with col_center:
    if "editing_mission" not in st.session_state:
        st.session_state.editing_mission = False

    if st.session_state.editing_mission:
        mission_text = st.text_area(
            "Edit Mission Document",
            value=_load_mission(),
            height=500,
            key="mission_editor",
            label_visibility="collapsed",
        )
        c1, c2, _ = st.columns([1, 1, 6])
        with c1:
            if st.button("Save", type="primary"):
                MISSION_PATH.write_text(mission_text)
                st.session_state.editing_mission = False
                st.rerun()
        with c2:
            if st.button("Cancel"):
                st.session_state.editing_mission = False
                st.rerun()
    else:
        st.markdown(
            '<div class="mission-card">',
            unsafe_allow_html=True,
        )
        st.markdown(_load_mission())
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("Edit Mission Document", type="secondary"):
            st.session_state.editing_mission = True
            st.rerun()

# ── Footer ──
st.markdown(
    """
<div class="dash-footer">
    &copy; 2026 O'Brien Immigration Law &middot; Internal Use Only
</div>
""",
    unsafe_allow_html=True,
)
