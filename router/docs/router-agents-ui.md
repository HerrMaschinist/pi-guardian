# Router Agents UI

## 1. UI-Integrationspunkt

- Der neue Hauptmenüpunkt `Agenten` ist in der bestehenden Sidebar der PI Guardian UI integriert.
- Die UI bleibt ein einziger Admin-Client unter `/home/alex/pi-guardian/ui` und erweitert die vorhandene lokale Page-Navigation um eine eigene Agentenansicht.
- Die Agentenansicht arbeitet direkt gegen den Router unter `127.0.0.1:8071` über die bestehende API-Service-Schicht.

## 2. Neue Dateien und Pfade

- `/home/alex/pi-guardian/ui/src/pages/Agents.tsx`
- `/home/alex/pi-guardian/ui/src/api/client.ts`
- `/home/alex/pi-guardian/ui/src/components/Sidebar.tsx`
- `/home/alex/pi-guardian/ui/src/App.tsx`
- `/home/alex/pi-guardian/ui/src/styles.css`
- `/home/alex/pi-guardian/router/docs/router-agents-ui.md`

## 3. Neue oder erweiterte API-Endpunkte

- `GET /agents`
- `GET /agents/{agent_name}`
- `GET /agents/{agent_name}/settings`
- `POST /agents`
- `PUT /agents/{agent_name}`
- `PUT /agents/{agent_name}/settings`
- `POST /agents/{agent_name}/enable`
- `POST /agents/{agent_name}/disable`
- `DELETE /agents/{agent_name}`
- `POST /agents/run`

## 4. Konfigurierbare Agent-Settings

- `active`
- `preferred_model`
- `max_steps`
- `timeout_seconds`
- `behavior.analysis_mode`
- `behavior.response_depth`
- `behavior.prioritization_style`
- `behavior.uncertainty_behavior`
- `behavior.risk_sensitivity`
- `personality.style`
- `personality.tone`
- `personality.directness`
- `personality.verbosity`
- `personality.technical_strictness`
- `custom_instruction`

## 5. Bewusst nicht frei konfigurierbare Grenzen

- `read_only` bleibt technisch erzwungen.
- `guardian_supervisor` ist ein System-Agent und kann nicht frei gelöscht werden.
- Der Agent hat nur die read-only Tools `system_status`, `docker_status` und `service_status`.
- Shell-Zugriffe, Schreibvorgänge, Dienständerungen und Containeränderungen sind weder in der UI noch im Backend freigeschaltet.

## 6. Testläufe in der UI

- Die Testlauf-Ansicht nutzt `POST /agents/run`.
- Der Benutzer wählt einen Agenten aus, gibt einen Prompt ein und kann optional `preferred_model` und `max_steps` überschreiben.
- Die Antwort zeigt `final_answer`, `steps`, `tool_calls`, `used_model` und `errors`.

## 7. Persistenz

- Custom-Agenten und ihre Aktiv-/Konfigurationsdaten werden im Router persistent gespeichert.
- Die Persistenz ist dateibasiert und liegt unter `/home/alex/pi-guardian/router/data/agents.json`.
- System-Agenten werden weiterhin aus dem Code geladen und werden durch die Persistenz nur ergänzt, nicht ersetzt.
- Beim Router-Start werden System-Agenten und persistierte Custom-Agenten zusammengeführt.

## 8. Aktivieren, Deaktivieren, Anlegen, Bearbeiten, Löschen

- Aktivieren und Deaktivieren werden über die neuen Router-Endpunkte unmittelbar sichtbar.
- Anlegen, Bearbeiten und Löschen laufen in der UI als echte API-Operationen mit Fehleranzeige und Sicherheitsabfrage beim Löschen.
- System-Agenten sind vor Löschung geschützt.
- Custom-Agenten lassen sich vollständig verwalten, solange die Backend-Validierung eingehalten wird.

## 9. Trennung zwischen System-Agenten und Custom-Agenten

- System-Agenten sind im Backend als `agent_type=system` markiert.
- Custom-Agenten werden als `agent_type=custom` gespeichert.
- Die UI zeigt diese Unterscheidung explizit an.
- System-Agenten dürfen nur innerhalb der freigegebenen Grenzen geändert werden.
- Custom-Agenten sind vollständig verwaltbar, aber weiterhin an die read-only Tool-Grenze gebunden.
