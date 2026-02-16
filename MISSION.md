# Law Office Technology Mission

## Vision
Build an internal suite of tools hosted on a Mac Mini that staff can access 24/7 to streamline the core tasks of our immigration law practice. Every tool should reduce manual work, improve accuracy, and keep client data in-house.

## Guiding Principles
- **Practical over perfect** — tools should solve real daily problems, not theoretical ones
- **Staff-friendly** — anyone in the office can use these without technical training
- **Data stays local** — all client data on our own hardware, not third-party cloud services
- **Incremental** — build one tool at a time, get it working, then move to the next

## Tools

### 1. Country Reports Assembler (Complete)
Search indexed country condition reports, curate excerpts with page-level citations, compile exhibit bundles with Bates numbering, export Google Docs briefs.
- **Status:** Working — FastAPI + Streamlit, 14 countries indexed
- **Location:** `/Users/jeff/my-new-website/country-reports-tool/`

### 2. Cover Letter Generator (Planned)
_[Define: What types of cover letters? What inputs does staff provide? Are there standard templates? What gets customized per case?]_

### 3. Brief Builder (Planned)
_[Define: What types of briefs? Asylum merits briefs? Motions? What's the current manual workflow? What parts are repetitive and could be templated or assisted?]_

### 4. [Future Tool]
_[Add tools as needs arise]_

## Infrastructure

### Current Setup
- **Development machine:** Jeff's MacBook Pro
- **Target deployment:** Mac Mini on office network
- **Stack:** Python 3.13, FastAPI, Streamlit, uv
- **Access:** Staff connect via browser at `http://[mac-mini]:8501`

### Deployment TODO
- [ ] Set up Mac Mini with Python 3.13 + uv
- [ ] Configure FastAPI + Streamlit as launchd services (auto-start on boot)
- [ ] Add basic authentication (password protection for the dashboard)
- [ ] Set up local network access (static IP or hostname for the Mac Mini)
- [ ] Backup strategy for data directory

## Open Questions
- What cover letter types are most common and most time-consuming?
- What brief types would benefit most from tooling?
- Should tools share data (e.g., country reports feeding into briefs)?
- Do we need user accounts, or is a single shared password sufficient?
- What other repetitive tasks eat up staff time?

---

_Last updated: February 15, 2026_
