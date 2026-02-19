# How the Staff Tools Dashboard Works

This is a plain-English guide to what's running on your Mac Mini for
the O'Brien Immigration Law staff tools.

---

## What Is This?

Your Mac Mini runs a suite of 13 web apps (plus 1 background API) that
your staff can access from any computer on the office network by going to:

    http://[mac-mini-ip-or-hostname]:8502

Port 8502 is the **Staff Dashboard** — the main hub with links to every tool.

Each tool is its own small web application built with **Streamlit** (a Python
framework for building web dashboards). They all share a common set of
integrations with Salesforce, Box, Claude AI, and Google Workspace.

---

## What's Running

There are 14 processes running in the background at all times:

| Port | App | What It Does |
|------|-----|-------------|
| 8000 | Country Reports API | Backend search engine for country condition reports |
| 8501 | Country Reports Tool | Search and compile country condition exhibits |
| 8502 | **Staff Dashboard** | Main hub — start here |
| 8503 | Declaration Drafter | Guided asylum declaration writing |
| 8504 | Cover Letters | Generate filing cover pages |
| 8505 | Timeline Builder | Visual case chronologies |
| 8506 | Case Checklist | Track case progress and tasks |
| 8507 | Brief Builder | Assemble legal briefs from templates |
| 8508 | Legal Research | Search case law and BIA decisions |
| 8509 | Forms Assistant | Fill out immigration forms (I-589, I-130, etc.) |
| 8510 | Templates | Email and document templates |
| 8511 | Document Translator | Auto-translate uploaded documents |
| 8512 | Client Info | View/edit Salesforce client data |
| 8513 | Admin Panel | Settings, staff management, configuration |

All of these run as background processes — they don't need a Terminal
window open and they survive closing Terminal.

---

## Automatic Startup

A **macOS LaunchAgent** is installed that automatically runs `start.sh`
whenever you log in to the Mac. This means:

- After a restart or reboot, the tools will start on their own
- You do NOT need to open Terminal or do anything manually
- It takes about 15-20 seconds after login for all apps to be ready

The LaunchAgent file lives at:

    ~/Library/LaunchAgents/com.obrien.stafftools.plist

Startup logs are saved to:

    ~/my-new-website/logs/startup.log
    ~/my-new-website/logs/startup-error.log

If something goes wrong after a reboot, check those log files.

---

## Manual Controls

If you ever need to start or stop things manually, open Terminal and run:

**Start everything:**

    cd ~/my-new-website && ./start.sh

**Stop everything:**

    cd ~/my-new-website && ./stop.sh

**Restart everything:**

    cd ~/my-new-website && ./stop.sh && ./start.sh

**Check if things are running:**

    ps aux | grep streamlit

(If you see a bunch of lines, the tools are running.)

---

## Working on the Project with Claude Code

Claude Code is the AI assistant you've been using to build and modify
this project. To start a session:

    cd ~/my-new-website && claude

This opens an interactive conversation where you can ask Claude to make
changes, fix bugs, add features, etc. Your code lives in `~/my-new-website`.

Claude Code is **separate** from the running tools — starting or stopping
Claude Code does not affect the staff tools, and vice versa.

---

## Where the Code Lives

    ~/my-new-website/
    ├── staff-dashboard/       ← Main hub (port 8502)
    ├── country-reports-tool/  ← Country reports + API
    ├── declaration-drafter/   ← Declaration tool
    ├── cover-letters/         ← Cover letters tool
    ├── timeline-builder/      ← Timeline tool
    ├── case-checklist/        ← Checklist tool
    ├── brief-builder/         ← Brief builder tool
    ├── legal-research/        ← Legal research tool
    ├── forms-assistant/       ← Forms tool
    ├── evidence-indexer/      ← Templates tool (port 8510)
    ├── document-translator/   ← Translator tool
    ├── client-info/           ← Client info tool
    ├── admin-panel/           ← Admin panel
    ├── shared/                ← Code shared by all tools
    ├── data/                  ← App data, config, feedback
    ├── logs/                  ← Startup logs
    ├── start.sh               ← Starts all services
    ├── stop.sh                ← Stops all services
    ├── .env                   ← API keys (Salesforce, Box, Claude, etc.)
    └── STARTUP-GUIDE.md       ← Quick-reference cheat sheet

---

## External Services

The tools connect to these third-party services (credentials are in the `.env` file):

- **Salesforce** — Client CRM data (lookups, contact info, case details)
- **Box** — Cloud document storage (uploading, linking files to cases)
- **Claude AI (Anthropic)** — AI-assisted drafting for declarations, briefs, etc.
- **Google Workspace** — Exporting documents to Google Docs

If any of these stop working, the API key or credentials in `.env` may
have expired and need to be updated.

---

## If Something Breaks

1. **A single tool isn't loading** — Try visiting its port directly
   (e.g., `http://localhost:8507`). If it's down, restart everything
   with `./stop.sh && ./start.sh`.

2. **Nothing loads after a reboot** — Check the startup log at
   `~/my-new-website/logs/startup.log`. Make sure `uv` is installed
   by running `uv --version` in Terminal.

3. **Salesforce/Box/Claude isn't working** — Check the `.env` file for
   expired credentials. You can also check each tool's console output
   in the browser (many show connection status).

4. **Need to update code** — Open Terminal, run `cd ~/my-new-website && claude`,
   and describe what you need changed.

---

## Disabling Auto-Startup

If you ever want to stop the tools from launching automatically at login:

    launchctl unload ~/Library/LaunchAgents/com.obrien.stafftools.plist

To re-enable:

    launchctl load ~/Library/LaunchAgents/com.obrien.stafftools.plist
