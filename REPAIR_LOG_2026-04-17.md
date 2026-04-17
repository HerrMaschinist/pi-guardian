# PI Guardian Repair Log

Date: 2026-04-17

## Ausgangslage
- Projekt wurde aus einem früheren Restore-Zustand wiederhergestellt.
- Verdacht auf Mischstand aus altem Frontend-Build, Router-Code und Konfiguration.

## Aktuelle Symptome
- Agents-Seite leer.
- Memory-Seite leer.
- Dienststatus zeigt keine Backend-Werte für System, Uptime und PID.
- Nur das 1.5B Modell ist sichtbar; das 3B Modell fehlt.

## Analyse-Schritte
- Projektstruktur geprüft und zwei getrennte Frontend-Bäume gefunden: `ui/` als nginx-Root und `router/src/` als legacy Kopie.
- Systemd-Unit und Router-Logs geprüft: Router läuft über uvicorn auf Port `8071`.
- nginx-Konfiguration geprüft: `/home/alex/pi-guardian/ui/dist` wird ausgeliefert und `/api/` auf `127.0.0.1:8071` proxied.
- Router-Datenbank geprüft: Agenten-, Skill-, Action- und Laufzeitdaten sind vorhanden.
- Backend-Schemas geprüft: `/route` erwartet `prompt`, `preferred_model`, `stream`; `/status/service` liefert echte Systemwerte; `/memory` liefert Run-Snapshots und Incident-/Knowledge-/Feedback-Daten.
- Frontend-Dateien geprüft: Dashboard, Models, Settings und Memory enthalten noch Platzhalter oder nutzen ältere Request-/Response-Formate.

## Wesentliche Befunde
- Das Deploy-Frontend in `ui/dist` war nicht defekt als Build-Artefakt, sondern spiegelte den vorhandenen Source-Stand mit Platzhaltern wider.
- `ui/src/pages/Dashboard.tsx` zeigt den Dienststatus nur als statischen Platzhalter.
- `ui/src/pages/Models.tsx` nutzt eine Mock-Modellliste und sendet für `/route` ein altes Request-Format.
- `ui/src/pages/Diagnostics.tsx` sendet ebenfalls das alte `/route`-Format.
- `ui/src/pages/History.tsx` liest History-Felder aus einem alten Schema und zeigt deshalb unvollständige Inhalte.
- `ui/src/pages/Memory.tsx` bindet die eigentliche Memory-API nicht an und zeigt nur Agenten-/Skill-/Action-Snapshots plus lokale Browser-Notizen.
- `ui/.env` enthält noch `VITE_ROUTER_PORT=8070`, obwohl der Router auf `8071` läuft.
- Die Router-Datenbank enthält 4 Agenten, 7 Skills und 3 Actions; die Leere ist also kein reines Backend-Datenproblem.
- Die geschützten Router-Routen waren vom aktuellen Browser-Client nicht erreichbar, weil der UI-Initialflow den Admin-Bootstrap nicht zuverlässig auslöst.
- Der Router besitzt zwar einen persistenten Admin-Client mit `/memory` und `/models`, aber ohne Bootstrap-Session landete der Browser auf einem eingeschränkten Client-Pfad.

## Durchgeführte Änderungen
- `ui/.env`: Router-Port auf `8071` korrigiert und `VITE_LARGE_MODEL=qwen2.5-coder:3b` ergänzt.
- `ui/src/config.ts`: Frontend-Konfiguration um `largeModel` ergänzt.
- `ui/src/types/index.ts`: Request-, Response- und Status-Typen an die echten Router-Schemas angepasst.
- `ui/src/api/client.ts`: Memory-Endpoints ergänzt, Settings-Antworttyp korrigiert und Auth-Retry nach `401/403` eingebaut.
- `ui/src/App.tsx`: Admin-Bootstrap beim App-Start angestoßen.
- `ui/src/pages/Dashboard.tsx`: echten Dienststatus statt Platzhalterdaten eingebunden.
- `ui/src/pages/Models.tsx`: echte Modellliste und echte Route-Antworten eingebunden.
- `ui/src/pages/Diagnostics.tsx`: Route-Aufrufe auf das aktuelle Backend-Format umgestellt.
- `ui/src/pages/History.tsx`: History-Rows auf die aktuellen Backend-Felder umgestellt.
- `ui/src/pages/Memory.tsx`: Memory-Ansicht auf echte Runs, Incidents, Knowledge und Feedback umgestellt.
- `ui/src/pages/Settings.tsx`: Live-Settings-Load/Save gegen den Router aktiviert.
- `ui/src/pages/Agents.tsx`: verschachtelte Agent-Settings lesbar zusammengefasst.
- `ui/src/pages/Clients.tsx`: Typinkonsistenz bei `id` behoben, damit der Build wieder sauber durchläuft.

## Warum diese Änderungen nötig waren
- Die UI und das Router-Backend liefen nach dem Restore mit unterschiedlichen Verträgen: einige Seiten erwarteten alte Request-/Response-Formate oder zeigten statische Platzhalter.
- Der Router liefert für `/models` und `/memory` nur dann Daten, wenn die Admin-Session korrekt gebootstrapped ist und der richtige Client mit ausreichenden Routen verwendet wird.
- Ohne den Bootstrap-Flow blieb die UI in einem Zustand, in dem die geschützten Seiten leer wirkten, obwohl Backend-Daten vorhanden waren.

## Testergebnisse
- Frontend-Build erfolgreich mit `npm run build` im Verzeichnis `/home/alex/pi-guardian/ui`.
- `GET /health` liefert `{"status":"ok"}`.
- Mit Browser-ähnlicher IP und Bootstrap-Session liefert `GET /models` die Modelle `qwen2.5-coder:3b` und `qwen2.5-coder:1.5b`.
- Mit derselben Session liefert `GET /memory` echte Run-Snapshots statt leerer Antworten.
- Mit derselben Session liefern auch `GET /agents` und `GET /history?limit=3` echte Backend-Daten.
- `GET /status/service` liefert echte Backend-Werte für Service, Laufzeit und PID.
- Router-Dienst läuft weiter aktiv über systemd und uvicorn auf Port `8071`.
- `journalctl -u pi-guardian-router.service -n 20 --no-pager` zeigt nach dem Fix 200er-Antworten für `auth/bootstrap`, `models`, `memory`, `status/service`, `agents` und `history`.

## Offener Reststatus
- Der Container-Testzugriff auf `127.0.0.1` ohne Browser-IP scheitert weiterhin an der IP-Berechtigung; das ist für die reale Browser-Nutzung kein Fehler, sondern Teil der Router-Policy.
- Die Bootstrap-Session muss aus dem Browser heraus aufgebaut werden; die UI stößt das nun automatisch an.
- Falls später ein anderer LAN-Client dieselbe Oberfläche nutzt, muss dessen IP ebenfalls im erlaubten Bereich liegen.

## Rückbau Fremdkopplung
- Unzulässige Kopplung entstanden zwischen dem eigenständigen `kids_controller` und dem PI-Guardian-Router, weil ich den Router-Secret-Wert zusätzlich in `/etc/kids_controller/.env` gespiegelt hatte.
- Betroffen war ausschließlich `/etc/kids_controller/.env`; das war eine externe Kids-Controller-Datei und gehört nicht in die Router-Reparatur.
- Die Trennung wurde wiederhergestellt, indem `/etc/kids_controller/.env` auf den vorherigen Stand zurückgesetzt und die temporäre Backup-Datei entfernt wurde.
- Der Router bleibt separat konfiguriert; die Router-seitige Authentifizierung funktioniert weiterhin, ohne dass `kids_controller` hart an Router-Interna gekoppelt ist.

## Neue Integrationsphase: Projekttrennung geprüft
- Der angegebene Kids-Controller-Pfad `/home/alex/kids_controller` existiert hier nicht als Arbeitsbaum.
- Der tatsächliche Kids-Controller-Quellstand liegt derzeit als Archiv vor: `/home/alex/kids_controller_v4.zip`.
- Zusätzliche Backup-Artefakte liegen unter `/home/alex/kids_controller_backups/`.
- Der Router-Arbeitsbaum ist im laufenden System unter `/home/alex/pi-guardian/router` aktiv; zusätzlich existiert eine separate Router-Kopie unter `/home/alex/pi-guardian-router`.
- Ein Git-Repository mit Branch `PI-Guardian` existiert derzeit nur im separaten Baum `/home/alex/pi-guardian-ui-build`; die aktiven Projektbäume `pi-guardian` und Kids Controller sind hier aktuell nicht als Git-Checkout vorhanden.
- Vor jeder API-Integration muss der Kids-Controller aus dem Archiv in einen eigenen Arbeitsbaum überführt werden; erst dann ist eine saubere, projektgetrennte Änderung möglich.

## Kids-Controller / Router-Integration
- Der Kids-Controller wurde in den eigenen Arbeitsbaum `/home/alex/kids_controller` entpackt und dort getrennt weiterbearbeitet.
- Die Router-Anbindung erfolgt ausschließlich über `integrations/router_client.py` und den bestehenden Router-Endpunkt `/route`.
- Der Kids Controller sendet vor der Home-Assistant-Übergabe ein fachliches Ergebnis an den Router, der dort Fairness, Plausibilität, Konsistenz und Regelkonformität prüft.
- Die Authentifizierung bleibt über den bestehenden Headernamen `X-API-Key`; nur der lokale Client-Wert des Kids Controllers wurde konfiguriert.
- Die frühere unzulässige Spiegelung nach `/etc/kids_controller/.env` ist nicht Teil dieser Integration und blieb getrennt.
- Verifikation:
  - `pytest /home/alex/kids_controller/tests/test_router_integration.py -q` lief mit `3 passed`.
  - Der Router-Endpunkt `/route` antwortet auf Loopback mit `200 OK` und liefert Fairness-Metadaten zurück.
  - Der Kids-Controller-Timeout für den Router-Review wurde auf 60 Sekunden angehoben, weil der erste Router-Call rund 43 Sekunden dauerte.

## Phase 1: Client-Verwaltung auf echtes Backend umgestellt
- Ausgangslage: Die UI-Seite `Client-Verwaltung` zeigte lokale Mock-Daten und einen Hinweis auf fehlendes Backend, obwohl der Router bereits eine echte persistente `/clients`-API besitzt.
- Analyse: `router/app/router/clients.py` liefert echte CRUD-Routen (`GET`, `POST`, `PUT`, `DELETE`), die Daten liegen in `router/data/pi_guardian.db` in der Tabelle `client`.
- Wesentlicher Befund: Der Kids Controller ist bereits als persistenter Client gespeichert und erscheint in der Router-DB sowie in der echten `/clients`-Antwort. Dass er in der UI fehlte, lag an der Mock-Seite, nicht an fehlender Persistenz.
- Änderungen:
  - `ui/src/pages/Clients.tsx` auf echte Backend-Daten, echte CRUD-Aktionen und persistente Anzeige umgestellt.
  - `ui/src/api/client.ts` so angepasst, dass `204 No Content` bei `DELETE /clients/{id}` sauber verarbeitet wird.
- Warum nötig:
  - Ohne Backend-Anbindung konnten Clients nur lokal simuliert werden und waren nach Reload nicht persistent.
  - Der 204-Fall hätte sonst den Delete-Pfad im Frontend fehlerhaft gemacht.
- Testergebnisse:
  - `npm run build` im UI-Verzeichnis lief erfolgreich.
  - Live-Bootstrap gegen den Router lieferte `204`, `/clients` lieferte `200`.
  - Live-CRUD gegen `/clients` funktionierte: `POST` = `201`, `PUT` = `200`, `DELETE` = `204`.
  - Die Antwort von `/clients` enthielt den persistierten `Kids_Controller`.
- Offener Reststatus:
  - Keine Mock-Daten mehr auf der Client-Seite; weitere UI-Bereiche bleiben für spätere Phasen unverändert.

## Phase 2: Modellverwaltung auf Backend-Quelle umgestellt
- Ausgangslage: Die Modellseite zeigte zwar installierte Ollama-Modelle, aber die aktiven Router-Modelle kamen weiterhin teilweise aus Frontend-Env-Werten. `LARGE_MODEL` war nur als Laufzeitkonstante vorhanden, und eine persistente Modellregistrierung fehlte.
- Analyse: `GET /models` war bereits echt und lieferte die bei Ollama installierten Modelle. `GET /settings` und `PUT /settings` verwalten jetzt auch `large_model`. Das System war damit funktional unvollständig, aber nicht kaputt.
- Wesentlicher Befund: Eine neue SQLite-Tabelle `modelrecord` wurde ergänzt. Die Registry hält die Kernmodelle als `default` und `large` fest und erlaubt zusätzliche `registered`-Einträge.
- Änderungen:
  - Backend: neue persistente Modellregistry mit CRUD-Endpunkten unter `/models/registry`.
  - Backend: `GET /settings`, `PUT /settings`, `/models/select` und der Admin-Bootstrap wurden um `large_model` und Registry-Synchronisation ergänzt.
  - UI: Modellseite zeigt jetzt Router-Modelle, installierte Modelle und die persistente Registry getrennt an.
  - UI: Dashboard, Diagnose und Einstellungen lesen die Modellnamen jetzt aus dem Backend.
- Warum nötig:
  - Ohne persistente Registry blieb die Modellverwaltung ein Mischsystem aus Ollama-Live-Daten und Frontend-Konfiguration.
  - `large_model` musste serverseitig sichtbar werden, damit UI und Router dieselbe Quelle nutzen.
  - Zusätzliche Modelle müssen administrierbar sein, ohne neue harte UI-Konstanten einzuführen.
- Testergebnisse:
  - Backend-Tests für Modellregistry, Settings-Exposition und bestehende Router-Helfer: `10 passed`.
  - Frontend-Build: erfolgreich.
  - Live-Prüfung nach Router-Neustart:
    - `GET /settings` -> `200`
    - `GET /models` -> `200`
    - `GET /models/registry` -> `200`
    - `GET /status/service` -> `200`
  - Die Registry enthält jetzt `qwen2.5-coder:1.5b` als `default` und `qwen2.5-coder:3b` als `large`.
- Offener Reststatus:
  - Phase 3 bleibt offen: kontrollierter Modell-Download über die Modellverwaltung ist noch zu bewerten und ggf. separat umzusetzen.

## Phase 3: Kontrollierter Modell-Download per Router-Job umgesetzt
- Ausgangslage: Es gab im Router noch keine Download-Funktion für Modelle; `ollama` war im laufenden System nicht als CLI verfügbar, also war ein Shell-Hack keine saubere Option.
- Analyse: Der lokale Stack kann Modell-Downloads sauber über die Ollama-HTTP-API `/api/pull` durchführen. Dafür braucht es aber einen asynchronen Job-Tracker, damit der Request nicht blockiert und Fortschritt sichtbar bleibt.
- Wesentlicher Befund: Der Router schreibt Pull-Jobs jetzt in eine persistente `modelpulljob`-Tabelle. Ein erfolgreicher Pull sorgt zusätzlich dafür, dass das Modell in der Registry auftaucht.
- Änderungen:
  - Backend: neue Pull-Job-API unter `/models/pull` mit `POST`, `GET /models/pull` und `GET /models/pull/{id}`.
  - Backend: asynchroner Pull-Worker gegen Ollama `/api/pull` mit laufender Statusaktualisierung.
  - Backend: Neustart-Reste werden als abgebrochene Pull-Jobs markiert, damit keine hängenden Jobs im System verbleiben.
  - UI: Modellseite bekam einen kontrollierten Pull-Dialog und eine Job-Statusliste.
- Warum nötig:
  - Ein direkter Shell-Blocker wäre architektonisch unsauber und schwer kontrollierbar.
  - Die Pull-Funktion braucht sichtbaren Status, Fehlerbehandlung und saubere Trennung von UI und Download-Execution.
  - Nach erfolgreichem Pull soll das Modell wieder in der Verwaltung auftauchen, ohne manuelle Nachpflege.
- Testergebnisse:
  - Router-Tests inklusive Pull-Job-Lifecycle: `13 passed`.
  - Frontend-Build: erfolgreich.
  - Live-Verifikation:
    - `POST /models/pull` erzeugt einen Job mit `201`.
    - Der Poll auf `GET /models/pull/3` lief über `queued/running` nach `succeeded`.
    - Der Job erreichte `100 %` und meldete `Modell qwen2.5-coder:1.5b erfolgreich geladen`.
    - `GET /models/registry` zeigte danach weiterhin die verwalteten Modelle konsistent an.
  - `journalctl -u pi-guardian-router.service -n 25 --no-pager` zeigt den erfolgreichen Pull-API-Call gegen Ollama und die 200er-Antworten der neuen Routen.
- Offener Reststatus:
- Die Pull-Funktion ist bewusst auf admin-geschützte Nutzung begrenzt.
- Eine Fortschrittsanzeige ist als Jobstatus vorhanden, aber nicht als fein granulierte Byte-/Token-Metrik.

## Phase 3 (aktueller Auftrag): UI-Layout und Kacheln modernisiert
- Ausgangslage: Die Oberfläche nutzte starre Mehrspalten-Grids und schnitt Karteninhalte durch globale `overflow: hidden`-Regeln ab. Dadurch entstanden unnötige Leerflächen, gedrängte Tabellen und unruhige Detailansichten.
- Analyse: Die Ursache lag überwiegend in den globalen Style-Regeln in `ui/src/styles.css`, nicht in einzelnen Seitenfunktionen. `grid--2` und `grid--3` waren als feste Spaltenraster definiert und wurden auf sehr unterschiedliche Inhalte angewendet.
- Ursache:
  - starre Raster statt inhaltsabhängiger Auto-Fit-Layouts
  - Karten mit abgeschnittenem Overflow
  - Tabellen ohne eigenen Scroll-Container
  - identische Rasterlogik für Statuskarten, Formulare und breite Detailtabellen
- Betroffene Dateien:
  - `ui/src/styles.css`
  - `ui/src/pages/Agents.tsx`
  - `ui/src/pages/Models.tsx`
  - `ui/src/pages/Clients.tsx`
  - `ui/src/pages/History.tsx`
  - `ui/src/pages/Memory.tsx`
  - `ui/src/pages/Dashboard.tsx`
- Änderungen:
  - globale Layout- und Grid-Regeln auf responsive Auto-Fit-Varianten umgestellt
  - neue Utility-Layouts wie `grid--dense`, `grid--feature`, `section` und `table-wrap` ergänzt
  - Karten wachsen jetzt natürlich mit dem Inhalt und schneiden ihn nicht mehr ab
  - Tabellen auf den Hauptseiten in horizontale Container gelegt
  - Typografie, Panel-Abstände und Sidebar-/Layout-Proportionen präzisiert
  - fehlende Stildefinition für `badge--info` ergänzt
- Warum nötig:
  - Die UI war funktional, aber strukturell zu grob gerastert. Ohne saubere globale Regeln wären weitere Einzelfixes nur neue Inkonsistenzen gewesen.
  - Breite Verwaltungsseiten wie Modelle, Clients und History brauchen andere Flächenlogik als kompakte Statuskarten.
- Testergebnisse:
  - `npm run build` im Verzeichnis `/home/alex/pi-guardian/ui` erfolgreich.
  - Neuer Build erzeugt die Assets `dist/assets/index-4i8TNM0b.css` und `dist/assets/index-zCMoAfIw.js`.
- Offener Reststatus:
  - Die Oberfläche ist jetzt strukturell moderner und inhaltsgetriebener.
  - Als nächste Phase bleibt die Agentenansicht selbst: mehr echte Aktivitätsdaten statt nur statischer Registry-Information.

## Phase 4: Agent-Aktivität transparenter gemacht
- Ausgangslage: Die Agentenansicht zeigte bisher im Wesentlichen Registry-Daten und den Aktiv/Inaktiv-Status. Echte Run-Daten lagen zwar in der Memory-Persistenz, wurden aber nicht in `/agents` zusammengeführt.
- Analyse:
  - `router/app/api/routes_agents.py` gab nur `list_agents()` bzw. `get_agent()` aus der Registry zurück.
  - Die echten Aktivitätsdaten lagen in `AgentRunRecord` und wurden bereits über die Memory-Schicht persistiert.
  - Die UI konnte dadurch nur statische Agent-Settings anzeigen, aber keine letzte Aufgabe, keinen letzten Laufzeitpunkt und kein zuletzt genutztes Modell.
- Ursache:
  - Registry-Definitionen und Memory-Laufdaten waren backendseitig getrennt.
  - Die Agenten-API bot bisher keine Aktivitätsanreicherung.
- Betroffene Dateien:
  - `router/app/agents/activity.py`
  - `router/app/api/routes_agents.py`
  - `router/app/models/agent_models.py`
  - `router/tests/test_agent_activity.py`
  - `ui/src/types/index.ts`
  - `ui/src/pages/Agents.tsx`
- Änderungen:
  - Neue Helper-Logik bestimmt den neuesten echten Run pro Agent aus `AgentRunRecord`.
  - `/agents` und `/agents/{name}` liefern jetzt optional ein Feld `activity` mit Snapshot-Daten.
  - Die Agentenansicht zeigt jetzt:
    - letzten Laufzeitpunkt
    - letzten Status
    - zuletzt verwendetes Modell
    - letzte Aktivität / Aufgabe
    - letztes Ergebnis-Preview
    - optionalen Auto-Refresh
- Warum nötig:
  - Ohne diese Zusammenführung blieb die Agentenseite funktional zu flach und vermittelte kaum echte Betriebsinformation.
  - Ein Snapshot aus echter Persistenz ist technisch belastbarer als eine künstliche Live-Anzeige.
- Testergebnisse:
  - Router-Tests erfolgreich: `16 passed`
  - Frontend-Build erfolgreich mit `npm run build`
  - `sudo systemctl restart pi-guardian-router.service` erfolgreich
  - `sudo systemctl status pi-guardian-router.service --no-pager -l` zeigt den Dienst aktiv laufend
  - Live-Prüfung:
    - `GET /agents` mit Admin-Key liefert jetzt `activity`-Felder je Agent
    - `GET /agents/guardian_supervisor` liefert ebenfalls `activity`
    - Beispiel: `service_operator` liefert letzten Run, Modell `qwen2.5-coder:1.5b`, Status `success` und Aktivitäts-Preview
- Offener Reststatus:
  - Die Anzeige bleibt bewusst snapshot-basiert; es gibt kein Event-Streaming.
  - Sehr kurze historische Läufe können `0 ms` als Dauer anzeigen, wenn Start- und Endzeit praktisch identisch gespeichert wurden.

## Modellrollen-Fix: Rollenwechsel ohne Umbenennen von Datensätzen
- Ausgangslage:
  - In `router/data/pi_guardian.db` existierten drei Modell-Datensätze:
    - `qwen2.5-coder:1.5b` mit `role=default`
    - `qwen2.5-coder:3b` mit `role=large`
    - `gemma3:4b` mit `role=registered`
  - Beim Setzen von `gemma3:4b` als Deep-Modell schlug der Router mit `sqlite3.IntegrityError: UNIQUE constraint failed: modelrecord.name` fehl.
- Analyse:
  - Die Ursache lag in `router/app/router/model_registry.py`.
  - `_upsert_role_entry()` suchte zuerst den Datensatz mit der Zielrolle und schrieb anschließend dessen `name` auf den neuen Modellnamen um.
  - Bei `role=large` führte das zu einem fehlerhaften Update:
    - vorhandener `large`-Datensatz `qwen2.5-coder:3b`
    - `name` wurde auf `gemma3:4b` umgeschrieben
    - gleichzeitig existierte `gemma3:4b` bereits als eigener Datensatz
    - Folge: UNIQUE-Constraint auf `modelrecord.name`
- Ursache:
  - Modellrollen wurden über Umbenennen bestehender Datensätze synchronisiert.
  - Korrekt ist stattdessen eine Rollen-Neuvergabe auf stabilen Datensatznamen.
- Betroffene Dateien:
  - `router/app/router/model_registry.py`
  - `router/tests/test_model_registry.py`
- Änderungen:
  - `_upsert_role_entry()` entfernt.
  - Neue Logik `_ensure_model_record()` sorgt nur noch dafür, dass gewünschte Modellnamen als Datensätze existieren.
  - `sync_model_registry()` berechnet den Zielzustand jetzt über Modellnamen:
    - `settings.DEFAULT_MODEL` bekommt `role=default`
    - `settings.LARGE_MODEL` bekommt `role=large`
    - alle übrigen Datensätze fallen auf `role=registered`
  - Modellnamen bleiben dabei unverändert.
  - Kernmodelle bleiben aktiviert und erhalten ihre Kernbeschreibung.
  - Der Zielzustand erzwingt weiterhin genau ein `default`- und ein `large`-Modell.
- Warum nötig:
  - Der Fehler war kein Datenproblem, sondern ein falsches Synchronisationsmodell.
  - Ohne diesen Fix würden Rollenwechsel auf bereits registrierte Modelle immer wieder gegen die Unique-Constraint laufen.
- Testergebnisse:
  - Router-Tests erfolgreich:
    - `tests/test_model_registry.py`
    - `tests/test_ollama_compat.py`
    - `tests/test_settings_manager.py`
    - Ergebnis: `13 passed`
  - Dienst neu gestartet:
    - `sudo systemctl restart pi-guardian-router.service`
    - `sudo systemctl status pi-guardian-router.service --no-pager -l` zeigt `active (running)`
  - Live-Rollenwechsel erfolgreich und ohne Constraint-Fehler:
    1. `gemma3:4b` als Deep-Modell gesetzt -> `200`
    2. `gemma3:4b` als Fast-Modell gesetzt -> `200`
    3. Rückwechsel auf `qwen2.5-coder:3b` als Deep-Modell und `qwen2.5-coder:1.5b` als Fast-Modell -> `200`
  - Abschließender Datenbankzustand:
    - `qwen2.5-coder:1.5b` -> `default`
    - `qwen2.5-coder:3b` -> `large`
    - `gemma3:4b` -> `registered`
  - Abschlussprüfung auf Rolleneindeutigkeit:
    - `default|1`
    - `large|1`
    - `registered|1`
- Offener Reststatus:
  - Kein offener Datenbankfehler mehr.
  - Ein direkter `GET /models/registry` mit dem aktuell verwendeten Header-Key lief als `403`, weil dieser Client für diese Route nicht freigeschaltet ist; der eigentliche Rollenfix ist davon unabhängig und über Datenbank- und Settings-Wechsel sauber verifiziert.
