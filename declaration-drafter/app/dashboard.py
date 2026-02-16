"""Streamlit dashboard for the Declaration Drafter tool."""

from __future__ import annotations

import requests
import streamlit as st

from app.prompts import DECLARATION_PROMPTS, DECLARATION_TYPES, build_declaration_text

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Declaration Drafter",
    page_icon=None,
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS
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
    .section-header {
        color: #1a2744;
        font-size: 1.2rem;
        font-weight: 600;
        margin-top: 1rem;
        margin-bottom: 0.25rem;
    }
    .section-instructions {
        color: #5a6a85;
        font-size: 0.88rem;
        margin-bottom: 0.75rem;
    }
    .preview-block {
        font-family: 'Times New Roman', Times, serif;
        font-size: 0.92rem;
        line-height: 1.6;
        background: #fafbfc;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 16px 20px;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="main-header">Declaration Drafter</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">Guided declaration drafting for immigration cases '
    "&mdash; O'Brien Immigration Law</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "answers" not in st.session_state:
    st.session_state.answers: dict[str, str] = {}
if "preview_text" not in st.session_state:
    st.session_state.preview_text: str = ""

# ---------------------------------------------------------------------------
# Sidebar — declaration type & declarant info
# ---------------------------------------------------------------------------
st.sidebar.header("Declaration Setup")

declaration_type = st.sidebar.selectbox(
    "Declaration Type",
    options=DECLARATION_TYPES,
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.subheader("Declarant Information")

declarant_name = st.sidebar.text_input("Full Legal Name")
country_of_origin = st.sidebar.text_input("Country of Origin")
language = st.sidebar.selectbox(
    "Language",
    options=["English", "Spanish", "French", "Portuguese", "Arabic", "Mandarin", "Other"],
    index=0,
)
a_number = st.sidebar.text_input("A-Number (if any)", placeholder="e.g. 123-456-789")

# ---------------------------------------------------------------------------
# Main area — guided prompt sections
# ---------------------------------------------------------------------------
sections = DECLARATION_PROMPTS.get(declaration_type, [])
prompt_col, preview_col = st.columns([3, 2])

with prompt_col:
    st.markdown("### Guided Questions")

    if not sections:
        st.info("No prompts defined for this declaration type yet.")

    for sec_idx, section in enumerate(sections):
        st.markdown(
            f'<div class="section-header">{section["title"]}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="section-instructions">{section["instructions"]}</div>',
            unsafe_allow_html=True,
        )

        for q in section["questions"]:
            qid = q["id"]
            current_val = st.session_state.answers.get(qid, "")
            answer = st.text_area(
                q["label"],
                value=current_val,
                height=120,
                key=f"ta_{qid}",
            )
            # Persist into session state answers dict
            st.session_state.answers[qid] = answer

        if sec_idx < len(sections) - 1:
            st.divider()

# ---------------------------------------------------------------------------
# Preview column
# ---------------------------------------------------------------------------
with preview_col:
    st.markdown("### Preview")

    if declarant_name:
        preview = build_declaration_text(
            answers=st.session_state.answers,
            declaration_type=declaration_type,
            declarant_name=declarant_name,
        )
        st.session_state.preview_text = preview

        st.markdown(
            f'<div class="preview-block">{preview}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("Enter the declarant's name in the sidebar to see a live preview.")

    st.markdown("---")

    # --- Export controls ---
    st.markdown("### Export")

    if not declarant_name:
        st.warning("Enter the declarant's name before exporting.")
    else:
        # Plain-text download
        st.download_button(
            "Download as Plain Text (.txt)",
            data=st.session_state.preview_text,
            file_name=f"Declaration_{declarant_name.replace(' ', '_')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

        # Word document export via API
        if st.button("Export to Word (.docx)", use_container_width=True):
            with st.spinner("Generating Word document..."):
                try:
                    payload = {
                        "declaration_type": declaration_type,
                        "declarant": {
                            "name": declarant_name,
                            "country_of_origin": country_of_origin,
                            "language": language,
                            "a_number": a_number,
                        },
                        "answers": st.session_state.answers,
                    }
                    resp = requests.post(
                        f"{API_BASE}/api/export/docx",
                        json=payload,
                        timeout=30,
                    )
                    resp.raise_for_status()
                    safe_name = declarant_name.replace(" ", "_")
                    st.download_button(
                        "Download Word Document",
                        data=resp.content,
                        file_name=f"Declaration_{safe_name}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        key="download_docx",
                    )
                    st.success("Word document generated successfully.")
                except requests.ConnectionError:
                    st.error(
                        "Could not connect to the API backend. "
                        "Make sure uvicorn is running on port 8000."
                    )
                except Exception as e:
                    st.error(f"Export failed: {e}")

    # TODO: add interpreter certification section when language != English
    # TODO: add ability to save/load draft declarations
    # TODO: add support for multiple declarants (e.g. joint asylum applications)
