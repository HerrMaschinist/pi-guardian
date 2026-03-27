# PI Guardian

Lokales KI-Routing-System auf dem Raspberry Pi.

## Architektur

- **Router** (router/): FastAPI, Port 8071, systemd
- **UI** (ui/): React + Vite, nginx, Port 3001
- **nginx** (nginx/): Reverse Proxy + Static Serving

## Produktiv laufende Endpunkte

| Endpunkt | Funktion |
|---|---|
| GET /health | Status-Check |
| POST /route | Prompt -> Ollama |
| GET /status/service | systemd-Status |
| GET /models | Ollama-Modellliste |
| GET /logs | Router-Logdatei |
| GET /settings | Aktive Konfiguration |

## Deployment auf dem Pi

```bash
/home/Alex/pi-guardian/nginx/deploy.sh
```

Das Script (`nginx/deploy.sh`) zieht den aktuellen Stand von GitHub,
startet den Router-Service neu und laedt nginx neu.
Es muss einmalig ausfuehrbar gemacht werden:

```bash
chmod +x /home/Alex/pi-guardian/nginx/deploy.sh
```

## Erstinstallation auf neuem Pi

```bash
# 1. Repo klonen
sudo git clone https://github.com/HerrMaschinist/pi-guardian.git /home/Alex/pi-guardian
sudo chown -R alex:alex /home/Alex/pi-guardian

# 2. Python-Umgebung einrichten
cd /home/Alex/pi-guardian/router
python3 -m venv .venv
.venv/bin/pip install -r app/requirements.txt

# 3. systemd-Service einrichten
sudo cp /home/Alex/pi-guardian/nginx/pi-guardian-router.service \
    /etc/systemd/system/pi-guardian-router.service
sudo systemctl daemon-reload
sudo systemctl enable pi-guardian-router
sudo systemctl start pi-guardian-router

# 4. nginx einrichten
sudo apt install -y nginx
sudo cp /home/Alex/pi-guardian/nginx/pi-guardian.conf \
    /etc/nginx/sites-available/pi-guardian
sudo ln -s /etc/nginx/sites-available/pi-guardian \
    /etc/nginx/sites-enabled/pi-guardian
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl start nginx

# 5. Erreichbarkeit pruefen
curl http://192.168.50.10:8071/health
curl http://192.168.50.10:3001/
```

## Offene Punkte (Phase 3)

- POST /models/select - Modellwechsel
- PUT /settings - Konfiguration persistieren
- GET/POST/PUT/DELETE /clients - Client-Verwaltung
- Login, Rollen, Datenbank (SQLite)
