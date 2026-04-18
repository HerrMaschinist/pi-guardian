# PI Guardian Router Product Architecture v1

Datum: 2026-04-17

## Ausgangslage

PI Guardian ist aktuell ein funktionaler Python-basierter Router mit FastAPI, SQLite-Persistenz, Admin-/Client-Auth, Modellregistry, History, Agenten-Aktivität und einer produktiv nutzbaren UI. Der Router ist nicht mehr nur ein Prototyp, aber die zentrale Request-Verarbeitung ist noch stark auf Modellwahl und Ollama-Ausführung fokussiert.

Die nächste Ausbaustufe muss deshalb nicht nur neue Funktionalität liefern, sondern die interne Struktur so schärfen, dass das System später in Richtung eines echten Produkts mit klaren Modulen, stabilen internen Verträgen und austauschbaren Ausführungsschichten weiterentwickelt werden kann.

## Aktueller Ist-Zustand

### Request-Verarbeitung

- HTTP-Einstieg für KI-Anfragen ist aktuell primär `/route` in `/home/alex/pi-guardian/router/app/main.py`.
- Die Route autorisiert den Client und ruft anschließend `route_prompt(...)` in `/home/alex/pi-guardian/router/app/router/service.py` auf.
- `route_prompt(...)` macht aktuell:
  - Modellwahl über `/home/alex/pi-guardian/router/app/router/classifier.py`
  - Fairness-Prüfung über `/home/alex/pi-guardian/router/app/router/fairness.py`
  - direkte LLM-Ausführung über `/home/alex/pi-guardian/router/app/router/ollama_client.py`
  - Audit-Eintrag über `/home/alex/pi-guardian/router/app/router/history.py`

### Modellwahl

- Die aktuelle Klassifikation ist in Wirklichkeit nur eine Modellwahl-Heuristik.
- `select_model_for_prompt(...)` unterscheidet heute nur grob nach Schlüsselwörtern und wählt dann `DEFAULT_MODEL` oder `LARGE_MODEL`.
- Es gibt noch keine vorgelagerte Entscheidung zwischen:
  - reine LLM-Antwort
  - Tool-Nutzung erforderlich
  - Web-/Internet-Zugriff erforderlich
  - Anfrage blockieren

### Tools

- Es existiert bereits ein sauber gekapseltes Tool-System:
  - Registry: `/home/alex/pi-guardian/router/app/tools/registry.py`
  - Executor: `/home/alex/pi-guardian/router/app/tools/executor.py`
- Das Tool-System wird aktuell vor allem im Agenten-Kontext genutzt.
- Für den normalen `/route`-Pfad ist noch kein Tool-Routing eingebunden.

### Client-Verwaltung und Auth

- Clients sind persistent in SQLite gespeichert.
- Auth und Route-Zugriffsprüfung sind in `/home/alex/pi-guardian/router/app/router/auth.py` bereits von den HTTP-Endpunkten entkoppelt.
- Die aktuelle Client-Prüfung deckt vor allem ab:
  - API-Key / Admin-Session
  - aktive/inaktive Clients
  - erlaubte Routen
  - erlaubte IP
- Es gibt noch keine feinere inhaltliche Policy-Prüfung auf Request-Ebene.

### Persistenz und Audit

- Persistente Bausteine existieren bereits:
  - `client`
  - `routehistory`
  - `modelrecord`
  - `modelpulljob`
  - weitere Agenten-/Memory-/Action-/Tool-Tabellen
- `routehistory` ist bereits ein brauchbarer Audit-Grundstock.
- Es fehlen aber noch explizite Entscheidungsdaten wie Klassifikation, Policy-Entscheidung oder Tool-/Web-Bedarf.

### UI-Anbindung

- UI und Backend sind bereits auf echte APIs umgestellt.
- Die UI ist damit kein Blocker, sondern ein nutzbarer Verbraucher zukünftiger Decision-/Policy-Daten.

## Identifizierte Lücken

1. Es gibt keinen expliziten Entscheidungs-Layer vor der Modell- oder Tool-Ausführung.
2. Die heutige Klassifikation ist nur Modellrouting, kein Request-Routing.
3. Tool-System und normaler Request-Pfad sind noch nicht sauber verbunden.
4. Internet-/Web-Bedarf ist architektonisch noch nicht als eigener Entscheidungstyp vorbereitet.
5. Client-Rechte existieren nur auf Routenebene, nicht auf inhaltlicher Nutzungsebene.
6. History ist vorhanden, aber der eigentliche Entscheidungsweg ist noch nicht nachvollziehbar genug.
7. `main.py` und `router/service.py` sind noch zu nah an der Orchestrierung mehrerer Verantwortlichkeiten.

## Soll-Architektur v1

### 1. Entscheidungs-Layer vor dem Modell

Künftig soll jeder eingehende KI-Request zuerst durch eine eigenständige Entscheidungsschicht laufen.

Diese Schicht sitzt logisch zwischen:

- HTTP/API-Einstieg
- nachgelagerter Ausführung über LLM, Tooling oder später Web-Layer

Empfohlene Position im bestehenden Projekt:

- neuer klarer Domänenbaustein unter `/home/alex/pi-guardian/router/app/router/decision/`
  - `models.py`
  - `classifier.py`
  - `service.py`
  - optional später `policy.py`

Die Entscheidungsschicht soll mindestens liefern:

- `classification`
  - `llm_only`
  - `tool_required`
  - `internet_required`
  - `blocked`
- `selected_model`
- `reasons`
- `policy_flags`
- `tool_hints`
- `internet_hints`

### 2. Trennung zwischen Entscheidung und Ausführung

Der Decision-Layer entscheidet, was grundsätzlich mit einer Anfrage passieren soll.

Die eigentliche Ausführung bleibt getrennt:

- LLM-Ausführung: Ollama-Client
- Tool-Ausführung: Tool-Router / Tool-Executor
- später Web-Ausführung: eigener Web-Layer

Damit wird vermieden, dass HTTP-Routen oder `service.py` mit jeder neuen Fähigkeit zu einem Monolithen anwachsen.

### 3. Tool-Routing

Tool-Routing soll nicht als direkter Sonderfall in `/route` entstehen, sondern als eigenes Grundgerüst:

- Decision-Layer liefert `tool_required` plus erste Tool-Hinweise
- ein separater Router-Baustein entscheidet anschließend:
  - welches Tool zugelassen ist
  - ob Tool-Ausführung erlaubt ist
  - ob zunächst nur ein strukturierter Fehler / Hinweis zurückgegeben wird

In v1 wird nur das Grundgerüst vorbereitet. Eine volle autonome Tool-Kette ist bewusst verschoben.

### 4. Internet-/Web-Layer

Internetzugriff wird nicht direkt in LLM-Routen eingebaut.

Stattdessen wird ein eigener Web-Layer vorbereitet:

- Decision-Layer kann `internet_required` zurückgeben
- die eigentliche Ausführung wird später über einen separaten Web-Service oder Web-Adapter erfolgen
- Web-Zugriff bleibt policy-gesteuert und auditierbar

Für v1 ist wichtig:

- Internetbedarf wird als eigener Entscheidungstyp sichtbar
- die Architektur dafür ist vorbereitet
- es gibt noch keinen unkontrollierten Blindzugriff

### 5. Client-Rechte und Policies

Die bestehende Route-Auth bleibt erhalten.

Zusätzlich soll eine zweite Ebene vorbereitet werden:

- Request-Policy auf Inhaltsebene
- Beispiele:
  - darf dieser Client Tool-Zugriff anfordern
  - darf dieser Client Web-Zugriff anfordern
  - darf dieser Client nur LLM-only
  - darf dieser Client geblockte Kategorien grundsätzlich nicht nutzen

Das soll als eigener Policy-Baustein entstehen, nicht verteilt über Endpunkte.

### 6. Audit und Nachvollziehbarkeit

Künftig sollen mindestens diese Entscheidungen nachvollziehbar sein:

- welche Klassifikation getroffen wurde
- welches Modell ausgewählt wurde
- ob Fairness-/Policy-Prüfung eingegriffen hat
- ob Tool-/Internet-Bedarf erkannt wurde
- ob eine Anfrage blockiert wurde und warum

In v1 reicht dafür eine Erweiterung des bestehenden Audit-Pfads.
Eine eigene Decision- oder Policy-History-Tabelle kann später folgen, falls der Umfang steigt.

## Vorbereitung auf spätere Produktisierung

Diese Punkte zahlen schon jetzt auf eine spätere Produktarchitektur ein:

1. **Interne Verträge statt impliziter Kopplung**
   - Decision-Request und Decision-Result werden als explizite Strukturen eingeführt.

2. **Orchestrierung getrennt von Transport**
   - FastAPI bleibt Transport-/HTTP-Schicht.
   - Entscheidung und Routing liegen in eigenen Domänenbausteinen.

3. **Ausführungsschichten klar separieren**
   - LLM
   - Tools
   - später Web
   - später Jobs

4. **Policy als eigenständige Schicht**
   - nicht als verstreute `if`-Sonderfälle in Endpunkten

5. **Audit als Produktfunktion, nicht nur Debug-History**
   - Entscheidungsweg wird nachvollziehbar gemacht

6. **Spätere Portierbarkeit**
   - Wenn der Router später stärker produktisiert oder teilweise aus Python herausgelöst wird, sind Entscheidungs- und Policy-Verträge bereits erkennbar und nicht an FastAPI-Handler gebunden.

## Reihenfolge der Umsetzung

### Sofort umsetzen

1. Decision-Layer mit einfacher Request-Klassifikation
2. sauberes Rückgabeobjekt für Entscheidungen
3. Anpassung des Route-Service auf Decision-Flow
4. Tool-Routing-Grundgerüst
5. erste Audit-Erweiterung für Klassifikation und Entscheidungsgründe

### Danach

1. Client-Policy-Grundlage
2. explizite Tool-/Internet-Rechte pro Client
3. eigener Web-Layer
4. feinere Audit-/Decision-Persistenz

### Später bewusst verschoben

1. großes Job-System
2. komplexe Multi-Agent-Orchestrierung
3. autonomes Tool-Chaining
4. großes Streaming-Rework
5. vollständige Produkt-Neuarchitektur oder Rewrite

## Bewusst verschobene Punkte

- Kein großer Plattform-Umbau in dieser Ausbaustufe
- Kein vollständiges Web-System
- Kein unkontrollierter Internetzugriff
- Kein Rewrite der Router-Architektur nur aus Prinzip
- Keine Vermischung mit anderen Projekten

## Ergebnis Phase 1

Die sinnvollste nächste Ausbaustufe ist eine eigenständige Entscheidungsschicht im Router, die Request-Klassifikation und Routing-Grundlagen liefert, ohne bestehende LLM-, Tool-, Auth- und Audit-Bausteine zu zerstören. Diese Entscheidung unterstützt sowohl die unmittelbare Funktionsverbesserung als auch die spätere Überführung von PI Guardian in ein stärker produktisiertes System mit klaren Modulgrenzen.

## Ergänzung Phase 2-6

Die nächste sinnvolle Schicht wurde jetzt tatsächlich angebunden:

- `tool_required` endet nicht mehr automatisch im LLM-Pfad.
- Der normale `/route`-Pfad besitzt jetzt einen kleinen Execution-Layer unter `router/app/router/execution/`.
- Dieser Layer nutzt bewusst den bestehenden `ToolExecutor`, statt ein paralleles Tool-Subsystem aufzubauen.
- Audit und Response tragen jetzt Execution- und Policy-Daten explizit.

Damit ist der Router nicht nur architektonisch vorbereitet, sondern besitzt erstmals einen echten, produktartig kontrollierten Nicht-LLM-Pfad im normalen Request-System.
