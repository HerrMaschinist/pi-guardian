# Modellverwaltung Rework 2026-04-17

## Ziel
- Modellverwaltung von reiner Ollama-Liveansicht zu einer echten, persistenten Backend-Verwaltung weiterentwickeln.
- Die Oberfläche soll installierte Modelle, im Router verwendete Modelle und registrierte Modelle getrennt und nachvollziehbar zeigen.
- Erweiterungen für neue Modelle sollen über Backend-Daten und nicht über verstreute Hardcodierungen erfolgen.

## Ist-Zustand
- `GET /models` liefert aktuell nur die bei Ollama installierten Modelle.
- `POST /models/select` setzt ausschließlich `DEFAULT_MODEL` in den Laufzeit- und `.env`-Werten.
- `LARGE_MODEL` existiert im Router nur als Konstante und wird nicht über `GET /settings` oder `PUT /settings` persistent verwaltet.
- In der SQLite-Datenbank existiert bisher keine eigene Modell-Tabelle.
- Die UI der Modellseite mischt Live-Ollama-Daten mit Frontend-Env-Werten (`VITE_DEFAULT_MODEL`, `VITE_LARGE_MODEL`).

## Analyse
- Die aktuelle Modellanzeige ist nicht vollständig falsch, aber unvollständig.
- Das Backend kennt bereits die echte Laufzeitquelle der Modelle über Ollama und die echte Auswahl des Standardmodells.
- Es fehlt jedoch eine persistente Datenbasis für Modellregistrierung, Sichtbarkeit und spätere Erweiterung.
- Die UI zeigt deshalb konfigurationsgetriebene Werte aus dem Build an, statt Backend-Quelle und tatsächliche Verfügbarkeit sauber zusammenzuführen.

## Architekturentscheidung
- `GET /models` bleibt die Live-Liste der bei Ollama verfügbaren Modelle.
- Eine persistente Modellregistrierung wird im Router ergänzt.
- Die Router-Settings werden um `large_model` erweitert, damit die UI nicht mehr auf Frontend-Env-Werte angewiesen ist.
- Die Modellseite soll künftig drei Ebenen trennen:
  - installierte Modelle
  - persistent registrierte Modelle
  - aktuell im Router verwendete Modelle

## Erweiterbarkeit
- Neue Modelle sollen künftig als registrierte Einträge angelegt werden können, ohne Code an mehreren Stellen anzupassen.
- Die Registrierungsdaten sollen als zentrale Backend-Quelle dienen.
- Zusätzliche Modellrollen wie weitere Qwen- oder Ollama-Modelle sollen über Daten statt über feste UI-Konstanten abbildbar sein.

## Offener Status
- Die persistente Modellregistrierung und die UI-Anbindung sind noch umzusetzen.
- Die Download-/Pull-Funktion wird in einer separaten Phase bewertet, nachdem die Modellverwaltung strukturell sauber ist.

## Umsetzungsergebnis
- Die persistente Modellregistrierung wurde als SQLite-Tabelle `modelrecord` umgesetzt.
- Die Kernmodelle werden beim Start aus den Router-Settings in die Registry synchronisiert.
- Die Router-Settings geben jetzt auch `large_model` aus und akzeptieren Updates dafür.
- Die UI liest die Modellnamen jetzt aus dem Backend statt aus reinen Build-Variablen.
- Die Modellseite unterscheidet jetzt sauber zwischen:
  - installierten Ollama-Modellen
  - persistent registrierten Modellen
  - im Router konfigurierten Kernmodellen

## Verifikation
- Router-Tests: `10 passed`.
- Frontend-Build: erfolgreich.
- Live-Endpunkte nach Router-Neustart:
  - `GET /settings` -> `200`
  - `GET /models` -> `200`
  - `GET /models/registry` -> `200`
  - `GET /status/service` -> `200`

## Ergebnis
- Die Modellverwaltung ist jetzt auf eine echte Backend-Basis umgestellt und erweiterbar.
- Die Registry kann zusätzliche Modelle aufnehmen, ohne die UI mit weiteren Hardcodierungen zu belasten.
- Die Phase-3-Frage bleibt offen: ein kontrollierter Pull-/Download-Flow ist technisch möglich, aber noch separat zu bewerten.

## Phase 3 Entscheidung
- Ein direkter `ollama pull`-Shell-Aufruf war nicht sinnvoll, weil das CLI im laufenden System nicht im PATH verfügbar war.
- Stattdessen wurde die Ollama-HTTP-API `/api/pull` genutzt.
- Der Pull läuft asynchron als eigener Job und blockiert keine UI- oder Router-Requests.
- Nach erfolgreichem Pull wird das Modell automatisch in die Registry übernommen, damit es in der Verwaltung sichtbar bleibt.

## Phase 3 Umsetzung
- Router: neue Endpunkte `/models/pull`, `GET /models/pull`, `GET /models/pull/{id}`.
- Router: persistente Pull-Job-Tabelle `modelpulljob`.
- Router: Background-Worker aktualisiert Jobstatus, Fortschritt und Fehlertext.
- UI: eigener Pull-Dialog mit Statusliste und laufender Aktualisierung.

## Phase 3 Verifikation
- Router-Tests inklusive Pull-Job-Lifecycle: `13 passed`.
- Frontend-Build: erfolgreich.
- Live-Test:
  - `POST /models/pull` erzeugt einen Job.
  - `GET /models/pull/{id}` lieferte nacheinander `queued`, `running` und `succeeded`.
  - Der Job meldete `100 %` und einen erfolgreichen Abschluss.
  - Die Registry blieb konsistent und zeigte die verwalteten Modelle weiterhin an.

## Abschluss
- Die Modellverwaltung ist jetzt vollständig backend-gestützt.
- Neue Modelle können registriert, sichtbar gemacht und per Pull nachgeladen werden.
- Die UI bleibt getrennt vom Download-Mechanismus und steuert nur den Jobstart und die Anzeige.
