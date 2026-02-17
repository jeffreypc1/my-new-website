"""O'Brien Immigration Law — Staff Tools Dashboard."""

import html as html_mod
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_sf_available = True
try:
    from shared.salesforce_client import get_client, load_active_client, save_active_client
except Exception:
    _sf_available = False
    import json as _json
    _FB = Path(__file__).resolve().parent.parent / "data" / "active_client.json"
    def load_active_client():
        try: return _json.loads(_FB.read_text()) if _FB.exists() else None
        except Exception: return None
    def save_active_client(r): pass
    def get_client(c): return None

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

/* Client lookup bar */
.client-bar {
    max-width: 1000px;
    margin: 0 auto 2rem;
    padding: 0 1rem;
}

.client-card {
    background: rgba(255, 255, 255, 0.72);
    backdrop-filter: saturate(160%) blur(20px);
    -webkit-backdrop-filter: saturate(160%) blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.8);
    border-radius: 16px;
    padding: 20px 28px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03),
                0 6px 24px rgba(0,0,0,0.04);
}

.client-info {
    display: flex;
    flex-wrap: wrap;
    gap: 16px 32px;
    margin-top: 8px;
}

.client-field {
    font-size: 0.82rem;
    color: #86868b;
}

.client-field strong {
    color: #1d1d1f;
    font-weight: 600;
}

.client-name-big {
    font-family: 'Inter', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: #1d1d1f;
    margin: 4px 0 0;
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

# ── Load active client from shared file on startup ──
_saved_client = load_active_client()
if _saved_client and not st.session_state.get("sf_client"):
    st.session_state.sf_client = _saved_client
    st.session_state.sf_customer_id = _saved_client.get("Customer_ID__c", "")

# ── Hero ──
st.markdown(
    """
<div class="hero-container">
    <div class="hero-badge">Internal Tools</div>
    <h1 class="hero-title">O'Brien Immigration Law</h1>
    <p class="hero-sub">Staff toolkit for research, document assembly, and case preparation.</p>
    <p class="hero-sub" style="margin-top:0.5rem;font-size:0.85rem;">All tools export to <strong style="color:#1d1d1f;">.txt</strong>, <strong style="color:#1d1d1f;">.docx</strong>, and <strong style="color:#1d1d1f;">Google Docs</strong></p>
</div>
""",
    unsafe_allow_html=True,
)

# ── Client lookup ──
_cl_left, _cl_center, _cl_right = st.columns([1, 8, 1])
with _cl_center:
    cl_cols = st.columns([3, 2, 2])
    with cl_cols[0]:
        customer_id = st.text_input(
            "Client #",
            key="inp_customer_id",
            placeholder="Enter client number",
            label_visibility="collapsed",
        )
    with cl_cols[1]:
        sf_pull = st.button("Pull from Salesforce", use_container_width=True, type="primary",
                            disabled=not _sf_available)
    with cl_cols[2]:
        _cid = st.session_state.get("sf_customer_id", "")
        if _cid:
            st.link_button(
                "Edit Client Info",
                url=f"http://localhost:8512?client_id={_cid}",
                use_container_width=True,
            )

    if sf_pull and customer_id and _sf_available:
        try:
            record = get_client(customer_id.strip())
            if record:
                st.session_state.sf_client = record
                st.session_state.sf_customer_id = customer_id.strip()
                save_active_client(record)
                st.rerun()
            else:
                st.warning(f"No client found for #{customer_id}")
        except Exception as e:
            st.error(f"Salesforce error: {e}")

    if st.session_state.get("sf_client"):
        sf = st.session_state.sf_client
        fields_html = []
        if sf.get("A_Number__c"):
            fields_html.append(f'<span class="client-field"><strong>A#:</strong> {html_mod.escape(str(sf["A_Number__c"]))}</span>')
        if sf.get("Country__c"):
            fields_html.append(f'<span class="client-field"><strong>Country:</strong> {html_mod.escape(str(sf["Country__c"]))}</span>')
        if sf.get("Best_Language__c"):
            fields_html.append(f'<span class="client-field"><strong>Language:</strong> {html_mod.escape(str(sf["Best_Language__c"]))}</span>')
        if sf.get("Birthdate"):
            fields_html.append(f'<span class="client-field"><strong>DOB:</strong> {html_mod.escape(str(sf["Birthdate"]))}</span>')
        if sf.get("Immigration_Status__c"):
            fields_html.append(f'<span class="client-field"><strong>Status:</strong> {html_mod.escape(str(sf["Immigration_Status__c"]))}</span>')
        if sf.get("MobilePhone"):
            fields_html.append(f'<span class="client-field"><strong>Phone:</strong> {html_mod.escape(str(sf["MobilePhone"]))}</span>')
        if sf.get("Email"):
            fields_html.append(f'<span class="client-field"><strong>Email:</strong> {html_mod.escape(str(sf["Email"]))}</span>')

        card_html = f"""
        <div class="client-bar"><div class="client-card">
            <div class="client-name-big">{html_mod.escape(sf.get("Name", ""))}</div>
            <div class="client-info">{"".join(fields_html)}</div>
        </div></div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

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
        "status": "live",
        "status_label": "Live",
        "url": "http://localhost:8504",
    },
    {
        "icon": "&#x1F4DC;",  # scroll
        "name": "Brief Builder",
        "desc": "Assemble legal briefs with templated sections, arguments, and citations.",
        "status": "live",
        "status_label": "Live",
        "url": "http://localhost:8507",
    },
    {
        "icon": "&#x1F58A;&#xFE0F;",  # pen
        "name": "Declaration Drafter",
        "desc": "Guided templates for asylum declarations, personal statements, and witness affidavits.",
        "status": "live",
        "status_label": "Live",
        "url": "http://localhost:8503",
    },
    {
        "icon": "&#x1F4C5;",  # calendar
        "name": "Timeline Builder",
        "desc": "Build visual chronologies of persecution events, travel history, and case milestones.",
        "status": "live",
        "status_label": "Live",
        "url": "http://localhost:8505",
    },
    {
        "icon": "&#x2696;&#xFE0F;",  # scales of justice
        "name": "Legal Research",
        "desc": "Search case law, BIA decisions, and circuit court opinions for relevant precedent.",
        "status": "live",
        "status_label": "Live",
        "url": "http://localhost:8508",
    },
    {
        "icon": "&#x1F4DD;",  # memo
        "name": "Forms Assistant",
        "desc": "Prepare and review I-589, I-130, I-485, and other immigration forms.",
        "status": "live",
        "status_label": "Live",
        "url": "http://localhost:8509",
    },
    {
        "icon": "&#x1F4CB;",  # clipboard
        "name": "Case Checklist",
        "desc": "Track filing requirements, deadlines, and document checklists per case type.",
        "status": "live",
        "status_label": "Live",
        "url": "http://localhost:8506",
    },
    {
        "icon": "&#x1F5C2;&#xFE0F;",  # file folder dividers
        "name": "Evidence Indexer",
        "desc": "Organize and label supporting documents with auto-generated exhibit lists.",
        "status": "live",
        "status_label": "Live",
        "url": "http://localhost:8510",
    },
    {
        "icon": "&#x1F310;",  # globe with meridians
        "name": "Document Translator",
        "desc": "Upload documents in any language, auto-translate to English, and export to Google Docs.",
        "status": "live",
        "status_label": "Live",
        "url": "http://localhost:8511",
    },
    {
        "icon": "&#x1F464;",  # bust silhouette
        "name": "Client Info",
        "desc": "View and edit Salesforce contact data. Pull client details and push updates back.",
        "status": "live",
        "status_label": "Live",
        "url": "http://localhost:8512",
    },
    {
        "icon": "&#x2699;&#xFE0F;",  # gear
        "name": "Admin Panel",
        "desc": "Configure tool settings, templates, and lists.",
        "status": "live",
        "status_label": "Live",
        "url": "http://localhost:8513",
        "no_client_param": True,
    },
]

# ── Render tool cards ──
_active_cid = st.session_state.get("sf_customer_id", "")

cards_html = '<div class="tool-grid">'
for tool in tools:
    status_class = f"status-{tool['status']}"
    url = tool["url"]
    if url and _active_cid and not tool.get("no_client_param"):
        url = f"{url}?client_id={_active_cid}"
    if url:
        cards_html += f"""
        <a href="{url}" target="_blank" class="tool-card" style="text-decoration:none;">
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
