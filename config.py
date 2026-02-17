"""
OpenClaw Dashboard Configuration
"""
import os
from pathlib import Path

# Paths
OPENCLAW_DIR = Path.home() / ".openclaw"
WORKSPACE_DIR = Path.home() / "openclaw"

# Server config
SERVER_HOST = "0.0.0.0"
SERVER_PORT = int(os.environ.get("SERVER_PORT", "18790"))

# Minimax (Coding Plan) API
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY")
MINIMAX_API_BASE = os.environ.get("MINIMAX_API_BASE", "https://www.minimaxi.com")
MINIMAX_GROUP_ID = os.environ.get("MINIMAX_GROUP_ID")
MINIMAX_QUOTA_URL = os.environ.get("MINIMAX_QUOTA_URL")
MINIMAX_USAGE_IS_REMAINING = os.environ.get("MINIMAX_USAGE_IS_REMAINING", "1") == "1"

# JWT config
JWT_SECRET = "openclaw-dashboard-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password file
PASSWORDS_FILE = OPENCLAW_DIR / "dashboard_users.json"
INTEGRATIONS_FILE = OPENCLAW_DIR / "dashboard_integrations.json"

# Default admin credentials (first run only)
DEFAULT_ADMIN = {
    "username": "admin",
    "password": "admin123",
    "must_change_password": True
}

# Status check intervals (seconds)
STATUS_CACHE_TTL = 10  # Cache duration for status data
