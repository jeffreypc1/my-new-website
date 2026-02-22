#!/bin/bash
#
# O'Brien Immigration Law — Stop All Staff Tools
#
# Usage:  ./stop.sh
#

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RESET="\033[0m"

echo ""
echo -e "${BOLD}O'Brien Immigration Law — Stopping Staff Tools${RESET}"
echo "================================================"
echo ""

# Find and kill all related processes
KILLED=0

# Kill streamlit processes running on our ports
for port in 8000 8501 8502 8503 8504 8505 8506 8507 8508 8509 8510 8511 8512 8513 8514 8515; do
    pids=$(lsof -ti :$port 2>/dev/null)
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill 2>/dev/null
        KILLED=$((KILLED+1))
    fi
done

# Also kill any straggler uv run processes for our project
pkill -f "uv run.*my-new-website" 2>/dev/null

# Wait and retry if anything survived
for attempt in 1 2 3; do
    sleep 1
    REMAINING=$(pgrep -f "my-new-website.*(streamlit|uvicorn)" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$REMAINING" -eq 0 ]; then
        break
    fi
    # Force kill on final attempt
    if [ "$attempt" -eq 3 ]; then
        pkill -9 -f "my-new-website.*(streamlit|uvicorn)" 2>/dev/null
        sleep 1
        REMAINING=$(pgrep -f "my-new-website.*(streamlit|uvicorn)" 2>/dev/null | wc -l | tr -d ' ')
    fi
done

if [ "$REMAINING" -eq 0 ]; then
    echo -e "${GREEN}All services stopped.${RESET}"
else
    echo -e "${YELLOW}$REMAINING process(es) still running. Try running ./stop.sh again.${RESET}"
fi
echo ""
