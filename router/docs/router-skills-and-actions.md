# Router Skills and Actions

## Zweck

Diese Seite dokumentiert die getrennte Skill- und Action-Schicht des PI Guardian Routers. Skills sind lesende, strukturierte Fachbausteine. Actions sind strikt freigesteuerte, potenziell wirksame Operationen.

## Skill-Architektur

Skills leben in:

- `/home/alex/pi-guardian/router/app/skills/base.py`
- `/home/alex/pi-guardian/router/app/skills/registry.py`
- `/home/alex/pi-guardian/router/app/skills/executor.py`
- `/home/alex/pi-guardian/router/app/skills/standard.py`

Jeder Skill besitzt:

- `name`
- `description`
- `allowed_tools`
- `input_schema`
- `output_schema`
- `read_only`
- `version`
- `execute()`

Skills dürfen nur die Tools nutzen, die explizit in ihrer Definition und zusätzlich in der Agent-Policy erlaubt sind.

## Registrierte Skills

- `system_snapshot`
- `service_triage`
- `router_log_review`
- `docker_snapshot`
- `service_log_correlation`
- `incident_summary`
- `agent_health_check`

## Skill-Zuordnung zu Agenten

### `guardian_supervisor`

- `system_snapshot`
- `service_triage`
- `router_log_review`
- `docker_snapshot`
- `incident_summary`
- `agent_health_check`

### `service_diagnose`

- `system_snapshot`
- `service_triage`
- `service_log_correlation`

### `log_analyst`

- `router_log_review`
- `service_log_correlation`

### `service_operator`

- `system_snapshot`
- `service_triage`
- `service_log_correlation`
- `incident_summary`
- `agent_health_check`

## Skill-Ausführung

Die Skill-Ausführung wird zentral über den Skill-Executor gesteuert. Der Executor validiert:

- Skill-Name
- Eingabeschema
- Erlaubnis in der Agent-Policy
- Lesbarkeit der zugrunde liegenden Tools

Skill-Outputs sind strukturierte Pydantic-Daten und damit testbar.

## Action-Architektur

Actions leben in:

- `/home/alex/pi-guardian/router/app/actions/base.py`
- `/home/alex/pi-guardian/router/app/actions/registry.py`
- `/home/alex/pi-guardian/router/app/actions/executor.py`
- `/home/alex/pi-guardian/router/app/actions/standard.py`

Jede Action besitzt:

- `name`
- `description`
- `allowed_targets`
- `requires_approval`
- `read_only = false`
- `execute()`

Actions werden nicht direkt vom Modell ausgeführt. Das Modell kann nur einen Vorschlag erzeugen. Die tatsächliche Ausführung läuft nur nach Policy-Prüfung und expliziter Freigabe.

## Registrierte Actions

- `restart_service`
- `restart_container`
- `rerun_health_check`

## Action-Policies

Der Action-Executor erzwingt zentral:

- Action-Existenz
- aktive Registrierung
- erlaubte Zielwerte
- Agent-Berechtigung
- Freigabezustand

System-Agenten können Action-Rechte nicht über UI oder API ausweiten.

## Actor-Agent `service_operator`

`service_operator` ist der erste vorbereitete Actor-Agent. Er darf:

- Service-Probleme einordnen
- eine sichere Standardaktion vorschlagen
- eine Begründung liefern

Er darf nicht:

- frei shellen
- frei schreiben
- ungeprüft Aktionen ausführen
- Container- oder systemweite Änderungen anstoßen

Die UI zeigt vorgeschlagene Actions an, markiert die Freigabe als erforderlich und gibt die Ausführung erst nach expliziter Bestätigung frei.

## Freigabemodell

1. Modell erzeugt einen Action-Vorschlag.
2. Der Parser validiert Name, Target und Argumente.
3. Der Action-Executor prüft die Policy.
4. Ohne Freigabe erfolgt keine Ausführung.
5. Erst nach Freigabe wird die Action ausgeführt.

## Sicherheitsgrenzen

- keine freie Shell
- keine freien Schreibzugriffe
- keine unkontrollierten systemd-Aktionen
- keine unkontrollierten Docker-Aktionen
- keine Umgehung über UI oder API
- keine Action-Ausführung nur aufgrund einer Modellantwort

