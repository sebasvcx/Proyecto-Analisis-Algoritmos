#!/usr/bin/env bash
# Levanta backend (FastAPI, puerto 8000) y frontend (Vite, puerto 5173) juntos.
# Ctrl+C detiene ambos.
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")" && pwd)"
VENV="$RAIZ/backend/.venv"

if [[ ! -x "$VENV/bin/uvicorn" ]]; then
  echo "→ Creando entorno de Python e instalando dependencias…"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q -r "$RAIZ/backend/requirements.txt"
fi

if [[ ! -d "$RAIZ/frontend/node_modules" ]]; then
  echo "→ Instalando dependencias del frontend…"
  (cd "$RAIZ/frontend" && npm install)
fi

trap 'kill 0' EXIT INT TERM

(cd "$RAIZ/backend" && "$VENV/bin/uvicorn" api.main:app --reload --port 8000) &
(cd "$RAIZ/frontend" && npm run dev) &

wait
