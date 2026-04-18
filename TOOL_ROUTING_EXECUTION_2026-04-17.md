# Tool Routing Execution 2026-04-17

## Ziel

Der normale `/route`-Pfad soll `tool_required` nicht mehr nur markieren, sondern in einem kleinen, kontrollierten Produktpfad wirklich ausführen können.

## Ausgangszustand

- `RequestDecision` konnte bereits `tool_required` liefern.
- Der normale Router-Pfad ignorierte diese Entscheidung operativ und ging immer in die LLM-Ausführung.
- Eine echte Tool-Ausführung existierte nur im Agenten-System über:
  - `app/tools/registry.py`
  - `app/tools/executor.py`
  - `app/models/tool_models.py`

## Architekturentscheidung

Es wurde kein zweites Tool-System gebaut.

Stattdessen nutzt der normale `/route`-Pfad jetzt dieselbe technische Ausführungsschicht wie die Agenten, aber mit einem eigenen, deutlich kleineren Route-Orchestrator unter:

- `router/app/router/execution/models.py`
- `router/app/router/execution/service.py`

Diese Route-Execution-Schicht übernimmt:

- kontrollierte Auswahl tatsächlich verdrahteter Route-Tools
- Aufbau eines kleinen, read-only Policy-Kontexts
- Aufruf des bestehenden `ToolExecutor`
- strukturierte Rückgabe der Tool-Resultate an Response und Audit

## Aktuell verdrahtete Route-Tools

Der normale `/route`-Pfad führt bewusst nur diese zwei Tool-Typen aus:

- `system_status`
- `service_status`

Nicht verdrahtet im normalen `/route`-Pfad bleiben vorerst:

- `docker_status`
- `router_logs`
- alles mit Mehrschritt-Orchestrierung
- alles mit Schreibrechten

## Warum diese Auswahl

- `system_status` ist parameterlos und stabil read-only.
- `service_status` ist klar begrenzt auf sichere, vordefinierte Services.
- Beide liefern kleine, strukturierte Outputs ohne Log- oder Datenflut.
- Damit entsteht ein belastbarer Produktkern statt einer vorschnellen Tool-Sammlung.

## Execution-Flow

1. `/route` klassifiziert den Request.
2. Client-Policy wird auf die Entscheidung angewendet.
3. Bei `tool_required` erzeugt die neue Route-Execution-Schicht einen kleinen Tool-Plan.
4. Nur verdrahtete Tools gelangen in die Ausführung.
5. Die Ausführung läuft über `ToolExecutor`.
6. Das Ergebnis wird:
   - in `RouteResponse` zurückgegeben
   - in `routehistory` auditierbar gespeichert

## Response-Vertrag

`RouteResponse` enthält jetzt zusätzlich:

- `execution_mode`
- `policy_trace`
- `tool_executions`
- `execution_error`

Damit sieht der aufrufende Client nicht mehr nur eine Textantwort, sondern den tatsächlichen Ausführungspfad.

## Audit-Vertrag

`routehistory` speichert jetzt zusätzlich:

- `policy_trace`
- `execution_mode`
- `execution_status`
- `executed_tools`
- `tool_execution_records`
- `execution_error`

Damit ist end-to-end sichtbar:

- welche Entscheidung getroffen wurde
- welche Policy galt
- welche Tools wirklich liefen
- ob sie erfolgreich waren
- welche strukturierten Resultate zurückkamen

## Internet-Pfad

`internet_required` ist jetzt kein stilles Halluzinations-Weiterreichen mehr.

Stattdessen gilt:

- die Entscheidung wird erkannt
- der Pfad wird im Audit als `internet_pending` markiert
- der Request endet kontrolliert mit `internet_execution_unavailable`

Das verhindert eine architektonische Sackgasse und reserviert denselben Execution-Rahmen für einen späteren Web-Layer.

## Bewusst nicht umgesetzt

- autonomes Tool-Chaining
- dynamische Tool-Auswahl über LLM im normalen `/route`-Pfad
- produktiver Web-/Internet-Zugriff
- nicht-lesende Tools
- große generische Tool-Abstraktionen ohne echten Nutzen
