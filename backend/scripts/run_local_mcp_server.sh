#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${BACKEND_DIR}"

if [[ -x "${BACKEND_DIR}/venv/bin/python" ]]; then
  exec "${BACKEND_DIR}/venv/bin/python" -m app.mcp.local_refiner_mcp_server
fi

exec python3 -m app.mcp.local_refiner_mcp_server

