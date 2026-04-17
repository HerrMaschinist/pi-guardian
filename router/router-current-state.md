# PI Guardian Router Current State

Stand: 2026-04-17

Diese Datei dokumentiert nur den verifizierten Ist-Zustand auf dem Pi. Keine Annahmen, keine aktiven API-Calls, keine Aenderungen am Betrieb.

## 1. Aktive Projektpfade

### 1.1 Aktiver Router-Pfad

Aktiver Router-Code: `/home/alex/pi-guardian/router`

Verzeichnisstruktur:

```text
/home/alex/pi-guardian/router
├── app
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models
│   ├── router
│   └── schemas
├── data
├── logs
├── tests
├── .env
├── .env.example
└── app/requirements.txt
```

### 1.2 Aktiver UI-Pfad

Aktive UI-Quelle: `/home/alex/pi-guardian/ui`

Verzeichnisstruktur:

```text
/home/alex/pi-guardian/ui
├── src
│   ├── api
│   ├── components
│   ├── hooks
│   ├── pages
│   ├── types
│   ├── App.tsx
│   ├── config.ts
│   └── main.tsx
├── dist
├── .env
├── vite.config.ts
└── package.json
```

### 1.3 Relevante Build- und Deployment-Pfade

- UI-Build-Ausgabe: `/home/alex/pi-guardian/ui/dist`
- nginx-Deployment-Config: `/home/alex/pi-guardian/nginx/pi-guardian.conf`
- systemd-Unit: `/etc/systemd/system/pi-guardian-router.service`
- Legacy-/Snapshot-Pfad: `/home/alex/pi-guardian-ui-build`

### 1.4 Kandidatenabgrenzung

| Pfad | Einordnung | Status |
|---|---|---|
| `/home/alex/pi-guardian-router` | Legacy-Standalone-Router | Nicht der aktive Dienstpfad |
| `/home/alex/pi-guardian` | Aktives Monorepo mit `router/` und `ui/` | Source of truth fuer Laufzeit |
| `/home/alex/pi-guardian-ui` | Legacy-Standalone-UI | Nicht der von nginx referenzierte Pfad |
| `/home/alex/pi-guardian-ui-build` | Deployment-/Build-Snapshot | Nicht die aktive Source |

## 2. Antwort auf die Projektfrage

Router und UI sind im aktiven Stand getrennte Subprojekte innerhalb des gemeinsamen Repos `/home/alex/pi-guardian`.

- Router: `/home/alex/pi-guardian/router`
- UI: `/home/alex/pi-guardian/ui`
- Kopplung: lokaler HTTP-Zugriff ueber nginx Reverse Proxy auf `127.0.0.1:8071`

## 3. Aktive systemd-Unit

### 3.1 Unit-Name und Pfad

- Unit-Name: `pi-guardian-router.service`
- Unit-Datei: `/etc/systemd/system/pi-guardian-router.service`

### 3.2 Verifizierter Inhalt

- `WorkingDirectory=/home/alex/pi-guardian/router`
- `User=alex`
- `Group=alex`
- `EnvironmentFile=/home/alex/pi-guardian/router/.env`
- `Environment=PYTHONPATH=/home/alex/pi-guardian/router`
- `ExecStart=/bin/sh -c 'exec /home/alex/pi-guardian/router/.venv/bin/uvicorn app.main:app --host "${ROUTER_HOST:-127.0.0.1}" --port "${ROUTER_PORT:-8071}"'`
- `Restart=always`
- `RestartSec=5`
- Haertung: `ProtectHome=true`, `ProtectSystem=full`, `NoNewPrivileges=true`, `ReadWritePaths=/home/alex/pi-guardian/router/data /home/alex/pi-guardian/router/logs /home/alex/pi-guardian/router/.env`

### 3.3 Journal- und Log-Befund

Beobachtung aus `journalctl -u pi-guardian-router -n 50 --no-pager`:

- Aktuelle Eintraege zeigen nur wiederholte `GET /health` mit `200`
- Keine aktuellen `ERROR`, `Traceback`, `failed` oder `Exception`-Eintraege im abgefragten Bereich
- Der aktuelle Journal-Ausschnitt deutet auf stabil laufenden Dienst hin

Beobachtung aus `/home/alex/pi-guardian/router/logs/router.log`:

- Aktuelle Eintraege zeigen `GET /health 200`
- Am `2026-04-17 08:27:41` wurden `GET /settings 200` und `GET /models 200` protokolliert
- Eine historische Warnung existiert am `2026-04-14 18:34:37` zu nicht erreichbarem Ollama

## 4. Python-Framework und Einstiegspunkt

### 4.1 Aktiver Router-Stack

- Framework: FastAPI
- Einstiegspunkt: `/home/alex/pi-guardian/router/app/main.py`
- App-Instanz: `app = FastAPI(...)`
- Lifespan-Hook: initialisiert die SQLite-Datenbank bei Start via `init_db()`

### 4.2 Legacy-Standalone-Router

Der Pfad `/home/alex/pi-guardian-router` ist ebenfalls FastAPI-basiert, aber ein anderer, aelterer Codebaum mit anderem API-Schnitt und anderem Laufzeitmodell.

## 5. API-Endpunkte im aktiven Router

### 5.1 Uebersicht

| Methode | Pfad | Implementierung | Request-Schema | Response-Schema |
|---|---|---|---|---|
| GET | `/health` | `/home/alex/pi-guardian/router/app/main.py:264-266` | keins | `dict{"status":"ok"}` |
| POST | `/route` | `/home/alex/pi-guardian/router/app/main.py:478-493` | `RouteRequest` | `RouteResponse` |
| GET | `/models` | `/home/alex/pi-guardian/router/app/main.py:331-337` | keins | `list[OllamaModel]` |
| POST | `/models/select` | `/home/alex/pi-guardian/router/app/main.py:496-505` | `ModelSelectionRequest` | `dict{"model": str}` |
| GET | `/settings` | `/home/alex/pi-guardian/router/app/main.py:372-378` | keins | `RouterSettings` |
| PUT | `/settings` | `/home/alex/pi-guardian/router/app/main.py:428-475` | `RouterSettingsUpdate` | `SettingsUpdateResponse` |
| GET | `/status/service` | `/home/alex/pi-guardian/router/app/main.py:313-319` | keins | `ServiceStatus` |
| GET | `/logs` | `/home/alex/pi-guardian/router/app/main.py:322-328` | Query `limit` | `list[LogEntry]` |
| GET | `/history` | `/home/alex/pi-guardian/router/app/main.py:340-369` | Query `limit` | `list[RouteHistoryEntry]` |
| GET | `/integration` | `/home/alex/pi-guardian/router/app/main.py:381-425` | keins | `IntegrationGuide` |
| GET | `/api/tags` | `/home/alex/pi-guardian/router/app/main.py:269-274` | keins | Raw Ollama JSON |
| POST | `/api/generate` | `/home/alex/pi-guardian/router/app/main.py:277-292` | Raw Ollama payload, mindestens `prompt` | Raw Ollama JSON |
| POST | `/api/chat` | `/home/alex/pi-guardian/router/app/main.py:295-310` | Raw Ollama payload, `messages` mit Text | Raw Ollama JSON |
| CRUD | `/clients` | `/home/alex/pi-guardian/router/app/router/clients.py:13-120` und Include in `main.py:86` | `ClientCreate`, `ClientUpdate` | `ClientRead`, `list[ClientRead]`, `204` |

### 5.2 Request- und Response-Schemata

#### `POST /route`

- Request: `RouteRequest`
  - `prompt: str`
  - `preferred_model: str | None`
  - `stream: bool`
- Response: `RouteResponse`
  - `request_id`
  - `model`
  - `response`
  - `done`
  - `done_reason`
  - `duration_ms`
  - `fairness_review_attempted`
  - `fairness_review_used`
  - `fairness_risk`
  - `fairness_review_override`
  - `fairness_reasons`
  - `fairness_notes`

#### `GET /settings`

- Response: `RouterSettings`
  - `router_host`
  - `router_port`
  - `ollama_host`
  - `ollama_port`
  - `timeout`
  - `default_model`
  - `logging_level`
  - `stream_default`
  - `require_api_key`
  - `escalation_threshold`

#### `PUT /settings`

- Request: `RouterSettingsUpdate`
  - `router_host`
  - `router_port`
  - `ollama_host`
  - `ollama_port`
  - `timeout`
  - `default_model`
  - `logging_level`
  - `stream_default`
  - `require_api_key`
  - `escalation_threshold`
  - `restart_service`
- Response: `SettingsUpdateResponse`
  - `settings`
  - `restart_requested`
  - `restart_performed`
  - `restart_message`
  - `validation_warnings`

#### `GET /models`

- Response: `list[OllamaModel]`
  - `name`
  - `size`
  - `modified_at`
  - `digest`

#### `POST /models/select`

- Request: `ModelSelectionRequest`
  - `model: str`
- Response: `{"model": str}`

#### `/clients`

- Request models:
  - `ClientCreate`
  - `ClientUpdate`
- Response model:
  - `ClientRead`
- Storage model:
  - `Client` in SQLite

#### `GET /history`

- Response: `RouteHistoryEntry`
  - `id`
  - `request_id`
  - `prompt_preview`
  - `model`
  - `success`
  - `error_code`
  - `client_name`
  - `duration_ms`
  - `fairness_review_attempted`
  - `fairness_review_used`
  - `fairness_risk`
  - `fairness_review_override`
  - `escalation_threshold`
  - `fairness_reasons`
  - `fairness_notes`
  - `created_at`

## 6. Modelllogik

### 6.1 Wie das Modell bestimmt wird

Die aktive Route-Entscheidung laeuft in zwei Stufen:

1. `select_model(request)` in `/home/alex/pi-guardian/router/app/router/classifier.py`
2. `route_prompt(...)` in `/home/alex/pi-guardian/router/app/router/service.py`

Verifizierte Regeln:

- Wenn `preferred_model` gesetzt ist, gewinnt dieser Wert direkt
- Ohne `preferred_model` entscheidet `select_model_for_prompt(prompt)`
- Prompt-Schluesselwoerter `architektur`, `refactor`, `analyse`, `debug`, `komplex` fuehren zu `LARGE_MODEL`
- Sonst wird `DEFAULT_MODEL` verwendet
- Danach laeuft eine Fairness-Pruefung mit `LARGE_MODEL`
- Wenn die Fairness-Pruefung `override_to_large` setzt oder das Risiko die Schwelle erreicht, wird ebenfalls `LARGE_MODEL` verwendet

### 6.2 Dynamisch oder statisch

Der Router ist dynamisch geroutet. Er ist nicht nur auf ein Standardmodell fixiert.

In der aktiven Logik gibt es:

- prompt-basierte Auswahl
- optionales Override per Request
- fairness-basierte Hochstufung
- persistierbares Standardmodell ueber `/models/select` und `/settings`

Es gibt keine Code-Evidenz fuer Load-Balancing zwischen Modellen oder fuer eine separate Aufgabenklassifikation jenseits dieser Regeln. Das ist eine Inferenz aus dem Source-Tree.

### 6.3 Persistenz des Modellwechsels

- `set_default_model()` schreibt `DEFAULT_MODEL` in die lokale `.env`
- `update_runtime_settings()` schreibt die gesamte Laufzeitkonfiguration in die lokale `.env`
- Die systemd-Unit liest `/home/alex/pi-guardian/router/.env` beim Start
- Damit ist der Modellwechsel nach Neustarts persistent, sofern die Datei geschrieben werden konnte

## 7. Verfuegbare Modelle

Verifiziert aus:

- `/home/alex/pi-guardian/router/app/config.py`
- `/home/alex/pi-guardian/router/.env`
- `/home/alex/pi-guardian/router/.env.example`
- `/home/alex/pi-guardian/router/app/router/settings_manager.py`
- `/home/alex/pi-guardian/router/app/main.py`

Modelle:

- `qwen2.5-coder:1.5b` als `DEFAULT_MODEL`
- `qwen2.5-coder:3b` als `LARGE_MODEL`

Beide Werte sind direkt in Config und `.env` vorhanden, nicht nur dynamisch erkannt.

## 8. Ollama-Anbindung

### 8.1 Base-URL

- Default in Code: `http://127.0.0.1:11434`
- Laufzeitwert kommt aus `/home/alex/pi-guardian/router/.env`
- Wird in `RouterSettings` ueber `ollama_host` und `ollama_port` gespiegelt

### 8.2 Integration

Aktive Ollama-Zugriffe:

- `GET /api/tags` ueber `fetch_models()` und `fetch_raw_tags()`
- `POST /api/generate` ueber `generate_with_ollama()`
- `POST /api/chat` wird durch den Router zu Ollama weitergereicht

### 8.3 Modellverwaltung

- Modellliste wird dynamisch aus Ollama gelesen
- Verfuegbarkeit der Modelle wird beim Speichern von `/settings` und beim Setzen von `/models/select` gegen die Ollama-Liste validiert
- Das aktive Standardmodell wird nicht in einer separaten DB-Tabelle gespeichert, sondern in der `.env`

## 9. UI-zu-API-Verknuepfung

### 9.1 API-Client

Gemeinsamer UI-Client: `/home/alex/pi-guardian/ui/src/api/client.ts`

Verwendeter Base-Pfad:

- `CONFIG.apiBaseUrl`
- Default: `/api`
- Vite-Entwicklung: Proxy auf `http://127.0.0.1:8071`

### 9.2 Seiten und Endpunkte

| UI-Datei | Verwendete Endpunkte |
|---|---|
| `/home/alex/pi-guardian/ui/src/pages/Dashboard.tsx` | `GET /status/service`, `GET /settings` |
| `/home/alex/pi-guardian/ui/src/pages/Diagnostics.tsx` | `GET /health`, `POST /route` |
| `/home/alex/pi-guardian/ui/src/pages/Models.tsx` | `GET /models`, `GET /settings`, `POST /route`, `POST /models/select` |
| `/home/alex/pi-guardian/ui/src/pages/Settings.tsx` | `GET /settings`, `PUT /settings` |
| `/home/alex/pi-guardian/ui/src/pages/Clients.tsx` | `GET /clients`, `POST /clients`, `PUT /clients/:id`, `DELETE /clients/:id`, `GET /integration` |
| `/home/alex/pi-guardian/ui/src/pages/Logs.tsx` | `GET /logs` |
| `/home/alex/pi-guardian/ui/src/pages/History.tsx` | `GET /history` |

### 9.3 Schnelltest-Anbindung

Die Diagnose-Seite sendet direkt:

- `GET /health`
- `POST /route` mit `prompt` und optional `preferred_model`

Damit ist der Schnelltest bereits an den produktiven Routerpfad angebunden.

## 10. UI-Base-URL und Deployment

### 10.1 Development

`/home/alex/pi-guardian/ui/vite.config.ts`:

- Proxy-Pfad: `/api`
- Target: `http://${VITE_ROUTER_HOST}:${VITE_ROUTER_PORT}`
- Defaultwerte aus `.env`: `127.0.0.1:8071`
- Rewrite entfernt das `/api`-Prefix

### 10.2 Production

`/home/alex/pi-guardian/nginx/pi-guardian.conf`:

- UI-Root: `/home/alex/pi-guardian/ui/dist`
- UI-Port: `3001`
- API-Proxy: `/api/` -> `http://127.0.0.1:8071/`

Damit ist die produktive Kette:

`Browser -> nginx:3001 -> /api -> FastAPI Router:8071 -> Ollama:11434`

## 11. Altpfade und Kritikalitaet

### 11.1 Gefundene veraltete Referenzen auf `/home/Alex/`

Aktive Source-Tree-Pruefung ohne Backup-/Vendor-Verzeichnisse:

- Keine Treffer in `/home/alex/pi-guardian/router`
- Keine Treffer in `/home/alex/pi-guardian/ui`
- Keine Treffer in `/etc/systemd/system`

Treffer im Snapshot-Bereich:

- `/home/alex/pi-guardian-ui-build/README.md:18`
- `/home/alex/pi-guardian-ui-build/pi-guardian.conf:5`

Zusatztreffer in einem Backup-Venv innerhalb des Legacy-Router-Trees:

- `/home/alex/pi-guardian/router/.venv_pre_alex_migration_backup/...`

### 11.2 Kritikalitaet

| Fundstelle | Kritikalitaet | Beurteilung |
|---|---|---|
| `pi-guardian-ui-build/README.md` | Niedrig | Nur Doku im Snapshot, nicht Laufzeitpfad |
| `pi-guardian-ui-build/pi-guardian.conf` | Mittel | Falscher Pfad in Deployment-Config eines Snapshots |
| `router/.venv_pre_alex_migration_backup` | Niedrig | Backup-Artefakt, nicht aktiver Laufzeitpfad |

### 11.3 Empfohlene Behebung

- Snapshot-Doku und Snapshot-Config auf `/home/alex/...` umstellen, falls der Snapshot weiter genutzt wird
- Backup-Venv nicht fuer Deployment oder Dokumentation referenzieren
- Aktive Source-Pfade bleiben unveraendert

## 12. Verifizierte Host- und Portdaten

- Router-Host: `127.0.0.1`
- Router-Port: `8071`
- Ollama-Host: `127.0.0.1`
- Ollama-Port: `11434`
- UI-Port via nginx: `3001`

## 13. Vorbereitung fuer Guardian-Anbindung

### 13.1 Welche Endpunkte Guardian spaeter nutzen sollte

Minimal fuer Inferenz:

- `POST /route`
- `GET /health`

Optional fuer Administration:

- `GET /settings`
- `PUT /settings`
- `GET /models`
- `POST /models/select`
- `GET /clients`
- `GET /integration`

### 13.2 Minimales Request-Format fuer `POST /route`

```json
{
  "prompt": "string",
  "preferred_model": "optional string",
  "stream": false
}
```

Nur `prompt` ist zwingend.

### 13.3 Sichere Response-Struktur fuer Guardian

Guardian kann fuer `/route` sicher mit `RouteResponse` rechnen:

- `request_id`
- `model`
- `response`
- `done`
- `done_reason`
- `duration_ms`
- Fairness-Felder

Bei Fehlern liefert der Router `RouteErrorResponse` mit:

- `request_id`
- optional `model`
- `error.code`
- `error.message`
- `error.retryable`

### 13.4 Separate Guardian-Client-Empfehlung

Ja, ein separater Guardian-Client ist sinnvoll.

Begruendung:

- klares Transport- und Auth-Handling
- lokaler API-Key im Header `X-API-Key`
- saubere Retry- und Timeout-Regeln
- klare Trennung zwischen Inferenz und Admin-Operationen

### 13.5 Ist der Router schon fuer strukturierte Maschinenanfragen geeignet?

Ja, fuer den aktiven `POST /route`-Pfad ist der Router bereits strukturiert genug:

- Pydantic-Requestmodell
- Pydantic-Responsemodell
- definierte Fehlerpayloads
- persistierte Anfragehistorie

Was Guardian trotzdem beachten muss:

- `REQUIRE_API_KEY` ist in der aktiven `.env` auf `true`
- bei aktivem Schutz muss `X-API-Key` mitgesendet werden
- `/models/select` und `/settings` sind Admin-Funktionen und nicht fuer jeden Client gedacht

## 14. Schlussbewertung

### 14.1 Aktiver Zustand

- Aktiver Router laeuft unter `/home/alex/pi-guardian/router`
- Aktive UI laeuft aus `/home/alex/pi-guardian/ui`
- nginx verbindet beide lokal und serviert die UI auf Port `3001`
- Der Router ist zurzeit stabil und liefert `200` fuer die laufenden Health-Checks

### 14.2 Relevante Blocker fuer Guardian

- API-Key-Pflicht ist aktuell aktiv
- Guardian braucht einen registrierten Client mit erlaubter Route
- Wenn Guardian Admin-Endpoints nutzen soll, braucht er passende Freigaben in `/clients`

