#!/bin/bash
set -e
cd /home/Alex/pi-guardian
echo "[deploy] Hole aktuellen Stand von GitHub..."
git fetch origin
git reset --hard origin/master
echo "[deploy] Starte Router neu..."
sudo systemctl restart pi-guardian-router
echo "[deploy] Lade nginx neu..."
sudo systemctl reload nginx
echo "[deploy] Fertig: $(date)"
