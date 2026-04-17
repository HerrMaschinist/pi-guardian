#!/bin/bash
set -euo pipefail
cd /home/alex/pi-guardian
echo "[deploy] Hole aktuellen Stand von GitHub..."
git fetch origin
branch="$(git rev-parse --abbrev-ref HEAD)"
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "[deploy] Abbruch: Arbeitsverzeichnis ist nicht sauber."
  exit 1
fi
git merge --ff-only "origin/${branch}"
echo "[deploy] Starte Router neu..."
sudo systemctl restart pi-guardian-router
echo "[deploy] Lade nginx neu..."
sudo systemctl reload nginx
echo "[deploy] Fertig: $(date)"
