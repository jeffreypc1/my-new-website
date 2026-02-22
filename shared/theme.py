"""Centralized CSS and navigation bar for all office tools.

Eliminates the ~50-line CSS block duplicated across 12+ dashboards.
Import `render_theme_css` and `render_nav_bar` instead of inlining.
"""

from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# Shared CSS
# ---------------------------------------------------------------------------

_BASE_CSS = """\
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Hide Streamlit chrome */
#MainMenu, footer,
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

/* Section labels */
.section-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: #5a6a85;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 4px;
    margin-top: 12px;
}

/* Boilerplate block */
.boilerplate-block {
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 0.84rem;
    line-height: 1.55;
    margin-bottom: 8px;
    color: #78630d;
}

/* Preview panel (shared base) */
.preview-panel {
    font-family: 'Times New Roman', Times, serif;
    font-size: 0.88rem;
    line-height: 1.8;
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 28px 32px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    max-height: 75vh;
    overflow-y: auto;
}

/* Brief preview sub-classes */
.preview-panel .brief-title {
    text-align: center;
    font-weight: bold;
    font-size: 1.05rem;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.preview-panel .brief-caption {
    text-align: center;
    font-size: 0.85rem;
    margin-bottom: 16px;
    line-height: 1.5;
}
.preview-panel .brief-heading {
    font-weight: bold;
    margin-top: 16px;
    margin-bottom: 4px;
}
.preview-panel .brief-subheading {
    font-weight: bold;
    font-style: italic;
    margin-top: 10px;
    margin-bottom: 4px;
    padding-left: 16px;
}
.preview-panel .brief-body {
    text-align: justify;
    margin-bottom: 8px;
    text-indent: 32px;
}
.preview-panel .brief-sig {
    margin-top: 28px;
    line-height: 2;
}

/* Letter preview sub-classes */
.preview-panel .letter-cert {
    margin-top: 28px;
    padding-top: 16px;
    border-top: 1px solid #ddd;
}
.preview-panel .conf-notice {
    background: #fff8f0;
    border: 1px solid #f0d0a0;
    border-radius: 4px;
    padding: 10px 14px;
    margin-bottom: 12px;
    font-size: 0.82rem;
    color: #8b4513;
    font-style: italic;
}

/* Draft badge */
.draft-badge {
    display: inline-block;
    padding: 3px 10px;
    font-size: 0.7rem;
    font-weight: 600;
    background: #e8f0fe;
    color: #1a73e8;
    border-radius: 12px;
    margin-bottom: 8px;
}

/* Saved confirmation */
.saved-toast {
    font-size: 0.8rem;
    color: #2e7d32;
    font-weight: 600;
}
"""


def render_theme_css(extra_css: str = "") -> None:
    """Inject the shared stylesheet. Pass *extra_css* for tool-specific rules."""
    css = _BASE_CSS
    if extra_css:
        css += "\n" + extra_css
    st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Navigation bar
# ---------------------------------------------------------------------------

def render_nav_bar(
    tool_title: str,
    firm_name: str = "O\u2019Brien Immigration Law",
) -> None:
    """Render the shared navigation bar with a back link and centered title."""
    import html as html_mod

    st.markdown(
        f'<div class="nav-bar">'
        f'    <a href="http://localhost:8502" class="nav-back">&#8592; Staff Dashboard</a>'
        f'    <div class="nav-title">{html_mod.escape(tool_title)}'
        f'<span class="nav-firm">&mdash; {html_mod.escape(firm_name)}</span></div>'
        f'    <div class="nav-spacer"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
