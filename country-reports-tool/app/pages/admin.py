"""Admin page for managing citation templates."""

import streamlit as st
import requests

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="Admin - Citation Template", layout="wide")

st.header("Citation Template Editor")

# Load current template
try:
    resp = requests.get(f"{API_BASE}/api/citation-template", timeout=5)
    resp.raise_for_status()
    current = resp.json()
except Exception:
    current = {
        "template": '"{snippet}" - Source: {source}, Country: {country}',
        "max_snippet_length": 300,
    }
    st.warning("Could not load template from API. Showing defaults.")

# --- Placeholder reference ---
st.markdown("**Available placeholders:**")
st.markdown(
    """
| Placeholder | Description |
|---|---|
| `{snippet}` | Truncated excerpt text (required) |
| `{source}` | Source PDF filename |
| `{country}` | Country name |
| `{chunk_index}` | Chunk sequence number |
"""
)

# --- Template editor ---
template = st.text_area(
    "Citation template",
    value=current["template"],
    height=100,
    help="Must contain {snippet}. Other placeholders: {source}, {country}, {chunk_index}",
)

max_snippet_length = st.number_input(
    "Max snippet length (characters)",
    min_value=50,
    max_value=2000,
    value=current["max_snippet_length"],
    step=50,
)

# --- Live preview ---
st.subheader("Preview")
sample_text = (
    "The government of El Salvador has been unable to control gang violence in urban areas, "
    "leading to widespread displacement of families seeking safety in neighboring countries."
)
sample_snippet = sample_text[:max_snippet_length]
if len(sample_text) > max_snippet_length:
    sample_snippet += "..."

try:
    preview = template.format(
        snippet=sample_snippet,
        source="ElSalvador_DOS_2023.pdf",
        country="El Salvador",
        chunk_index=12,
    )
    st.code(preview, language=None)
except (KeyError, IndexError, ValueError) as e:
    st.error(f"Template error: {e}")

# --- Save ---
if st.button("Save Template"):
    if "{snippet}" not in template:
        st.error("Template must contain the {snippet} placeholder.")
    else:
        try:
            save_resp = requests.post(
                f"{API_BASE}/api/citation-template",
                json={"template": template, "max_snippet_length": max_snippet_length},
                timeout=5,
            )
            save_resp.raise_for_status()
            result = save_resp.json()
            if "error" in result:
                st.error(result["error"])
            else:
                st.success("Template saved.")
        except Exception as e:
            st.error(f"Save failed: {e}")
