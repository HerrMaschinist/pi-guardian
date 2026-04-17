# Router Agents Operations

## Wichtige Dateien

- `/home/alex/pi-guardian/router/app/main.py`
  - FastAPI-App, Router-Registrierung, Logging, bestehende Endpunkte
- `/home/alex/pi-guardian/router/app/api/routes_agents.py`
  - Agenten-API für Registry, Settings und Runtime
- `/home/alex/pi-guardian/router/app/api/routes_skills.py`
  - Skill-API für Registry- und Detailabfragen
- `/home/alex/pi-guardian/router/app/api/routes_actions.py`
  - Action-API für Vorschlag, Ausführung und Registry
- `/home/alex/pi-guardian/router/app/agents/registry.py`
  - zentrale Agenten-Registry mit System- und Actor-Agenten
- `/home/alex/pi-guardian/router/app/agents/runtime.py`
  - mehrschrittige Agentenlaufzeit mit Skill- und Action-Erkennung
- `/home/alex/pi-guardian/router/app/agents/tool_parser.py`
  - Parser für Tool-, Skill- und Action-JSON
- `/home/alex/pi-guardian/router/app/skills/registry.py`
  - zentrale Skill-Registry
- `/home/alex/pi-guardian/router/app/skills/executor.py`
  - kontrollierte Skill-Ausführung
- `/home/alex/pi-guardian/router/app/skills/standard.py`
  - implementierte Standard-Skills
- `/home/alex/pi-guardian/router/app/actions/registry.py`
  - zentrale Action-Registry
- `/home/alex/pi-guardian/router/app/actions/executor.py`
  - kontrollierte Action-Ausführung mit Freigabeprüfung
- `/home/alex/pi-guardian/router/app/actions/standard.py`
  - implementierte Standard-Actions
- `/home/alex/pi-guardian/router/app/tools/registry.py`
  - zentrale Tool-Registry
- `/home/alex/pi-guardian/router/app/tools/executor.py`
  - kontrollierte Tool-Ausführung
- `/home/alex/pi-guardian/router/app/tools/system_status_tool.py`
  - Systemstatus lesen
- `/home/alex/pi-guardian/router/app/tools/docker_status_tool.py`
  - Docker-Status lesen
- `/home/alex/pi-guardian/router/app/tools/service_status_tool.py`
  - sichere Services lesen
- `/home/alex/pi-guardian/router/app/tools/router_logs_tool.py`
  - begrenzte Router-Logs lesen
- `/home/alex/pi-guardian/router/docs/router-agent-architecture.md`
  - Architekturbegründung
- `/home/alex/pi-guardian/router/docs/router-skills-and-actions.md`
  - Skill-/Action-Übersicht und Freigabemodell
- `/home/alex/pi-guardian/router/docs/router-admin-auth.md`
  - dedizierter Admin-Client, Auth-Bootstrap und UI-Session-Wiederherstellung
- `/home/alex/pi-guardian/router/docs/router-memory-db.md`
  - SQLite-Persistenz für Runs, Knowledge, Feedback, Incidents und Freigaben
- `/home/alex/pi-guardian/router/docs/router-project-boundaries.md`
  - saubere Trennung zwischen Router und Kids Controller

## Registrierte Agenten

- `guardian_supervisor`
- `service_diagnose`
- `log_analyst`
- `service_operator`

System-Agenten:

- `guardian_supervisor`
- `service_diagnose`
- `log_analyst`

Actor-Agent:

- `service_operator`

## Registrierte Skills

- `system_snapshot`
- `service_triage`
- `router_log_review`
- `docker_snapshot`
- `service_log_correlation`
- `incident_summary`
- `agent_health_check`

## Registrierte Actions

- `restart_service`
- `restart_container`
- `rerun_health_check`

## Policy-Modell

Die UI zeigt die Agenten-Policy nur an. Die tatsächliche Durchsetzung findet zentral in den Skill-, Tool- und Action-Executors statt.

Rechte und Limits pro Agent:

- `allowed_tools`
- `allowed_skills`
- `allowed_actions`
- `read_only`
- `can_propose_actions`
- `can_use_logs`
- `can_use_services`
- `can_use_docker`
- `max_steps`
- `max_tool_calls`

System-Agenten behalten ihre Sicherheitsbasis unveränderbar. Über UI oder API können sie nicht auf schreibende Rechte oder zusätzliche Tool-Klassen aufgewertet werden. `service_operator` darf Aktionen nur vorschlagen, nicht freigeschaltet autonom ausführen.

## Integration in den Router

Die Agenten-, Skill- und Action-API hängt direkt an der bestehenden FastAPI-App. Der Router bleibt funktional erhalten, und die neue Laufzeit ist ein zusätzlicher, sauber getrennter Bereich.

Die Route-Gruppen nutzen dieselbe Authentifizierung wie die übrigen geschützten Routen. Wenn `REQUIRE_API_KEY=true` ist, müssen Clients die administrativen Route-Gruppen freigeschaltet haben.

## Persistenz und Memory

Die Memory-API ist im Router unter `/memory` angebunden. Sie ist auf Lesezugriffe und gezielte Vorbereitung ausgelegt:

- `GET /memory/runs`
- `GET /memory/runs/{run_id}`
- `GET /memory/incidents`
- `GET /memory/incidents/{incident_id}`
- `GET /memory/knowledge`
- `GET /memory/feedback`

Schreibende Vorbereitungspfade:

- `POST /memory/incidents`
- `POST /memory/incidents/{incident_id}/findings`
- `POST /memory/knowledge`
- `POST /memory/feedback`

Die DB liegt im Router unter `/home/alex/pi-guardian/router/data/pi_guardian.db`, sofern `PI_GUARDIAN_DB_PATH` nicht gesetzt ist.

## Admin-Auth

Die Admin-UI nutzt den Router-Admin-Client `Router_Admin_UI_Persistent`.

Freigegebene Routen für diesen Client:

- `/health`
- `/settings`
- `/status/service`
- `/logs`
- `/clients`
- `/agents`
- `/skills`
- `/actions`
- `/memory`

Optional nur bei realem Bedarf:

- `/route`
- `/models`
- `/models/select`

Die UI holt sich ihre Session nach Cache-Verlust per Bootstrap-Endpoint neu und nutzt dann `credentials: 'include'`.

## Auswirkung auf den Router-Dienst

- keine Änderung an den bestehenden Endpunkten
- keine Änderung an `/route`
- keine Änderung an `/health`
- keine Änderung an Modellwahl, Persistenz oder Logging-Grundstruktur
- keine Kopplung an Kids-Controller-Secrets oder Kids-Controller-Pfade

Der Dienst `pi-guardian-router.service` startet weiterhin die gleiche FastAPI-Anwendung. Die neue Agentik erweitert nur die App-Struktur.

## Log-Prüfung

Relevante Logs landen im bestehenden Logpfad:

- `/home/alex/pi-guardian/router/logs/router.log`

Suche dort nach:

- `agent_run_start`
- `agent_run_end`
- `skill_call_start`
- `skill_call_end`
- `skill_call_failed`
- `action_proposal`
- `action_proposal_denied`
- `action_execute_start`
- `action_execute_end`
- `action_execute_failed`
- `tool_call_start`
- `tool_call_end`
- `tool_call_failed`
- `agent_run_parse_error`
- `agent_run_model_error`
- `tool_call_policy_denied`
- `tool_call_limit_denied`

## Test-Endpunkte und Beispiel-Requests

### Agentenliste

```bash
curl http://127.0.0.1:8071/agents
```

Die Antwort enthält System-Agenten, Actor-Agenten und persistierte Custom-Agenten.

### Skills

```bash
curl http://127.0.0.1:8071/skills
curl http://127.0.0.1:8071/skills/system_snapshot
```

### Actions

```bash
curl http://127.0.0.1:8071/actions
curl http://127.0.0.1:8071/actions/restart_service
```

### Agentenlauf

```bash
curl -X POST http://127.0.0.1:8071/agents/run \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_name": "guardian_supervisor",
    "input": "Analysiere den Zustand des Systems",
    "max_steps": 3
  }'
```

Für `service_diagnose` ist dasselbe Schema zu verwenden, z. B.:

```bash
curl -X POST http://127.0.0.1:8071/agents/run \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_name": "service_diagnose",
    "input": "Prüfe den ollama-Dienst und priorisiere mögliche Ursachen",
    "max_steps": 3
  }'
```

Für `log_analyst` ist dasselbe Schema zu verwenden, z. B.:

```bash
curl -X POST http://127.0.0.1:8071/agents/run \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_name": "log_analyst",
    "input": "Analysiere aktuelle Router-Logs auf Fehlerbilder",
    "max_steps": 3
  }'
```

### Action-Vorschlag und Freigabe

```bash
curl -X POST http://127.0.0.1:8071/actions/propose \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_name": "service_operator",
    "action_name": "restart_service",
    "arguments": {"service_name": "pi-guardian-router"},
    "reason": "Dienst hängt"
  }'
```

```bash
curl -X POST http://127.0.0.1:8071/actions/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_name": "service_operator",
    "action_name": "restart_service",
    "arguments": {"service_name": "pi-guardian-router"},
    "approved": true
  }'
```

## Typische Fehlerquellen

- Ollama läuft nicht oder ist nicht erreichbar
- ein Skill bekommt ein ungültiges Input-Schema
- `service_status` bekommt einen nicht erlaubten Dienstnamen
- Docker ist nicht installiert oder der aktuelle Benutzer hat keinen Zugriff
- `restart_service` bekommt einen nicht erlaubten Dienstnamen
- `restart_container` ist bewusst deaktiviert
- `REQUIRE_API_KEY=true`, aber der Client hat die Route nicht freigeschaltet
- Modellantwort liefert keinen gültigen Tool-, Skill- oder Action-Call
- `max_steps` ist zu niedrig für eine vollständige Analyse
- eine Action wird ohne Freigabe angefragt

## Troubleshooting-Guide

1. Prüfe zuerst `GET /health`.
2. Prüfe `GET /status/service`.
3. Prüfe `GET /agents`.
4. Prüfe `GET /skills` und `GET /actions`.
5. Prüfe die Logs im Router-Log.
6. Prüfe, ob Ollama unter `settings.OLLAMA_BASE_URL` erreichbar ist.
7. Prüfe Docker- und systemd-Rechte, wenn Tools keine Daten liefern.
8. Prüfe, ob der Client überhaupt Zugriff auf die administrativen Routen hat.
9. Prüfe bei `log_analyst`, ob `logs/router.log` existiert und lesbar ist.
10. Prüfe bei Action-Fehlern, ob das Ziel erlaubt und die Freigabe gesetzt ist.

## Produktionshinweise

- Tool-, Skill- und Action-Ausführung sind read-only beziehungsweise streng freigesteuert.
- Die Laufzeit bricht nach `max_steps` ab.
- Zusätzliche Tool-Limits werden im Executor erzwungen.
- Action-Ausführung ist nie direkt aus dem Modell heraus erlaubt.
- Parser-Fehler werden geloggt und an den Lauf zurückgegeben.
- Fehler werden strukturiert in `AgentRunResponse.errors` gesammelt.
