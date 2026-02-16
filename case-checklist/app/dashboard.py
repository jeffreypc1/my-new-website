"""Streamlit dashboard for the Case Checklist tool.

Part of the O'Brien Immigration Law tool suite. Provides a UI for managing
immigration cases with pre-built checklists, deadline tracking, and
progress monitoring.

Flow:
1. Sidebar shows case type filter and status filter.
2. Main area lists active cases with progress bars.
3. Clicking a case shows its checklist with checkboxes.
4. Deadline tracking uses color coding (red = overdue, yellow = due soon, green = on track).
5. "New Case" button creates a case with an auto-populated checklist.
"""

from datetime import date, datetime, timedelta

import streamlit as st
import requests

API_BASE = "http://localhost:8000"

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Case Checklist",
    page_icon=None,
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

if "selected_case_id" not in st.session_state:
    st.session_state.selected_case_id = None
if "show_new_case_form" not in st.session_state:
    st.session_state.show_new_case_form = False

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
    .status-active {
        display: inline-block;
        background: #059669;
        color: #ffffff;
        padding: 2px 10px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-pending {
        display: inline-block;
        background: #d97706;
        color: #ffffff;
        padding: 2px 10px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-denied {
        display: inline-block;
        background: #dc2626;
        color: #ffffff;
        padding: 2px 10px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-approved {
        display: inline-block;
        background: #2563eb;
        color: #ffffff;
        padding: 2px 10px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .deadline-overdue {
        color: #dc2626;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .deadline-soon {
        color: #d97706;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .deadline-ok {
        color: #059669;
        font-size: 0.85rem;
    }
    .category-badge {
        display: inline-block;
        background: #e2e8f0;
        color: #334155;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        margin-right: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="main-header">Case Checklist</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">Track immigration case progress with pre-built checklists and deadline monitoring</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar: filters
# ---------------------------------------------------------------------------

st.sidebar.header("Filters")

# Case type filter
CASE_TYPES = ["All", "Asylum", "Family-Based", "VAWA"]
selected_case_type = st.sidebar.selectbox("Case Type", CASE_TYPES)

# Status filter
STATUSES = ["All", "Active", "Pending RFE", "Approved", "Denied"]
selected_status = st.sidebar.selectbox("Status", STATUSES)

# ---------------------------------------------------------------------------
# Sidebar: new case button
# ---------------------------------------------------------------------------

st.sidebar.markdown("---")

if st.sidebar.button("New Case", use_container_width=True):
    st.session_state.show_new_case_form = True

# New case form in sidebar
if st.session_state.show_new_case_form:
    st.sidebar.markdown("### Create New Case")
    new_case_id = st.sidebar.text_input(
        "Case ID",
        placeholder="e.g. GARCIA-2026-001",
    )
    new_client_name = st.sidebar.text_input(
        "Client Name",
        placeholder="e.g. Maria Garcia Lopez",
    )
    new_case_type = st.sidebar.selectbox(
        "Case Type",
        options=["Asylum", "Family-Based", "VAWA"],
        key="new_case_type",
    )
    new_a_number = st.sidebar.text_input(
        "A-Number",
        placeholder="e.g. A-123-456-789",
        key="new_a_number",
    )

    create_col, cancel_col = st.sidebar.columns(2)
    with create_col:
        if st.button("Create", use_container_width=True):
            if new_case_id and new_client_name:
                try:
                    resp = requests.post(
                        f"{API_BASE}/api/cases",
                        json={
                            "case_id": new_case_id,
                            "client_name": new_client_name,
                            "case_type": new_case_type,
                            "a_number": new_a_number,
                        },
                        timeout=30,
                    )
                    resp.raise_for_status()
                    st.session_state.show_new_case_form = False
                    st.session_state.selected_case_id = new_case_id
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Failed to create case: {e}")
            else:
                st.sidebar.warning("Case ID and Client Name are required.")
    with cancel_col:
        if st.button("Cancel", use_container_width=True):
            st.session_state.show_new_case_form = False
            st.rerun()

# ---------------------------------------------------------------------------
# Helper: status badge
# ---------------------------------------------------------------------------

def _status_badge(status: str) -> str:
    """Return HTML for a color-coded status badge."""
    css_class = {
        "Active": "status-active",
        "Pending RFE": "status-pending",
        "Denied": "status-denied",
        "Approved": "status-approved",
    }.get(status, "status-active")
    return f'<span class="{css_class}">{status}</span>'


def _deadline_label(deadline_date: str | None) -> str:
    """Return HTML for a color-coded deadline label."""
    if not deadline_date:
        return ""
    try:
        dl = datetime.strptime(deadline_date, "%Y-%m-%d").date()
    except ValueError:
        return ""
    today = date.today()
    days_remaining = (dl - today).days

    if days_remaining < 0:
        return f'<span class="deadline-overdue">OVERDUE ({abs(days_remaining)}d)</span>'
    elif days_remaining <= 30:
        return f'<span class="deadline-soon">Due in {days_remaining}d</span>'
    else:
        return f'<span class="deadline-ok">Due in {days_remaining}d</span>'


# ---------------------------------------------------------------------------
# Main area: case list and detail view
# ---------------------------------------------------------------------------

# Fetch cases from the API
cases: list[dict] = []
try:
    params = {}
    if selected_status != "All":
        params["status"] = selected_status
    if selected_case_type != "All":
        params["case_type"] = selected_case_type

    resp = requests.get(f"{API_BASE}/api/cases", params=params, timeout=10)
    resp.raise_for_status()
    cases = resp.json()
except Exception:
    pass

# Two-column layout: case list (left) | case detail (right)
list_col, detail_col = st.columns([2, 3])

with list_col:
    st.markdown("### Cases")

    if cases:
        for case in cases:
            case_id = case.get("case_id", "")
            client_name = case.get("client_name", "")
            case_type = case.get("case_type", "")
            status = case.get("status", "Active")
            completion = case.get("completion", {})
            pct = completion.get("pct", 0)

            st.markdown(
                f'{_status_badge(status)} **{client_name}** ({case_type})',
                unsafe_allow_html=True,
            )
            st.progress(pct / 100)
            st.caption(f"{pct}% complete | Case ID: {case_id}")

            if st.button("View", key=f"view_{case_id}"):
                st.session_state.selected_case_id = case_id
                st.rerun()

            st.markdown("---")
    else:
        st.info(
            "No cases found. Create a new case using the sidebar button."
        )

with detail_col:
    st.markdown("### Checklist")

    if st.session_state.selected_case_id:
        case_id = st.session_state.selected_case_id

        # Fetch case detail
        case_detail: dict | None = None
        try:
            # Load from the cases list or fetch individually
            case_detail = next(
                (c for c in cases if c.get("case_id") == case_id),
                None,
            )
            if case_detail is None:
                resp = requests.get(
                    f"{API_BASE}/api/cases/{case_id}/status",
                    timeout=10,
                )
                resp.raise_for_status()
                case_detail = resp.json()
        except Exception:
            pass

        if case_detail and "error" not in case_detail:
            st.markdown(
                f'**{case_detail.get("client_name", "")}** | '
                f'{_status_badge(case_detail.get("status", "Active"))}',
                unsafe_allow_html=True,
            )

            checklist = case_detail.get("checklist", [])

            # Group by category
            categories: dict[str, list] = {}
            for idx, item in enumerate(checklist):
                cat = item.get("category", "General")
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append((idx, item))

            for cat_name, cat_items in categories.items():
                st.markdown(
                    f'<span class="category-badge">{cat_name}</span>',
                    unsafe_allow_html=True,
                )

                for idx, item in cat_items:
                    label = item.get("label", "")
                    completed = item.get("completed", False)
                    required = item.get("required", True)
                    deadline_date = item.get("deadline_date")

                    col_check, col_label, col_deadline = st.columns([1, 4, 2])

                    with col_check:
                        new_val = st.checkbox(
                            f"item_{idx}",
                            value=completed,
                            key=f"check_{case_id}_{idx}",
                            label_visibility="collapsed",
                        )
                        # TODO: Send update to API when checkbox changes
                        if new_val != completed:
                            try:
                                requests.put(
                                    f"{API_BASE}/api/cases/{case_id}",
                                    json={
                                        "checklist_updates": [
                                            {"index": idx, "completed": new_val}
                                        ]
                                    },
                                    timeout=10,
                                )
                            except Exception:
                                pass

                    with col_label:
                        req_marker = " (required)" if required else ""
                        if completed:
                            st.markdown(f"~~{label}~~{req_marker}")
                        else:
                            st.markdown(f"{label}{req_marker}")

                    with col_deadline:
                        dl_html = _deadline_label(deadline_date)
                        if dl_html:
                            st.markdown(dl_html, unsafe_allow_html=True)

                st.markdown("")  # spacing between categories
        else:
            st.warning(f"Could not load case: {case_id}")
    else:
        st.caption("Select a case from the list to view its checklist.")
