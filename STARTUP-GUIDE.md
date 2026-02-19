# O'Brien Immigration Law — Staff Tools Startup Guide

## Quick Reference

| What you want to do | Command |
|---|---|
| Start all tools | `cd ~/my-new-website && ./start.sh` |
| Stop all tools | `cd ~/my-new-website && ./stop.sh` |
| Restart everything | `cd ~/my-new-website && ./stop.sh && ./start.sh` |
| Open the dashboard | Go to `http://localhost:8502` in your browser |
| Start Claude Code | `cd ~/my-new-website && claude` |

---

## After a Reboot (or if the tools aren't running)

1. **Open Terminal** (search "Terminal" in Spotlight, or find it in Applications > Utilities)

2. **Start the tools:**
   ```
   cd ~/my-new-website && ./start.sh
   ```
   You'll see a checklist as each service starts up. Wait about 15 seconds for everything to fully load.

3. **Open your browser** and go to:
   ```
   http://localhost:8502
   ```
   That's the Staff Dashboard hub with links to all the tools.

4. **To work with Claude Code** (optional — only when you want to make changes to the project):
   ```
   cd ~/my-new-website && claude
   ```

---

## Shutting Things Down

To stop all the tools:
```
cd ~/my-new-website && ./stop.sh
```

**Note:** Closing Terminal does NOT stop the tools. They run in the background. You must use `./stop.sh` to stop them, or they'll stop when the Mac restarts.

---

## Port Map

| Port | Tool |
|---|---|
| 8000 | Country Reports API |
| 8501 | Country Reports Tool |
| 8502 | **Staff Dashboard (main hub)** |
| 8503 | Declaration Drafter |
| 8504 | Cover Letters |
| 8505 | Timeline Builder |
| 8506 | Case Checklist |
| 8507 | Brief Builder |
| 8508 | Legal Research |
| 8509 | Forms Assistant |
| 8510 | Templates |
| 8511 | Document Translator |
| 8512 | Client Info |
| 8513 | Admin Panel |

---

## Troubleshooting

**"Services appear to already be running"**
The tools are already up. Open `http://localhost:8502` in your browser. If they seem broken, run `./stop.sh` first, then `./start.sh`.

**A single tool isn't loading**
Check if it's running by visiting its port directly (e.g., `http://localhost:8507` for Brief Builder). If not, you can restart everything with `./stop.sh && ./start.sh`.

**"command not found: claude"**
Claude Code isn't installed, or the shell hasn't loaded the path. Try opening a new Terminal window and running `claude` again.

**Nothing loads after `./start.sh`**
Wait 15 seconds — Streamlit apps take a moment to spin up. If still nothing, check that Python and `uv` are installed by running `uv --version` in Terminal.
