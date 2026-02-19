#!/bin/bash
#
# O'Brien Immigration Law — Staff Tools Dashboard
# Starts all 14 services (13 Streamlit apps + 1 API)
#
# Usage:  ./start.sh
# Stop:   ./stop.sh
#

BASE="/Users/jeff/my-new-website"

# Ensure Homebrew tools (uv, python) are on PATH even when run by launchd
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# Text formatting
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo ""
echo -e "${BOLD}O'Brien Immigration Law — Starting Staff Tools${RESET}"
echo "================================================"
echo ""

# Check if services are already running
if pgrep -f "streamlit run.*--server.port 8502" > /dev/null 2>&1; then
    echo -e "${YELLOW}Services appear to already be running.${RESET}"
    echo "Run ./stop.sh first if you want to restart them."
    echo ""
    exit 1
fi

# Track failures
FAILED=0

start_app() {
    local name="$1"
    local dir="$2"
    local cmd="$3"

    cd "$dir" || { echo -e "  ${RED}[FAIL]${RESET} $name — directory not found: $dir"; FAILED=$((FAILED+1)); return; }
    nohup $cmd > /dev/null 2>&1 &
    echo -e "  ${GREEN}[OK]${RESET}   $name"
}

# --- Country Reports API (must start first — other tools may depend on it) ---
echo -e "${BOLD}Starting API...${RESET}"
start_app "Country Reports API    :8000" \
    "$BASE/country-reports-tool" \
    "uv run uvicorn app.api:app --port 8000"

sleep 1

# --- Staff Dashboard Hub ---
echo ""
echo -e "${BOLD}Starting Staff Dashboard...${RESET}"
start_app "Staff Dashboard        :8502" \
    "$BASE/country-reports-tool" \
    "uv run streamlit run $BASE/staff-dashboard/app.py --server.port 8502"

# --- Individual Tools ---
echo ""
echo -e "${BOLD}Starting Tools...${RESET}"

start_app "Country Reports Tool   :8501" \
    "$BASE/country-reports-tool" \
    "uv run streamlit run app/dashboard.py --server.port 8501"

start_app "Declaration Drafter    :8503" \
    "$BASE/declaration-drafter" \
    "uv run streamlit run app/dashboard.py --server.port 8503"

start_app "Cover Letters          :8504" \
    "$BASE/cover-letters" \
    "uv run streamlit run app/dashboard.py --server.port 8504"

start_app "Timeline Builder       :8505" \
    "$BASE/timeline-builder" \
    "uv run streamlit run app/dashboard.py --server.port 8505"

start_app "Case Checklist         :8506" \
    "$BASE/case-checklist" \
    "uv run streamlit run app/dashboard.py --server.port 8506"

start_app "Brief Builder          :8507" \
    "$BASE/brief-builder" \
    "uv run streamlit run app/dashboard.py --server.port 8507"

start_app "Legal Research         :8508" \
    "$BASE/legal-research" \
    "uv run streamlit run app/dashboard.py --server.port 8508"

start_app "Forms Assistant        :8509" \
    "$BASE/forms-assistant" \
    "uv run streamlit run app/dashboard.py --server.port 8509"

start_app "Templates              :8510" \
    "$BASE/evidence-indexer" \
    "uv run streamlit run app/dashboard.py --server.port 8510"

start_app "Document Translator    :8511" \
    "$BASE/document-translator" \
    "uv run streamlit run app/dashboard.py --server.port 8511"

start_app "Client Info            :8512" \
    "$BASE/client-info" \
    "uv run streamlit run app/dashboard.py --server.port 8512"

start_app "Admin Panel            :8513" \
    "$BASE/admin-panel" \
    "uv run streamlit run app/dashboard.py --server.port 8513"

start_app "Hearing Prep           :8514" \
    "$BASE/hearing-prep" \
    "uv run streamlit run app/dashboard.py --server.port 8514"

# --- Summary ---
echo ""
echo "================================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All services started successfully.${RESET}"
else
    echo -e "${YELLOW}Started with $FAILED failure(s). Check above for details.${RESET}"
fi
echo ""
echo -e "Staff Dashboard: ${BOLD}http://localhost:8502${RESET}"
echo ""
echo "It may take 10-15 seconds for all apps to fully load."
echo "Run ./stop.sh to shut everything down."
echo ""
