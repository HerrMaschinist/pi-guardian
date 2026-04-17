# Agent Activity Rework 2026-04-17

## Ziel
- Die Agentenansicht soll mehr als reine Registry-Metadaten zeigen.
- Sichtbar sein sollen echte letzte Aktivität, letzter Status, verwendetes Modell und letzter Laufzeitpunkt.
- Keine Mock- oder Fake-Live-Anzeige, sondern belastbare Snapshot-Daten aus dem Backend.

## Ausgangslage
- `/agents` lieferte bisher nur die Agent-Definitionen aus der Registry.
- Echte Laufdaten lagen separat in der Memory-Persistenz (`agentrunrecord`), wurden aber nicht an die Agentenansicht gekoppelt.
- Die UI konnte deshalb nur `aktiv/inaktiv` und statische Settings anzeigen.

## Ursache
- Backend und UI nutzten zwei getrennte Informationsschichten:
  - Registry für Definitionen
  - Memory für echte Agent-Läufe
- Die Agenten-API führte beides nicht zusammen.

## Architekturentscheidung
- Kein zweiter UI-only Datenpfad.
- Kein Pseudo-Streaming.
- Stattdessen werden `/agents` und `/agents/{name}` serverseitig mit einer kleinen Aktivitäts-Zusammenfassung aus den neuesten Memory-Runs angereichert.

## Betroffene Dateien
- `/home/alex/pi-guardian/router/app/agents/activity.py`
- `/home/alex/pi-guardian/router/app/api/routes_agents.py`
- `/home/alex/pi-guardian/router/app/models/agent_models.py`
- `/home/alex/pi-guardian/router/tests/test_agent_activity.py`
- `/home/alex/pi-guardian/ui/src/types/index.ts`
- `/home/alex/pi-guardian/ui/src/pages/Agents.tsx`

## Umsetzung
- Neue Hilfslogik erstellt, die den neuesten Run pro Agent aus `AgentRunRecord` bestimmt.
- `/agents` und `/agents/{name}` geben jetzt optional ein Feld `activity` zurück.
- Enthalten sind:
  - `last_run_id`
  - `last_run_at`
  - `last_status`
  - `last_model`
  - `last_activity`
  - `last_result_preview`
  - `last_duration_ms`
- Die Agenten-UI nutzt diese Daten jetzt direkt:
  - zusätzliche Aktivitätsübersicht
  - letzte Aktivität pro Agent in der Liste
  - Detailbereich mit letztem Run, letzter Aufgabe und letztem Ergebnis
  - optionaler Auto-Refresh im 15-Sekunden-Takt

## Testablauf
- Router-Tests:
  - `test_agent_activity.py`
  - `test_agent_models.py`
  - `test_agent_registry.py`
  - `test_memory_service.py`
- Frontend-Build:
  - `npm run build` in `/home/alex/pi-guardian/ui`
- Live-Verifikation:
  - `GET /agents` mit Admin-Key
  - `GET /agents/guardian_supervisor` mit Admin-Key

## Ergebnis
- Die Agentenansicht kann jetzt echte letzte Läufe und Aktivitäten anzeigen.
- Die Daten basieren auf echter Persistenz, nicht auf Schätzungen.
- Das UI bleibt bewusst snapshot-basiert und stabil statt künstlich live zu wirken.

## Offener Reststatus
- Die Laufzeitberechnung ist aktuell nur dann sinnvoll gefüllt, wenn Start- und Endzeit unterschiedlich sind; sehr kurze historische Testläufe ergeben teils `0 ms`.
- Es gibt weiterhin kein Event-Streaming für Agentenaktivität; das ist bewusst nicht Teil dieser Phase.
