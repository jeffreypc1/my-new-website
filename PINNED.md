# Pinned Items

Items to revisit later. Add with "put a pin in it" during sessions.

---

## Open

- **Email button in client banner not clickable** (Feb 17, 2026)
  - Button renders but stays disabled. Likely cause: active client record missing `Email` field, or Salesforce unavailable at the time.
  - Code: `shared/client_banner.py:369-391` — `has_email` check and `disabled=` flag.
  - To debug: pull a client that definitely has an Email field in SF and check if the button enables.

## Resolved

_(none yet)_
