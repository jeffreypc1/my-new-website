"""Streamlit dashboard for the Forms Assistant tool.

Part of the O'Brien Immigration Law tool suite. Provides a multi-step form
wizard for completing USCIS immigration forms with field validation,
progress tracking, and export functionality.

Flow:
1. User selects a form from the sidebar (I-589, I-130, I-485, etc.).
2. The main area displays the form sections as a step-by-step wizard.
3. Fields include validation with helpful error messages.
4. Progress indicator shows completion percentage.
5. Export/print button generates the completed form data.
"""

import streamlit as st
import requests

API_BASE = "http://localhost:8000"

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Forms Assistant",
    page_icon=None,
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

if "form_data" not in st.session_state:
    st.session_state.form_data = {}  # field_name -> value
if "current_section" not in st.session_state:
    st.session_state.current_section = 0
if "validation_errors" not in st.session_state:
    st.session_state.validation_errors = {}

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
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a2744;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .form-meta {
        font-size: 0.85rem;
        color: #5a6a85;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="main-header">Forms Assistant</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">Complete USCIS immigration forms with guided assistance and validation</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar: form selector
# ---------------------------------------------------------------------------

st.sidebar.header("Select Form")

# Fetch available forms from the API
forms: list[dict] = []
try:
    resp = requests.get(f"{API_BASE}/api/forms", timeout=10)
    resp.raise_for_status()
    forms = resp.json()
except Exception:
    st.sidebar.warning(
        "Could not connect to API. Is the backend running on port 8000?"
    )

# Form selector with names
FORM_OPTIONS = {
    "I-589": "I-589 Asylum Application",
    "I-130": "I-130 Family Petition",
    "I-485": "I-485 Adjustment of Status",
    "I-765": "I-765 Employment Authorization",
    "I-131": "I-131 Travel Document",
    "I-290B": "I-290B Appeal/Motion",
    "I-360": "I-360 VAWA Self-Petition",
}

selected_form = st.sidebar.selectbox(
    "Form",
    options=list(FORM_OPTIONS.keys()),
    format_func=lambda x: FORM_OPTIONS.get(x, x),
)

# Display form metadata in sidebar
form_meta = next((f for f in forms if f.get("form_id") == selected_form), None)
if form_meta:
    st.sidebar.markdown(f'<div class="form-meta">**Filing Fee:** {form_meta["filing_fee"]}</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f'<div class="form-meta">**Processing:** {form_meta["processing_time"]}</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f'<div class="form-meta">**Agency:** {form_meta["agency"]}</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar: progress indicator
# ---------------------------------------------------------------------------

st.sidebar.markdown("---")
st.sidebar.header("Progress")

# Calculate completion from form_data
total_fields = len(st.session_state.form_data)
filled_fields = sum(1 for v in st.session_state.form_data.values() if v)
completion_pct = round((filled_fields / total_fields) * 100) if total_fields > 0 else 0

st.sidebar.progress(completion_pct / 100)
st.sidebar.caption(f"{completion_pct}% complete ({filled_fields}/{total_fields} fields)")

# ---------------------------------------------------------------------------
# Sidebar: export button
# ---------------------------------------------------------------------------

st.sidebar.markdown("---")
if st.sidebar.button("Validate Form", use_container_width=True):
    try:
        resp = requests.post(
            f"{API_BASE}/api/forms/{selected_form}/validate",
            json={"data": st.session_state.form_data},
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()
        completeness = result.get("completeness", {})
        field_errors = result.get("field_errors", {})

        if field_errors:
            st.session_state.validation_errors = field_errors
            st.sidebar.error(f"{len(field_errors)} field(s) have errors")
        else:
            st.session_state.validation_errors = {}
            st.sidebar.success("All fields valid!")

        missing = completeness.get("required_missing", [])
        if missing:
            st.sidebar.warning(f"{len(missing)} required field(s) missing")

    except Exception as e:
        st.sidebar.error(f"Validation failed: {e}")

if st.sidebar.button("Export Form Data", use_container_width=True):
    try:
        resp = requests.post(
            f"{API_BASE}/api/forms/{selected_form}/export",
            json={"data": st.session_state.form_data, "format": "json"},
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()

        import json
        export_json = json.dumps(result, indent=2)
        st.sidebar.download_button(
            "Download JSON",
            data=export_json,
            file_name=f"{selected_form}_data.json",
            mime="application/json",
            use_container_width=True,
        )
    except Exception as e:
        st.sidebar.error(f"Export failed: {e}")

# ---------------------------------------------------------------------------
# Main area: form fields
# ---------------------------------------------------------------------------

# Fetch field definitions for the selected form
fields_data: dict = {}
try:
    resp = requests.get(
        f"{API_BASE}/api/forms/{selected_form}/fields",
        timeout=10,
    )
    resp.raise_for_status()
    fields_data = resp.json()
except Exception:
    pass

sections = fields_data.get("sections", {})

if sections:
    section_names = list(sections.keys())

    # Section navigation tabs
    if section_names:
        selected_section = st.radio(
            "Section",
            section_names,
            horizontal=True,
            index=min(st.session_state.current_section, len(section_names) - 1),
        )
        st.session_state.current_section = section_names.index(selected_section)

        st.markdown(
            f'<div class="section-header">{selected_section}</div>',
            unsafe_allow_html=True,
        )

        fields = sections.get(selected_section, [])

        if fields:
            for field_def in fields:
                field_name = field_def["name"]
                field_type = field_def["field_type"]
                required = field_def.get("required", False)
                help_text = field_def.get("help_text", "")
                options = field_def.get("options", [])

                label = field_name.replace("_", " ").title()
                if required:
                    label += " *"

                # Show validation errors if any
                errors = st.session_state.validation_errors.get(field_name, [])

                current_value = st.session_state.form_data.get(field_name, "")

                if field_type == "select" and options:
                    idx = options.index(current_value) if current_value in options else 0
                    value = st.selectbox(
                        label,
                        options=[""] + options,
                        index=0 if not current_value else options.index(current_value) + 1,
                        help=help_text,
                        key=f"field_{field_name}",
                    )
                elif field_type == "textarea":
                    value = st.text_area(
                        label,
                        value=current_value,
                        help=help_text,
                        key=f"field_{field_name}",
                        height=120,
                    )
                elif field_type == "checkbox":
                    value = st.checkbox(
                        label,
                        value=bool(current_value),
                        help=help_text,
                        key=f"field_{field_name}",
                    )
                    value = "Yes" if value else ""
                elif field_type == "date":
                    value = st.text_input(
                        label,
                        value=current_value,
                        help=help_text,
                        placeholder="mm/dd/yyyy",
                        key=f"field_{field_name}",
                    )
                else:
                    value = st.text_input(
                        label,
                        value=current_value,
                        help=help_text,
                        key=f"field_{field_name}",
                    )

                st.session_state.form_data[field_name] = value

                if errors:
                    for err in errors:
                        st.error(err)
        else:
            st.info(
                "Detailed field definitions are not yet available for this section. "
                "Coming soon."
            )

        # Navigation buttons
        st.markdown("---")
        nav_left, nav_right = st.columns(2)
        with nav_left:
            if st.session_state.current_section > 0:
                if st.button("Previous Section"):
                    st.session_state.current_section -= 1
                    st.rerun()
        with nav_right:
            if st.session_state.current_section < len(section_names) - 1:
                if st.button("Next Section"):
                    st.session_state.current_section += 1
                    st.rerun()
else:
    st.info(
        "Select a form from the sidebar to begin. "
        "Field definitions will load automatically."
    )
