# Productization Prep 2026-04-17

## Fokus

Die Änderungen dieser Phase verschieben PI Guardian nicht kosmetisch, sondern strukturell in Richtung eines belastbaren Produktkerns.

## Modulgrenzen

Die Request-Pipeline ist jetzt klarer in Schichten aufgeteilt:

- HTTP/API:
  - `router/app/main.py`
- Decision:
  - `router/app/router/decision/*`
- Policy:
  - `router/app/router/policy.py`
- Route-Execution:
  - `router/app/router/execution/*`
- Tool-Laufzeit:
  - `router/app/tools/*`
- Audit/Persistenz:
  - `router/app/router/history.py`
  - `router/app/models/route_history.py`

## Warum das produktionsnäher ist

- Der normale `/route`-Pfad besitzt jetzt einen echten Switch zwischen LLM-, Tool- und Internet-Pfad.
- Tool-Ausführung ist nicht mehr implizit an Agenten gebunden.
- Policy ist am Ausführungspfad sichtbar beteiligt.
- Audit speichert nicht mehr nur „Request lief“, sondern den tatsächlichen Entscheidungspfad.

## Reversibilität

Die Änderungen sind absichtlich reversibel und klein gehalten:

- keine Big-Bang-Umschreibung
- keine neue generische Workflow-Engine
- keine Auflösung bestehender Schichten
- Wiederverwendung des vorhandenen `ToolExecutor`

## Vorbereitung auf spätere Schritte

Die neue Struktur erleichtert später:

- einen separaten Web-/Internet-Executor
- feinere Tool-Policies pro Client
- explizite Tool-Rollen statt globaler Tool-Freigaben
- alternative Persistenz/Audit-Backends
- spätere Extraktion von Execution- oder Decision-Schichten

## Bewusst aufgeschoben

- Job-System für Tool-/Web-Workflows
- Streaming-Rework
- asynchrone Multi-Step-Tool-Strategien
- nicht-read-only Tool-Pfade
- vollständige Portierung oder Re-Implementierung
