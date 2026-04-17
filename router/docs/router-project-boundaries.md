# Router Project Boundaries

## Router

Zum Router gehören:

- `/home/alex/pi-guardian/router/app`
- `/home/alex/pi-guardian/router/data`
- `/home/alex/pi-guardian/router/docs`
- `/home/alex/pi-guardian/router/logs`
- `/home/alex/pi-guardian/router/ui`

Der Router verwaltet:

- API-Key-Clients
- Agenten
- Skills
- Actions
- Runtime
- SQLite-Persistenz
- Admin-UI-Auth

## Kids Controller

Der Kids Controller bleibt ein separates Projekt mit eigener Konfiguration, eigenen Secrets und eigener Datenhaltung.

Der Router darf nicht direkt von Kids-Controller-Dateien oder -Env-Dateien abhängen.

## Unerwünschte Kopplungen

Folgende Kopplungen gelten als falsch und sollen nicht eingeführt werden:

- Router liest aus `/etc/kids_controller/.env`
- Router importiert Kids-Controller-Konfiguration direkt
- Router verwendet Kids-Controller-API-Keys als Router-Admin-Key
- Router schreibt Daten in Kids-Controller-Pfade
- Router lädt UI-Auth-Zustand nur aus volatilem Browser-Cache ohne Bootstrap-Mechanik

## Saubere Entkopplung

Die Trennung wird so umgesetzt:

- Router besitzt eigene `.env`
- Router besitzt eigenen persistenten Admin-Client
- Router besitzt eigene SQLite-Datenbank
- Router baut Auth und Memory unabhängig vom Kids Controller auf
- vorhandene Kopplungen werden dokumentiert und, wo nötig, entfernt

## Prüfkriterien

Die Trennung ist nur dann sauber, wenn:

- keine Router-Datei auf Kids-Controller-Secrets angewiesen ist
- keine Router-Route auf Kids-Controller-Pfade zeigt
- keine Router-Doku Kids-Controller-Konfiguration als Voraussetzung nennt
- Admin-UI und Memory-DB ausschließlich Router-Assets verwenden

