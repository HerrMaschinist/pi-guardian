# Router Admin Auth

## Ziel

Die Admin-UI soll nach Browser-Cache-Verlust oder Reload wieder stabil mit geschützten Router-Endpunkten sprechen können, ohne dass der Router auf Kids-Controller-Secrets angewiesen ist.

## Dedizierter Admin-Client

- Name: `Router_Admin_UI_Persistent`
- Zweck: nur die Router-Admin-UI
- Schlüssel: serverseitig im Router erzeugt und in der Router-DB gepflegt
- keine Kopplung an `/etc/kids_controller`
- kein globaler Super-Key

## Serverseitige Ablage

Der Admin-Client wird im Router persistiert und bei Bedarf automatisch angelegt oder aktualisiert.

Die Admin-Client-Daten liegen damit in der Router-eigenen Konfiguration und Datenbank, nicht im Kids-Controller-Umfeld.

## Freigegebene Routen

Die UI darf nur die Routen nutzen, die sie operativ benötigt:

- `/health`
- `/settings`
- `/status/service`
- `/logs`
- `/clients`
- `/agents`
- `/skills`
- `/actions`
- `/memory`

Optional und nur bei realem Bedarf zusätzlich:

- `/route`
- `/models`
- `/models/select`

## Auth-Mechanik

Der Router akzeptiert für geschützte Admin-Requests:

- `X-API-Key`
- oder ein HttpOnly-Cookie für die Admin-Session

Nach einem erfolgreichen Bootstrap setzt der Router ein HttpOnly-Cookie mit dem persistierten Admin-Key.

## UI-Verhalten

Die UI nutzt beim Laden geschützter Endpunkte einen Bootstrap-Request:

- wenn kein lokaler Key vorhanden ist, wird `/auth/bootstrap` aufgerufen
- der Router setzt die Session erneut
- danach laufen geschützte Requests mit `credentials: 'include'`

Wenn der Browser-Cache oder Local Storage leer ist, kann die UI dadurch wieder stabil starten.

## Fehlerfall

Wenn Bootstrap nicht möglich ist, reagiert die UI kontrolliert:

- geschützte Requests schlagen sichtbar fehl
- der manuelle Admin-Key bleibt als Fallback möglich
- es wird kein Key unkontrolliert ins Frontend gebacken

## Sicherheitsgrenzen

- kein Zugriff auf Kids-Controller-Dateien
- keine Nutzung von `/etc/kids_controller/.env`
- keine gemeinsame Konfigurationsbasis mit dem Kids Controller
- kein hart codierter API-Key im ausgelieferten Bundle

