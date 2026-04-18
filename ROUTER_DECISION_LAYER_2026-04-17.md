# Router Decision Layer 2026-04-17

## Ziel

Der Router soll Requests nicht mehr nur direkt auf ein Modell werfen, sondern vor der Ausführung strukturiert entscheiden, welche Art Anfrage vorliegt und welcher Ausführungspfad grundsätzlich zulässig oder notwendig ist.

## Ausgangslage

- `/route` hat bisher Modellwahl, Fairness und Ollama-Aufruf in einem linearen Ablauf kombiniert.
- Es gab keine explizite Entscheidungsrepräsentation.
- Tool-System und Request-Pfad waren technisch vorhanden, aber nicht über eine eigene Routing-Entscheidung verbunden.

## Architekturentscheidung

Die erste Produkt-Ausbaustufe führt einen eigenen Decision-Layer unter
`/home/alex/pi-guardian/router/app/router/decision/` ein.

Bausteine:

- `models.py`
  - interner Vertrag für `RequestClassification` und `RequestDecision`
- `classifier.py`
  - erste heuristische Klassifikation
- `service.py`
  - klarer Einstieg für spätere Erweiterungen

## Aktuelle Klassifikationen

- `llm_only`
- `tool_required`
- `internet_required`
- `blocked`

## Aktuelle Wirkung

- `llm_only`
  - Request darf normal über das Modell laufen
- `tool_required`
  - Tool-Bedarf wird erkannt und im Response/Audit markiert
  - für ausgewählte read-only Tools erfolgt jetzt echte kontrollierte Ausführung im normalen `/route`-Pfad
- `internet_required`
  - Web-Bedarf wird erkannt und im Response/Audit markiert
  - echter Web-Layer bleibt bewusst später; Requests enden kontrolliert als `internet_execution_unavailable`
- `blocked`
  - Request wird vor der Modellausführung mit `403` abgebrochen

## Audit

Die Entscheidung wird jetzt in `routehistory` mitgeschrieben:

- `decision_classification`
- `decision_reasons`
- `decision_tool_hints`
- `decision_internet_hints`
- `policy_trace`
- `execution_mode`
- `execution_status`
- `executed_tools`
- `tool_execution_records`
- `execution_error`

Damit ist die vorgelagerte Routing-Entscheidung erstmals nachvollziehbar.

## Client-Policy-Grundlage

Zusätzlich wurden minimale Client-Fähigkeiten eingeführt:

- `can_use_llm`
- `can_use_tools`
- `can_use_internet`

Diese Fähigkeiten werden über eine eigene Policy-Schicht auf die Decision-Ergebnisse angewendet.

Konsequenz:

- Ein Request kann nicht nur durch Inhalt, sondern auch durch Client-Rechte blockiert werden.
- Damit ist eine zweite, produktfähigere Ebene neben der bisherigen Route-Auth vorhanden.

## Warum das auf spätere Produktisierung einzahlt

- HTTP-Transport bleibt von der Entscheidungsschicht getrennt.
- Entscheidung, Policy und Ausführung sind als eigene Verantwortlichkeiten erkennbar.
- Tool- und Web-Layer können später hinter dieselbe Entscheidungsrepräsentation gehängt werden.
- Die interne Struktur ist damit eher domänengetrieben als route-getrieben.

## Noch bewusst nicht umgesetzt

- echtes Tool-Orchestrierungs-Subsystem für normale `/route`-Anfragen
- produktiver Web-Layer
- feinere Risk-/Policy-Matrix
- eigene dedizierte Decision- oder Policy-History-Tabellen
- komplexes Job- oder Workflow-System
