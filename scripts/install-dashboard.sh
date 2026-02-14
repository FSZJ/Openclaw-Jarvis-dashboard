#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

command -v python3 >/dev/null 2>&1 || { echo "python3 not found"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "node not found"; exit 1; }

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

cd frontend
npm install
npm run build
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  cp .env.example .env
fi

echo "Install done. Run: source .venv/bin/activate && ./start.sh"
