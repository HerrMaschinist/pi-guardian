# UI Direction Rework 2026-04-17

## Zielbild

Die Admin-Oberfläche soll als technische Leitwarte wirken, nicht wie ein generisches AI-SaaS-Dashboard mit Prompt-Box im Zentrum.

## Beobachtete AI-Dashboard-Muster

Vor der Änderung waren vor allem diese Muster sichtbar:

- Diagnose primär als Prompt-Demo statt als Ausführungskonsole
- History primär als allgemeine Request-Liste statt als Audit-Ansicht
- Dashboard eher als statische Statuskarten-Sammlung statt als Routing-/System-Panel

## Richtungsentscheidung

Die UI wurde nicht kosmetisch neu erfunden, sondern entlang des neuen Produktkerns ausgerichtet:

- mehr Execution-/Policy-/Audit-Sichtbarkeit
- weniger generisches Prompt-Senden
- stärkere Benennung entlang technischer Rollen:
  - `Route Console`
  - `Route Channel`
  - `Execution History`
  - `Execution Lanes`

## Konkrete Änderungen

- Dashboard zeigt jetzt die verfügbaren Execution-Lanes statt nur Feature-Aufzählung.
- Diagnose zeigt jetzt:
  - `execution_mode`
  - `decision_classification`
  - `policy_trace`
  - tatsächliche `tool_executions`
- History zeigt jetzt zusätzlich:
  - Decision-Lane
  - Execution-Mode
  - tatsächlich ausgeführte Tools

## Stilentscheidung

Die bestehende dunkle, technische Richtung wurde beibehalten, aber in Richtung Instrumentierung verschoben:

- neue `trace-list`-Darstellung für Policy-/Execution-Zustände
- kompaktere Ergebnisraster statt bloßer Demo-KV-Paare
- stärkere Begriffe aus Kontrollraum/Operations-Kontext statt AI-Marketing-Sprache

## Bewusst nicht getan

- kein großflächiger Branding-Pass
- keine dekorativen Neon-/Gradienten-Spielereien
- keine neue Design-Sprache, die vom bestehenden System abweicht
- keine Verschiebung von Entwicklungszeit aus dem Kernpfad in reines UI-Theater
