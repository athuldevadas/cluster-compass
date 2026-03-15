#!/usr/bin/env bash

set -euo pipefail

PORT="${1:-${PORT:-8501}}"
HOST="${2:-${HOST:-localhost}}"

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  echo "Python 3 was not found. Create the virtual environment first or install python3." >&2
  exit 1
fi

"$PYTHON_BIN" -m streamlit run app.py --server.port "$PORT" --server.address "$HOST"
