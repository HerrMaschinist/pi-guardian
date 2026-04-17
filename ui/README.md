# PI Guardian Admin UI

Lokale Admin-Oberfläche für den PI Guardian Model Router.

## Voraussetzungen

- Node.js >= 18
- npm
- PI Guardian Router erreichbar im LAN

## Setup

```bash
tar -xzf pi-guardian-ui.tar.gz
cd pi-guardian-ui
npm install
```

## Konfiguration

Alle Infrastrukturwerte stehen zentral in `.env`:

```
VITE_ROUTER_HOST=127.0.0.1
VITE_ROUTER_PORT=8070
VITE_DEFAULT_MODEL=qwen2.5-coder:1.5b
```

Diese Werte werden verwendet von:
- `vite.config.ts` – Proxy-Target im Dev-Modus
- `src/config.ts` – Anzeige in der UI und API-Client

Wenn sich Host, Port oder Modell ändern, reicht eine Anpassung der `.env`.

## Entwicklung

```bash
npm run dev
```

Startet den Vite-Dev-Server auf Port 3000.
Der Proxy leitet `/api/*` automatisch an den in `.env` konfigurierten Router weiter.

Erreichbar unter: `http://localhost:3000`

## Production Build

```bash
npm run build
npm run preview
```

Build-Output liegt in `dist/`.

### ANNAHME: Production-Deployment

Für den Betrieb ohne Vite-Dev-Server muss entweder:
- `dist/` über einen Webserver (Nginx) ausgeliefert werden, der auch den Proxy übernimmt
- oder `VITE_API_URL` als Umgebungsvariable auf die direkte Backend-URL gesetzt werden

## Proxy-Konfiguration (Vite Dev)

Definiert in `vite.config.ts`, liest Host und Port aus `.env`:

```
/api/* → http://${VITE_ROUTER_HOST}:${VITE_ROUTER_PORT}/*
```

Beispiel: `fetch('/api/health')` wird zu `http://127.0.0.1:8070/health` (bei Standard-.env).

---

## Architektur

```
.env                               # Zentrale Infrastrukturwerte (Host, Port, Modell)
vite.config.ts                     # Proxy-Config, liest aus .env
src/
├── config.ts                      # Zentrale Config für die gesamte App
├── api/
│   └── client.ts                  # Zentraler API-Client mit Timeout + Fehlerbehandlung
├── components/
│   ├── Card.tsx                   # Wiederverwendbare Karten-Komponente
│   ├── Layout.tsx                 # Seiten-Layout-Wrapper
│   ├── Sidebar.tsx                # Navigation + Statusanzeige
│   └── StatusBadge.tsx            # Verbindungsstatus-Anzeige
├── hooks/
│   └── useApi.ts                  # Health-Polling + generischer API-Call-Hook
├── pages/
│   ├── Dashboard.tsx              # Systemübersicht
│   ├── Models.tsx                 # Modellverwaltung + Testanfrage
│   ├── Diagnostics.tsx            # Health-Check + Route-Test mit Request/Response
│   ├── Clients.tsx                # Client-Verwaltung (Mock)
│   ├── Settings.tsx               # Router-Einstellungen (Mock)
│   └── Logs.tsx                   # Log-Ansicht (Mock)
├── types/
│   └── index.ts            # Alle TypeScript-Typen
├── App.tsx                 # Hauptkomponente + Seitenrouting
├── main.tsx                # Einstiegspunkt
├── styles.css              # Vollständiges Stylesheet
└── vite-env.d.ts           # Vite-Typen
```

---

## Funktionsstatus

### SOFORT NUTZBAR (Phase 1)

| Funktion                      | Seite       | Endpunkt       |
|-------------------------------|-------------|----------------|
| Health-Check                  | Dashboard   | GET /health    |
| Health-Check mit Antwortzeit  | Diagnose    | GET /health    |
| Route-Test mit Prompt         | Diagnose    | POST /route    |
| Modelltest mit Prompt         | Modelle     | POST /route    |
| Verbindungsstatus-Anzeige     | Sidebar     | GET /health    |
| Request/Response-Anzeige      | Diagnose    | POST /route    |
| Fehleranzeige (Timeout etc.)  | Diagnose    | –              |

### BACKEND ERFORDERLICH (Phase 2)

| Endpunkt              | Zweck                          | Genutzt auf       |
|-----------------------|--------------------------------|--------------------|
| GET /models           | Verfügbare Modelle auflisten   | Modelle            |
| POST /models/select   | Standardmodell wechseln        | Modelle            |
| GET /settings         | Konfiguration laden            | Einstellungen      |
| PUT /settings         | Konfiguration speichern        | Einstellungen      |
| GET /status/service   | systemd-Status, PID, Uptime    | Dashboard          |
| GET /logs             | Log-Einträge abrufen           | Logs               |
| GET /clients          | Registrierte Clients laden     | Clients            |
| POST /clients         | Neuen Client anlegen           | Clients            |
| PUT /clients/:id      | Client bearbeiten              | Clients            |
| DELETE /clients/:id   | Client entfernen               | Clients            |

### Phase 3 (Zugriffskontrolle)

- API-Key-basierte Authentifizierung
- Rollen/Berechtigungen pro Client
- Token-Validierung im Router-Backend
- Rate Limiting pro Client

---

## Bekannte Werte (konfigurierbar über .env)

- Router-Host: siehe `VITE_ROUTER_HOST` (Standard: 127.0.0.1)
- Router-Port: siehe `VITE_ROUTER_PORT` (Standard: 8070)
- Aktives Modell: siehe `VITE_DEFAULT_MODEL` (Standard: qwen2.5-coder:1.5b)
- Backend: Ollama (lokal)
- Bestehende Endpunkte: GET /health, POST /route

## API-Schnittstelle POST /route

Das Backend erwartet aktuell:

```json
{
  "task_description": "...",
  "task_type": "generic_json_task",
  "source": "admin",
  "expected_format": "text",
  "priority": "normal",
  "force_model": "fast_model"
}
```

Die UI nutzt aktuell die bestehenden Router-Endpunkte `GET /health` und `POST /route`.
Die Seiten `Clients`, `Settings` und `Logs` bleiben vorbereitet, benötigen aber weitere Backend-Endpunkte.
