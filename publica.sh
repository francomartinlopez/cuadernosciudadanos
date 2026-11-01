#!/bin/sh
# Arma datos.js, commitea y publica en main (Netlify actualiza solo).
set -e
cd "$(dirname "$0")"
python3 armar.py
git add -A
git commit -m "${1:-Actualización de la revista}" || true
git push origin main
git log -1 --oneline
