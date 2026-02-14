#!/bin/bash
# OpenClaw Dashboard Startup Script

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Find Python interpreter (prefer local venv)
if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python"
elif [ -f "/opt/homebrew/bin/python3" ]; then
    PYTHON="/opt/homebrew/bin/python3"
elif [ -f "/usr/bin/python3" ]; then
    PYTHON="/usr/bin/python3"
else
    echo "Error: Python 3 not found"
    exit 1
fi

cd "$SCRIPT_DIR"

# Load env overrides if present
if [ -f ".env" ]; then
  set -a
  source ".env"
  set +a
fi

export MINIMAX_API_KEY="${MINIMAX_API_KEY}"
export MINIMAX_GROUP_ID="${MINIMAX_GROUP_ID}"
export MINIMAX_QUOTA_URL="${MINIMAX_QUOTA_URL:-https://www.minimaxi.com/v1/api/openplatform/coding_plan/remains?GroupId=${MINIMAX_GROUP_ID}}"

SERVER_PORT="${SERVER_PORT:-18790}"
echo "Starting OpenClaw Dashboard..."
echo "Access at: http://localhost:${SERVER_PORT}"
echo ""
echo "Default login:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "Press Ctrl+C to stop"
echo ""

exec "$PYTHON" server.py
