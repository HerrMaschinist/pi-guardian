# PI Guardian

Monorepo für das PI Guardian System auf dem Raspberry Pi.

## Struktur

```
pi-guardian/
├── router/     FastAPI-Backend, Prompt-Routing an Ollama
├── ui/         React/TypeScript-Dashboard (Vite)
└── nginx/      nginx-Konfiguration für das Deployment
```

## router/

- FastAPI + Uvicorn, Port 8071
- Läuft als systemd-Service `pi-guardian-router`
- Konfiguration via `router/.env`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port 8071`

## ui/

- React 18 + TypeScript + Vite
- Build: `cd ui && npm install && npm run build`
- Build-Output: `ui/dist/` → wird von nginx serviert

## nginx/

- Serviert `ui/dist/` auf Port 3001
- Proxyt `/api/*` → `http://127.0.0.1:8071/`
- Deployment: siehe `nginx/README.md` (im nginx-Ordner nach Bedarf anlegen)

## Deployment auf dem Pi

```bash
git clone https://github.com/HerrMaschinist/pi-guardian.git
# Router
cd pi-guardian/router && python -m venv .venv && .venv/bin/pip install -r app/requirements.txt
# UI
cd ../ui && npm install && npm run build
# nginx
sudo cp ../nginx/pi-guardian.conf /etc/nginx/sites-available/pi-guardian
sudo ln -s /etc/nginx/sites-available/pi-guardian /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```
