# Router Memory DB

## Zweck

Die Router-Laufzeit speichert Agentenläufe, Tool-Nutzung, Skills, Actions, Incidents, Knowledge und Feedback persistent in SQLite.

Das Ziel ist keine Trainingspipeline, sondern eine belastbare operative Basis für:

- Wiederverwendung früherer Läufe
- spätere Incident-Korrelation
- bestätigte Muster
- menschliches Feedback
- Freigabe- und Ausführungsnachverfolgung

## Datenbankpfad

- Standardpfad: `/home/alex/pi-guardian/router/data/pi_guardian.db`
- Überschreibbar über `PI_GUARDIAN_DB_PATH`

Der Router verwendet seine eigene DB-Datei. Es gibt keine Abhängigkeit auf ` /etc/kids_controller` oder andere Kids-Controller-Pfade.

## Verwendete Technik

- SQLite als primäre Persistenz
- SQLModel / SQLAlchemy im bestehenden Router-Stil
- Tabellenanlage über `SQLModel.metadata.create_all(...)`
- vorhandene Daten werden beim Initialisieren ergänzt, nicht blind gelöscht

## Persistierte Kernobjekte

- `agents`
- `agent_settings`
- `agent_runs`
- `agent_steps`
- `tool_calls`
- `tool_results`
- `skills`
- `skill_runs`
- `actions`
- `action_proposals`
- `action_executions`
- `approvals`
- `incidents`
- `incident_findings`
- `knowledge_entries`
- `feedback_entries`

## Gespeicherte Mindestfelder

### agents

- `agent_name`
- `agent_type`
- `enabled`
- `read_only`
- `created_at`
- `updated_at`

### agent_settings

- `agent_name`
- `preferred_model`
- `max_steps`
- `timeout_seconds`
- `behavior`
- `personality`
- `policy`
- `custom_instruction`
- `created_at`
- `updated_at`

### agent_runs

- `run_id`
- `agent_name`
- `input`
- `used_model`
- `success`
- `final_answer`
- `started_at`
- `finished_at`

### agent_steps

- `run_id`
- `step_number`
- `action_type`
- `observation`
- `raw_payload`

### tool_calls

- `run_id`
- `step_number`
- `tool_name`
- `arguments`
- `reason`
- `created_at`

### tool_results

- `run_id`
- `step_number`
- `tool_name`
- `success`
- `output`
- `error`
- `created_at`

### incidents

- `title`
- `summary`
- `severity`
- `status`
- `created_at`
- `updated_at`

### incident_findings

- `incident_id`
- `source_type`
- `source_ref`
- `finding_type`
- `content`
- `confidence`

### knowledge_entries

- `title`
- `pattern`
- `probable_cause`
- `recommended_checks`
- `recommended_actions`
- `confidence`
- `confirmed`
- `source`
- `created_at`
- `updated_at`

### feedback_entries

- `related_run_id`
- `related_incident_id`
- `verdict`
- `comment`
- `created_by`
- `created_at`

## Datenfluss

### Agentenlauf

1. Runtime erstellt oder erhält `run_id`
2. Schritte werden mit strukturiertem `raw_payload` gespeichert
3. Tool-Calls und Tool-Results werden separat gespeichert
4. Skill-Runs werden als eigene Zeilen gespeichert
5. Finale Antwort und Erfolgscode landen im Run-Datensatz

### Action-Flow

1. Aktion wird vorgeschlagen
2. Vorschlag bekommt `proposal_id`
3. Freigabe wird in `approvals` gespeichert
4. Ausführung wird in `action_executions` gespeichert

### Incident-Flow

1. Incident anlegen
2. Findings anhängen
3. Status und Bezug zu Runs pflegen

### Knowledge-Flow

1. Bestätigte oder beobachtete Muster als Knowledge-Entry speichern
2. Quelle und Confidence dokumentieren
3. Spätere Wiederverwendung vorbereiten

### Feedback-Flow

1. Feedback an Run oder Incident binden
2. Verbalen Befund und Autor speichern
3. Spätere Auswertung vorbereiten

## Wiederverwendung

Die DB ist für strukturierte Wiederverwendung vorbereitet:

- ähnliche Runs
- offene Incidents
- bestätigte Knowledge-Entries
- letztes Feedback zu vergleichbaren Fällen

Es gibt absichtlich noch keine Embeddings, keine semantische Suche und keine Trainingspipeline.

## Migration

Beim Start werden vorhandene Referenzdaten und Agenten-/Action-/Skill-Definitionen in die SQLite-Basis übernommen.

Übernommen werden, sofern vorhanden:

- Agenten-Definitionen
- Agenten-Settings
- Skill-Definitionen
- Action-Definitionen
- vorhandene Run-Historien
- vorhandene Knowledge- oder Feedback-Strukturen
- vorhandene Incident-Strukturen

Nicht übernommen oder neu erfunden wird nichts, was im Bestand nicht real vorhanden ist.

