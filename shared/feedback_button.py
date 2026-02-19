"""Floating feedback button for all tool dashboards.

Renders a fixed-position "Feedback" button in the top-right corner of every
page. When clicked, opens a dialog where the user can capture/upload a
screenshot and describe what needs to be fixed. Feedback (screenshot +
description) is saved to data/feedback/ for review.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

FEEDBACK_DIR = Path(__file__).resolve().parent.parent / "data" / "feedback"


def _save_feedback(
    tool_name: str,
    description: str,
    screenshot_bytes: bytes | None = None,
) -> str:
    """Save feedback to disk. Returns the feedback ID."""
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    feedback_id = f"{tool_name}_{ts}"

    if screenshot_bytes:
        img_path = FEEDBACK_DIR / f"{feedback_id}.png"
        img_path.write_bytes(screenshot_bytes)

    meta = {
        "id": feedback_id,
        "tool": tool_name,
        "timestamp": datetime.now().isoformat(),
        "description": description,
        "has_screenshot": screenshot_bytes is not None,
    }
    meta_path = FEEDBACK_DIR / f"{feedback_id}.json"
    meta_path.write_text(json.dumps(meta, indent=2))

    return feedback_id


@st.dialog("Page Feedback", width="large")
def _show_feedback_dialog(tool_name: str):
    """Dialog for submitting page feedback with screenshot."""

    st.caption(
        "Capture the current page or upload a screenshot, then describe "
        "what needs to be fixed."
    )

    # html2canvas capture button
    components.html(
        """
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <div style="display:flex; align-items:center; gap:10px; font-family:Inter,sans-serif;">
            <button id="captureBtn" style="
                background:#1a2744; color:white; border:none; border-radius:6px;
                padding:8px 16px; font-size:13px; font-weight:600; cursor:pointer;
                font-family:Inter,sans-serif; display:flex; align-items:center; gap:6px;
            ">&#128247; Capture Page Screenshot</button>
            <span id="captureStatus" style="font-size:12px; color:#666;"></span>
        </div>
        <script>
        document.getElementById('captureBtn').addEventListener('click', function() {
            var status = document.getElementById('captureStatus');
            status.textContent = 'Capturing...';
            this.disabled = true;
            var mainEl = window.parent.document.querySelector('[data-testid="stAppViewBlockContainer"]')
                      || window.parent.document.querySelector('[data-testid="stMainBlockContainer"]')
                      || window.parent.document.querySelector('.main')
                      || window.parent.document.body;
            html2canvas(mainEl, {
                useCORS: true,
                allowTaint: true,
                scale: 1,
                logging: false,
                ignoreElements: function(el) {
                    return el.getAttribute && el.getAttribute('role') === 'dialog';
                }
            }).then(function(canvas) {
                var link = document.createElement('a');
                var ts = new Date().toISOString().slice(0,19).replace(/[T:]/g, '-');
                link.download = 'feedback_' + ts + '.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
                status.textContent = 'Saved to Downloads! Upload it below.';
                document.getElementById('captureBtn').disabled = false;
            }).catch(function(err) {
                status.textContent = 'Capture failed — use Cmd+Shift+4 instead.';
                document.getElementById('captureBtn').disabled = false;
            });
        });
        </script>
        """,
        height=50,
    )

    st.markdown("---")

    # File uploader for the screenshot
    uploaded = st.file_uploader(
        "Upload screenshot",
        type=["png", "jpg", "jpeg"],
        key=f"_feedback_upload_{tool_name}",
        help="Upload the captured screenshot or any other image",
    )

    if uploaded:
        st.image(uploaded, caption="Attached screenshot", use_container_width=True)

    # Description
    description = st.text_area(
        "What needs to be fixed or adjusted?",
        key=f"_feedback_desc_{tool_name}",
        height=150,
        placeholder="Describe what you see and what should change...",
    )

    if st.button(
        "Submit Feedback",
        type="primary",
        use_container_width=True,
        key=f"_feedback_submit_{tool_name}",
    ):
        if not description.strip():
            st.warning("Please add a description of what needs to be fixed.")
        else:
            screenshot_bytes = uploaded.getvalue() if uploaded else None
            feedback_id = _save_feedback(tool_name, description.strip(), screenshot_bytes)
            st.success(f"Feedback saved ({feedback_id})")


# ── CSS to hide the real Streamlit button + fixed-position HTML button ────────


def render_feedback_button(tool_name: str) -> None:
    """Render a fixed-position feedback button in the top-right corner.

    Call this once per page, typically right after render_client_banner()
    and render_tool_help().  If render_tool_help() already rendered the
    feedback button inline, this is a no-op.
    """
    # Skip if already rendered side-by-side by render_tool_help()
    if st.session_state.get(f"_feedback_rendered_{tool_name}"):
        return

    # Hidden Streamlit button that triggers the dialog
    _c = st.container()
    with _c:
        st.markdown(
            "<style>div[data-testid='stVerticalBlock']:has(> div > div > button"
            f"[key='_feedback_btn_{tool_name}']) {{ height: 0; overflow: hidden; "
            "margin: 0; padding: 0; }}</style>",
            unsafe_allow_html=True,
        )
        if st.button("\U0001f4f8 Feedback", key=f"_feedback_btn_{tool_name}"):
            _show_feedback_dialog(tool_name)

    # Fixed-position HTML button that clicks the hidden Streamlit button
    components.html(
        f"""
        <style>
        .fb-float-wrap {{
            position: fixed;
            top: 14px;
            right: 20px;
            z-index: 999990;
        }}
        .fb-float-btn {{
            background: #1a2744;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 7px 14px;
            font-size: 0.78rem;
            font-weight: 600;
            cursor: pointer;
            font-family: 'Inter', sans-serif;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 5px;
            transition: background 0.15s;
        }}
        .fb-float-btn:hover {{
            background: #2a3a5c;
        }}
        </style>
        <div class="fb-float-wrap">
            <button class="fb-float-btn" onclick="
                var btns = window.parent.document.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {{
                    if (btns[i].textContent.indexOf('Feedback') !== -1) {{
                        btns[i].click();
                        break;
                    }}
                }}
            ">&#128248; Feedback</button>
        </div>
        """,
        height=0,
    )

    # Re-open dialog if flagged
    if st.session_state.pop(f"_feedback_open_{tool_name}", False):
        _show_feedback_dialog(tool_name)
