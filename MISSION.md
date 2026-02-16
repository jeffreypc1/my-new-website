# Law Office Technology Mission

## Vision
Build an internal suite of tools hosted on a Mac Mini that staff can access 24/7 to streamline the core tasks of our immigration law practice. Every tool should reduce manual work, improve accuracy, and keep client data in-house.

## Guiding Principles
- **Practical over perfect** — tools should solve real daily problems, not theoretical ones
- **Staff-friendly** — anyone in the office can use these without technical training
- **Data stays local** — all client data on our own hardware, not third-party cloud services
- **Incremental** — build one tool at a time, get it working, then move to the next
- **Shared infrastructure** — tools share Box (client files) and Google Workspace (document creation) integrations

## Tools

### 1. Country Reports Assembler (Complete)
Search indexed country condition reports, curate excerpts with page-level citations, compile exhibit bundles with Bates numbering, export Google Docs briefs.
- **Status:** Working — FastAPI + Streamlit, 14 countries indexed
- **Location:** `country-reports-tool/`
- **Repo:** jeffreypc1/country-reports-tool

### 2. Cover Letter Generator (Planned)
Generate professional cover letters that accompany every filing submitted to USCIS, Immigration Court, or the BIA.

**What it does:**
- Staff selects case type and filing type, fills in case details
- Tool generates a formatted cover letter listing all enclosed documents
- Exports to Google Docs / Word for final review and signature

**Typical cover letter includes:**
- Attorney/firm letterhead and contact info
- Filing office address (USCIS Service Center, Immigration Court, BIA)
- RE line: client name, A-number, receipt number
- Purpose of filing (initial application, response to RFE, motion, etc.)
- Itemized list of enclosed forms and supporting documents
- Attorney signature block

**Case types:** Asylum (I-589), Family-Based (I-130/I-485), Employment-Based, VAWA (I-360), U-Visa (I-918), T-Visa (I-914), Removal Defense, Appeals (I-290B), Motions to Reopen/Reconsider

- **Location:** `cover-letters/`

### 3. Brief Builder (Planned)
Assemble legal briefs and memoranda with templated sections, standard legal arguments, and integrated citations.

**What it does:**
- Attorney selects brief type, fills in case-specific facts
- Tool provides standard legal framework with boilerplate for each section
- Integrates with Country Reports for country conditions citations
- Exports formatted brief to Google Docs / Word

**Brief types:**
- **Asylum Merits Brief** — Statement of Facts, Legal Standard (INA §208, 8 USC §1158), Argument (past persecution, well-founded fear, nexus, PSG definition), Country Conditions, Conclusion
- **Motion to Reopen** — Procedural history, changed country conditions or new evidence, legal standard (INA §240(c)(7))
- **Appeal Brief (BIA)** — Issues on appeal, standard of review, argument, relief requested
- **Bond Brief** — Not a flight risk, not a danger, community ties, equities
- **Cancellation of Removal** — 10 years continuous presence, good moral character, exceptional and extremely unusual hardship

**Key legal references:**
- Matter of Acosta (PSG definition), Matter of Mogharrabi (well-founded fear standard)
- INS v. Cardoza-Fonseca (asylum vs. withholding standard)
- Matter of A-B- (PSG/domestic violence), Matter of L-E-A- (family as PSG)
- Matter of M-E-V-G- (immutability, particularity, social distinction)

- **Location:** `brief-builder/`

### 4. Declaration Drafter (Planned)
Guide attorneys and clients through writing asylum declarations, witness statements, and expert affidavits with structured prompts.

**What it does:**
- Step-by-step guided interview covering all required topics for asylum
- Prompts ensure nothing critical is missed (nexus, specific incidents, dates, harm feared)
- Assembles answers into numbered paragraphs in proper declaration format
- Includes penalty of perjury clause and signature block
- Exports to Google Docs / Word

**Declaration types:**
- **Asylum Declaration (I-589 Supplement)** — the client's personal statement
- **Witness Declaration** — corroborating statements from family, friends, experts
- **Expert Declaration** — country conditions expert, medical/psychological professional
- **Personal Statement** — for non-asylum cases (VAWA, U-Visa, cancellation)

**Guided sections for asylum declaration:**
1. Background — birth, nationality, ethnicity, religion, family, education, occupation
2. Particular Social Group / Protected Ground — what group, why targeted
3. Persecution History — each incident chronologically (who, what, when, where, why)
4. Reporting to Authorities — did you seek help? What happened?
5. Harm Feared on Return — what specifically would happen if deported
6. Internal Relocation — why can't you move elsewhere in your country
7. Departure and Arrival — how and when you left, route to US, one-year filing deadline
8. Life in the US — what you've been doing, community ties, hardship if removed

- **Location:** `declaration-drafter/`

### 5. Timeline Builder (Planned)
Create visual chronologies for asylum cases showing persecution events, travel, legal milestones, and case history.

**What it does:**
- Add events with dates (exact or approximate), descriptions, and categories
- Displays as a visual timeline with color-coded event types
- Exports to Word (formatted table) or PDF (visual graphic)
- Useful for interview prep, hearing prep, and brief exhibits

**Event categories:**
- Persecution (red) — incidents of harm, threats, discrimination
- Travel (blue) — departure, transit countries, arrival in US
- Legal Filing (green) — applications filed, RFEs, hearings, decisions
- Personal (gray) — marriage, children, employment, education
- Medical (purple) — injuries, treatment, psychological evaluations

**Date handling:** Supports approximate dates common in asylum cases — "March 2019", "Summer 2017", "Late 2018", "2015", "Between 2016 and 2018"

- **Location:** `timeline-builder/`

### 6. Legal Research (Planned)
Search and organize immigration case law, BIA decisions, and circuit court opinions.

**What it does:**
- Search indexed immigration decisions by topic, holding, or keyword
- Browse by legal topic (asylum grounds, credibility, procedural issues)
- Save relevant decisions to case-specific collections
- Format citations in proper legal style
- Could integrate with brief builder for citation insertion

**Key sources to index:**
- BIA published and unpublished decisions
- Circuit court immigration opinions (especially 9th Circuit for California practice)
- Supreme Court immigration cases
- USCIS policy memos and guidance

**Priority legal topics:**
- Particular Social Group definition and analysis
- Credibility determinations
- One-year filing deadline exceptions
- Changed country conditions
- Firm resettlement
- Withholding of removal standard
- Convention Against Torture (CAT) standard
- Discretionary factors

- **Location:** `legal-research/`

### 7. Forms Assistant (Complete)
Guided form preparation with field validation, completeness checks, PDF form filling, and preparer management.

- **Status:** Working — Streamlit on port 8509, 7 hardcoded forms + PDF upload
- **Location:** `forms-assistant/`

**What it does:**
- Multi-step wizard matching the actual form layout
- Field-level help text explaining what each question is asking
- Validation (required fields, format checks, consistency)
- Progress indicator showing completion percentage
- Upload actual USCIS PDF forms → auto-extract fillable fields → fill and export completed PDFs
- Office preparer management — tag fields with preparer roles, select a preparer to auto-fill
- Exports: .txt, .docx, Google Docs, and filled PDF (for uploaded forms)
- Draft save/load/delete with client name derivation

**Hardcoded forms (7):**
- **I-589** — Application for Asylum and Withholding of Removal (71 fields across 6 sections)
- **I-130** — Petition for Alien Relative
- **I-485** — Application to Register Permanent Residence (Adjustment of Status)
- **I-765** — Application for Employment Authorization
- **I-131** — Application for Travel Document
- **I-360** — Petition for Amerasian, Widow(er), or Special Immigrant (VAWA)
- **I-290B** — Notice of Appeal or Motion

**PDF upload workflow:**
1. Admin uploads a fillable USCIS PDF in Admin Panel → Forms Assistant tab → Upload PDF
2. System extracts all AcroForm widgets (text, checkbox, select, combo) with auto-derived labels
3. Admin edits field labels, assigns sections, tags preparer roles, sets required flags
4. Staff selects the uploaded form in Forms Assistant, fills fields, downloads completed PDF

**Key modules:**
- `shared/pdf_form_extractor.py` — PyMuPDF-based field extraction and PDF filling
- `shared/preparer_store.py` — JSON CRUD for office preparers (`data/config/preparers.json`)
- `forms-assistant/app/pdf_form_store.py` — bridge merging hardcoded + uploaded forms
- `forms-assistant/app/form_definitions.py` — 7 hardcoded form definitions with validation
- `forms-assistant/app/dashboard.py` — Streamlit UI

### 8. Case Checklist (Planned)
Track case progress with auto-populated checklists, deadline tracking, and status dashboards.

**What it does:**
- Create a new case → auto-populates required steps based on case type
- Checklist items with checkboxes, deadlines, and status colors
- Dashboard view showing all active cases with progress bars
- Deadline alerts (overdue = red, due soon = yellow, on track = green)
- Filter by case type, status, attorney, urgency

**Checklist templates by case type:**
- **Asylum:** I-589 filed, declaration drafted, country conditions gathered, supporting evidence compiled, brief written, exhibit bundle compiled, biometrics completed, interview/hearing prep done
- **Family-Based:** I-130 filed, I-485 filed, I-765/I-131 filed, civil documents gathered, translations certified, affidavit of support (I-864), biometrics completed, interview prep
- **VAWA:** I-360 filed, personal declaration, evidence of qualifying relationship, evidence of abuse, evidence of good faith marriage, evidence of good moral character
- **U-Visa:** I-918 filed, personal declaration, law enforcement certification (I-918B), evidence of crime and harm

- **Location:** `case-checklist/`

### 9. Evidence Indexer (Planned)
Organize, label, and compile supporting documents into exhibit packages with auto-generated indices.

**What it does:**
- Upload or reference documents from Box
- Assign exhibit letters (Tab A, Tab B, ...), categories, and descriptions
- Drag-to-reorder exhibits
- Auto-generate exhibit index (Word doc with exhibit letter, title, page range)
- Compile exhibit bundle PDF with tab divider pages and Bates numbering (reuses exhibit_compiler from Country Reports)

**Document categories:**
- Identity Documents (passport, birth certificate, national ID)
- Country Conditions (reports, articles, expert analysis)
- Medical / Psychological (evaluations, treatment records, diagnoses)
- Expert Reports (country conditions experts, forensic experts)
- Declarations (client, witnesses, experts)
- Photographs (injuries, evidence of persecution, family)
- Government Documents (police reports, court records, military records)
- Correspondence (threats, notices, communications)
- Other Supporting Evidence

**Shared code:** The exhibit compilation logic (tab pages, Bates numbering, PDF merging) is already built in Country Reports — this tool reuses that engine for any case type's evidence bundle.

- **Location:** `evidence-indexer/`

## Infrastructure

### Current Setup
- **Development machine:** Jeff's MacBook Pro
- **Target deployment:** Mac Mini on office network
- **Stack:** Python 3.13, FastAPI, Streamlit, uv
- **Integrations:** Box (client files, CCG auth), Google Workspace (document export, OAuth)
- **Access:** Staff connect via browser at `http://[mac-mini]:8502` (hub dashboard)

### Port Assignments
| Port | Service |
|------|---------|
| 8000 | Country Reports (API) |
| 8501 | Country Reports (Streamlit) |
| 8502 | Staff Dashboard (hub) |
| 8503 | Declaration Drafter |
| 8504 | Cover Letters |
| 8505 | Timeline Builder |
| 8506 | Case Checklist |
| 8507 | Brief Builder |
| 8508 | Legal Research |
| 8509 | Forms Assistant |
| 8510 | Evidence Indexer |
| 8511 | Document Translator |
| 8512 | Client Info |
| 8513 | Admin Panel |

### Deployment TODO
- [ ] Set up Mac Mini with Python 3.13 + uv
- [ ] Configure all services as launchd daemons (auto-start on boot)
- [ ] Add basic authentication (password protection for the dashboard)
- [ ] Set up local network access (static IP or hostname for the Mac Mini)
- [ ] Backup strategy for data directories
- [x] Shared .env for Box/Google/Salesforce credentials across all tools

### Cross-Tool Integration Opportunities
- **Country Reports → Brief Builder:** Insert country conditions citations directly into briefs
- **Country Reports → Evidence Indexer:** Include country reports in exhibit bundles
- **Declaration Drafter → Timeline Builder:** Extract dates from declarations into timeline
- **Forms Assistant → Case Checklist:** Auto-check items as forms are completed
- **Evidence Indexer → Brief Builder:** Reference exhibit letters in brief citations
- **Legal Research → Brief Builder:** Insert case law citations into argument sections

## Open Questions
- Should tools share a single database/data directory or stay independent?
- Do we need user accounts per staff member, or is a shared password sufficient?
- Which tool should we build next after Country Reports?
- What's the priority order for the remaining 8 tools?

---

_Last updated: February 16, 2026_
