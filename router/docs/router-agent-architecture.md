# Router Agent Architecture

## 1. Ziel der Erweiterung

Der bestehende PI Guardian Model Router bleibt als lokaler FastAPI-Router für Ollama-Anfragen erhalten. Die Agentik ergänzt den Router um eine klar getrennte interne Laufzeit für mehrschrittige Analyseaufgaben, eine Skill-Schicht und eine streng begrenzte Action-Schicht.

Die ersten Ausbaustufen sind:

- `guardian_supervisor`
- `service_diagnose`
- `log_analyst`
- `service_operator`

Die ersten drei Agenten arbeiten strikt `read_only`. `service_operator` ist ein vorbereiteter Actor-Agent, der Aktionen nur vorschlägt und nie frei ausführt.

## 2. Neue Modulstruktur

- `/home/alex/pi-guardian/router/app/agents/__init__.py`
- `/home/alex/pi-guardian/router/app/agents/registry.py`
- `/home/alex/pi-guardian/router/app/agents/runtime.py`
- `/home/alex/pi-guardian/router/app/agents/prompt_builder.py`
- `/home/alex/pi-guardian/router/app/agents/tool_parser.py`
- `/home/alex/pi-guardian/router/app/skills/__init__.py`
- `/home/alex/pi-guardian/router/app/skills/base.py`
- `/home/alex/pi-guardian/router/app/skills/registry.py`
- `/home/alex/pi-guardian/router/app/skills/executor.py`
- `/home/alex/pi-guardian/router/app/skills/standard.py`
- `/home/alex/pi-guardian/router/app/actions/__init__.py`
- `/home/alex/pi-guardian/router/app/actions/base.py`
- `/home/alex/pi-guardian/router/app/actions/registry.py`
- `/home/alex/pi-guardian/router/app/actions/executor.py`
- `/home/alex/pi-guardian/router/app/actions/standard.py`
- `/home/alex/pi-guardian/router/app/tools/__init__.py`
- `/home/alex/pi-guardian/router/app/tools/base.py`
- `/home/alex/pi-guardian/router/app/tools/registry.py`
- `/home/alex/pi-guardian/router/app/tools/executor.py`
- `/home/alex/pi-guardian/router/app/tools/system_status_tool.py`
- `/home/alex/pi-guardian/router/app/tools/docker_status_tool.py`
- `/home/alex/pi-guardian/router/app/tools/service_status_tool.py`
- `/home/alex/pi-guardian/router/app/tools/router_logs_tool.py`
- `/home/alex/pi-guardian/router/app/models/agent_models.py`
- `/home/alex/pi-guardian/router/app/models/skill_models.py`
- `/home/alex/pi-guardian/router/app/models/action_models.py`
- `/home/alex/pi-guardian/router/app/models/tool_models.py`
- `/home/alex/pi-guardian/router/app/api/routes_agents.py`
- `/home/alex/pi-guardian/router/app/api/routes_skills.py`
- `/home/alex/pi-guardian/router/app/api/routes_actions.py`

Die Trennung folgt dem bestehenden Layout des Routers: Datenmodelle unter `app/models`, Routing unter `app/api`, Laufzeitlogik unter `app/agents`, Skill- und Action-Implementierungen in eigenen Schichten und technische Ausführungslogik unter `app/tools` bzw. `app/actions`.

## 3. Agentenmodell, Skill-Modell und Action-Modell

### Agentenmodell

Die Agentenmodelle sind Pydantic-Modelle und trennen klar zwischen:

- Eingaben des API-Clients
- internen Tool-Aufrufen
- Skill-Aufrufen
- Action-Vorschlägen
- Schrittprotokollen
- vollständigen Agentenläufen

Zusätzlich gibt es eine zentrale Policy-Ebene pro Agent. Sie wird zusammen mit der Agenten-Definition persistiert und zentral durchgesetzt. Die Policy umfasst:

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

### Skill-Modell

Skills sind kontrollierte, lesende Fachfunktionen über bestehenden Tools. Sie haben eine eigene Registry und einen eigenen Executor.

Erste Skills:

- `system_snapshot`
- `service_triage`
- `router_log_review`
- `docker_snapshot`
- `service_log_correlation`
- `incident_summary`
- `agent_health_check`

Skills dürfen nur die in ihrer Definition hinterlegten Tools nutzen. Sie bleiben read-only und können die Policy nicht umgehen.

### Action-Modell

Actions sind streng getrennte, potenziell wirksame Operationen. Das Modell darf sie nur vorschlagen, nie direkt ausführen. Die eigentliche Ausführung ist nur nach expliziter Freigabe und Policy-Prüfung möglich.

Erste Actions:

- `restart_service`
- `restart_container` als bewusst deaktivierte Vorbereitung
- `rerun_health_check`

Der Actor-Agent `service_operator` nutzt dieses Modell. Er ist nicht frei autonom, sondern arbeitet mit Vorschlag, Policy-Prüfung und externer Freigabe.

## 4. Laufzeitmodell

Die Laufzeit in `/home/alex/pi-guardian/router/app/agents/runtime.py` arbeitet in einer begrenzten Schleife:

1. Agent aus Registry laden
2. Modell bestimmen
3. Prompt mit System-, Benutzer-, Skill- und Action-Kontext erzeugen
4. Ollama-Aufruf ausführen
5. Tool-, Skill- oder Action-JSON prüfen und validieren
6. Tool, Skill oder Action-Vorschlag über den zentralen Executor verarbeiten
7. Observation in den Kontext zurückschreiben
8. Wiederholen bis Abschluss, Freigabeanforderung oder `max_steps`

Es gibt keinen Shell-Zugriff für den Agenten selbst. Alle Ausführungen laufen nur über die zentralen Tool-, Skill- und Action-Klassen. Die eigentliche Rechteprüfung passiert zusätzlich in den jeweiligen Executor-Schichten und nicht nur im Prompt oder in der UI.

## 5. Registrierte Agenten

### `guardian_supervisor`

- Name: `guardian_supervisor`
- Typ: `system`
- Beschreibung: read-only Analyse-Agent für System-, Docker- und Service-Status
- Erlaubte Tools:
  - `system_status`
  - `docker_status`
  - `service_status`
- Erlaubte Skills:
  - `system_snapshot`
  - `service_triage`
  - `router_log_review`
  - `docker_snapshot`
  - `incident_summary`
  - `agent_health_check`
- `read_only=True`
- `max_steps=5`
- Policy:
  - `can_use_logs=False`
  - `can_use_services=True`
  - `can_use_docker=True`
  - `can_propose_actions=False`

Der Agent darf nur zusammenfassen, priorisieren und Maßnahmen empfehlen. Er darf keine Aktionen ausführen.

## 7. Persistenz und Wiederverwendung

Die Agentik schreibt ihre operative Historie in SQLite und nutzt dafür die Router-eigene Memory-Schicht:

- Agent-Runs
- Schritte
- Tool-Calls
- Tool-Results
- Skill-Runs
- Action-Vorschläge
- Freigaben
- Action-Ausführungen
- Incidents
- Knowledge
- Feedback

Die Details dazu stehen in [`router-memory-db.md`](./router-memory-db.md).

Wichtig ist die Trennung zwischen Beobachtung und Verbesserung:

- es gibt keine Trainingspipeline
- es gibt keine Embedding-Schicht
- es gibt nur strukturierte Persistenz für spätere Wiederverwendung

## 8. Admin-Client und Auth

Der Router besitzt einen dedizierten persistenten Admin-Client für die UI:

- `Router_Admin_UI_Persistent`
- serverseitig im Router angelegt und gepflegt
- keine Kids-Controller-Abhängigkeit
- kein hardcodierter Browser-Key

Die Auth-Details stehen in [`router-admin-auth.md`](./router-admin-auth.md).

### `service_diagnose`

- Name: `service_diagnose`
- Typ: `system`
- Beschreibung: read-only Diagnose-Agent für systemd-Services und Systemzustand
- Erlaubte Tools:
  - `service_status`
  - `system_status`
- Erlaubte Skills:
  - `system_snapshot`
  - `service_triage`
  - `service_log_correlation`
- `read_only=True`
- `max_steps=5`
- Policy:
  - `can_use_logs=False`
  - `can_use_services=True`
  - `can_use_docker=False`
  - `can_propose_actions=False`

Der Agent bewertet Dienstzustände, priorisiert Probleme, benennt wahrscheinliche Ursachen und gibt nur vorsichtige Handlungsempfehlungen.

### `log_analyst`

- Name: `log_analyst`
- Typ: `system`
- Beschreibung: read-only Analyse-Agent für Router-Logs, Fehlerbilder und Muster
- Erlaubte Tools:
  - `router_logs`
  - `service_status`
  - `system_status`
- Erlaubte Skills:
  - `router_log_review`
  - `service_log_correlation`
  - `system_snapshot`
  - `service_triage`
- `read_only=True`
- `max_steps=5`
- Policy:
  - `can_use_logs=True`
  - `can_use_services=True`
  - `can_use_docker=False`
  - `can_propose_actions=False`

Der Agent analysiert definierte Router-Logs, erkennt Fehlerbilder und Muster, schätzt Priorität ein und benennt wahrscheinliche Ursachen. Freie Dateileselogik ist nicht Teil der Architektur.

### `service_operator`

- Name: `service_operator`
- Typ: `actor`
- Beschreibung: vorbereiteter read-only Actor-Agent für Service-Diagnose mit Aktionsvorschlägen
- Erlaubte Tools:
  - `system_status`
  - `service_status`
  - `router_logs`
- Erlaubte Skills:
  - `system_snapshot`
  - `service_triage`
  - `service_log_correlation`
  - `incident_summary`
  - `agent_health_check`
- Erlaubte Actions:
  - `restart_service`
  - `rerun_health_check`
- `read_only=True`
- `can_propose_actions=True`

Der Agent darf nur Aktionen vorschlagen. Die Ausführung erfolgt separat über den kontrollierten Action-Executor und nur nach Freigabe.

## 6. Registrierte Tools

### `system_status`

Liest lokale Systemwerte:

- Uptime
- Load Average / CPU-Druck
- Speicherwerte
- Disk-Nutzung
- Temperatur, wenn auf dem System verfügbar

### `docker_status`

Liest Containerzustände über `docker ps` und `docker inspect`:

- Containername
- Status
- Health
- Image

### `service_status`

Prüft nur vordefinierte sichere Dienste:

- `pi-guardian-router`
- `ollama`
- `docker`

Die Tool-Validierung verhindert freie Dienstabfragen.

### `router_logs`

Liest ausschließlich die definierten Router-Logs aus `logs/router.log` mit begrenzter Ausgabe und strikter Validierung:

- `limit` ist begrenzt
- optionale Filter für Log-Level und Teilstrings
- keine freie Dateipfad-Auswahl
- keine Schreiboperationen

## 7. Neue API-Endpunkte

- `GET /agents`
- `GET /agents/{agent_name}`
- `POST /agents/run`
- `GET /skills`
- `GET /skills/{skill_name}`
- `GET /actions`
- `GET /actions/{action_name}`
- `POST /actions/propose`
- `POST /actions/execute`

Die neuen Routen werden in `/home/alex/pi-guardian/router/app/main.py` registriert und nutzen das bestehende Authentifizierungsmodell über `authorize_protected_request`.

## 8. Sicherheitsgrenzen des read-only Agenten

- keine freie Shell
- keine Schreiboperationen
- keine Dienst-Neustarts ohne Action-Freigabe
- keine Container-Änderungen
- keine unregistrierten Tools
- keine nicht freigegebenen Skills
- keine nicht freigegebenen Actions
- keine direkte Action-Ausführung durch das Modell
- keine Policy-Änderung für System-Agenten über UI oder API
- keine Rechteaufweichung an der UI vorbei

Die zentrale Tool-, Skill- und Action-Schicht erzwingt diese Grenzen zusätzlich zur Prompt-Disziplin.

## 9. Wiederverwendete Router-Komponenten

- `/home/alex/pi-guardian/router/app/router/ollama_client.py`
  - bestehender Ollama-Call für Modellaufrufe
- `/home/alex/pi-guardian/router/app/router/classifier.py`
  - bestehende Modellwahl-Heuristik
- `/home/alex/pi-guardian/router/app/router/auth.py`
  - bestehende Zugangskontrolle
- `/home/alex/pi-guardian/router/app/router/settings_manager.py`
  - bestehende `.env`-Persistenz und Laufzeitkonfiguration
- `/home/alex/pi-guardian/router/app/router/system_status.py`
  - wird im Service-Status-Tool für den Router selbst wiederverwendet
- `/home/alex/pi-guardian/router/app/main.py`
  - bestehende FastAPI-App und Logging-Konfiguration

## 10. Codebase-Konventionen

- Pydantic für Input- und Statusmodelle
- `extra="forbid"` für kontrollierte Schemas
- Type-Hints überall dort, wo Daten zwischen Modulen wandern
- Logging über `logging.getLogger(__name__)`
- Fehler werden nicht verschluckt, sondern strukturiert zurückgegeben und zusätzlich geloggt
- keine neuen Altpfade außerhalb `/home/alex/pi-guardian/router`

## 11. Offene Grenzen für spätere Ausbaustufen

- weitere read-only Skills
- weitere Actions mit Approval-Flow
- feinere Rechte auf Skill- oder Action-Ebene
- persistente Skill- oder Action-Konfiguration für Custom-Erweiterungen
- Chat-/Streaming-API für Agenten
- persistente Agenten-Historie
- stärkere Modellvalidierung gegen aktive Ollama-Modelle
