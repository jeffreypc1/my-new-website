# Testing Guide

## Overview

This project has two test suites:

| Suite | Framework | Command |
|---|---|---|
| Python (unit + API) | pytest | `python -m pytest tests/` |
| JavaScript (browser logic) | Jest | `npm test` |

Tests are automatically run on every push and pull request via GitHub Actions (`.github/workflows/tests.yml`).

---

## Running Python Tests

### Quick run
```bash
python -m pytest tests/ -v
```

### With coverage report
```bash
python -m pytest tests/ --cov=shared --cov-report=term-missing
```

### Full coverage across all modules
```bash
python -m pytest tests/ \
  --cov=shared \
  --cov=evidence-indexer/app \
  --cov=brief-builder/app \
  --cov=case-checklist/app \
  --cov=cover-letters/app \
  --cov=declaration-drafter/app \
  --cov=forms-assistant/app \
  --cov=legal-research/app \
  --cov=timeline-builder/app \
  --cov-report=term-missing \
  --cov-report=html:coverage/python/html
```
Then open `coverage/python/html/index.html` in a browser.

### Required packages
```bash
pip install pytest pytest-cov streamlit python-dotenv simple-salesforce \
            anthropic fastapi httpx python-docx
```

---

## Running JavaScript Tests

### Quick run
```bash
npm test
```

### With coverage
```bash
npm run test:coverage
```
Coverage report is written to `coverage/js/`.

### Required packages
```bash
npm install
```

---

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures (tmp dirs, sample data)
├── shared/
│   ├── test_auth.py                     # Session lifecycle, password management
│   ├── test_usage_tracker.py            # Cost estimation, API usage aggregation
│   ├── test_email_service.py            # Template merging, email sending
│   ├── test_config_store.py             # Config read/write, component toggles
│   ├── test_attorney_store.py           # Attorney CRUD
│   ├── test_pdf_form_extractor.py       # PDF field parsing, auto-suggest roles
│   ├── test_box_client.py               # Box folder ID parsing
│   └── test_salesforce_client.py        # Record flattening, session persistence
├── evidence_indexer/
│   └── test_evidence.py                 # Exhibit lettering, case CRUD, reordering
├── api/
│   ├── test_brief_builder_api.py        # Brief types, sections, generate, export, drafts
│   ├── test_case_checklist_api.py       # Case CRUD, item updates, progress
│   ├── test_cover_letters_api.py        # Templates, generate, export, drafts
│   ├── test_declaration_drafter_api.py  # Types, prompts, generate, export, drafts
│   ├── test_timeline_api.py             # Timeline CRUD, event CRUD, export
│   ├── test_legal_research_api.py       # Search, decisions, collections
│   ├── test_forms_assistant_api.py      # Forms, fields, validate, export, drafts
│   └── test_evidence_indexer_api.py     # Cases, documents, reorder, export
└── js/
    ├── analytics.test.js                # Event tracking, aggregation, localStorage
    └── portal-auth.test.js              # Session management, magic tokens, JWT
```

---

## Design Principles

**Isolation**: Every test uses `tmp_path` (pytest) or fresh `localStorage` mocks (Jest). No test reads from or writes to real config files, production data directories, or external services.

**No external service calls**: Salesforce, Box, Anthropic, and Google APIs are either mocked with `unittest.mock.patch` or the tested code paths avoid calling them entirely.

**Fast**: The full suite runs in under 5 seconds.

---

## Adding New Tests

### Python
1. Add a test file under the appropriate `tests/` subdirectory.
2. Import the module under test.
3. Use `patch.object(module, "DATA_DIR", tmp_path / "mydir")` or similar to isolate file I/O.
4. Use descriptive class names (`TestFunctionName`) and method names (`test_what_it_does`).

### JavaScript
1. Add a `.test.js` file under `tests/js/`.
2. Call `jest.resetModules()` and `require(...)` inside your setup function so each test gets a fresh module state.
3. Mock `localStorage`, `fetch`, and `window` globals before loading the module.
