# Kids Controller Router Integration

Datum: 2026-04-17

## Ziel der Integration
- Der Kids Controller soll den PI-Guardian-Router als externen KI-Dienst nutzen.
- Der Router soll eine zusätzliche Fairness-, Plausibilitäts- und Konsistenzprüfung vor der finalen Home-Assistant-Übergabe liefern.
- Beide Projekte sollen getrennt bleiben und nur über explizite API-Aufrufe kommunizieren.

## Bestätigte Projekttrennung
- Der Kids-Controller läuft jetzt in einem eigenen Arbeitsbaum unter `/home/alex/kids_controller`.
- Die ursprüngliche Quelle lag als Archiv vor: `/home/alex/kids_controller_v4.zip`.
- Der PI-Guardian-Router läuft im separaten Baum `/home/alex/pi-guardian/router`.
- Zusätzlich existiert eine separate Router-Kopie unter `/home/alex/pi-guardian-router`.
- In beiden aktiven Projektbäumen liegt hier kein eigenes `.git`; ein separater Git-Checkout mit Branch `PI-Guardian` existiert nur unter `/home/alex/pi-guardian-ui-build` und gehört nicht zum Kids Controller.

## Erkannte Alt-Kopplungen
- Eine frühere unzulässige Kopplung wurde bereits zurückgebaut: ein Router-Secret war fälschlich in `/etc/kids_controller/.env` gespiegelt worden.
- Diese Spiegelung war architektonisch falsch, weil damit ein Router-Secret in Fremdkonfiguration gelandet wäre.
- Für die aktuelle Integrationsphase wird keine Secret-Spiegelung zwischen Projekten verwendet.

## Architekturentscheidung
- Keine gemeinsame Konfiguration.
- Keine impliziten Pfadabhängigkeiten.
- Keine Secret-Synchronisierung.
- Der Kids Controller wird über einen expliziten API-Client an den Router angebunden.
- Die Fairness-Prüfung bleibt eine nachgelagerte Router-Prüfinstanz und ersetzt keine Fachlogik im Kids Controller.

## Betroffene Dateien
- `/home/alex/kids_controller/config/settings.py`
- `/home/alex/kids_controller/.env`
- `/home/alex/kids_controller/integrations/router_client.py`
- `/home/alex/kids_controller/app/api_routes.py`
- `/home/alex/kids_controller/pyproject.toml`
- `/home/alex/kids_controller/README.md`
- `/home/alex/kids_controller/tests/test_router_integration.py`

## Grobe nächste Umsetzungsschritte
- Router-API und Auth-Fluss zwischen den beiden Projekten vermessen.
- Einen klar benannten Router-Endpunkt für die Fairness-Prüfung verwenden.
- Einen gekapselten API-Client im Kids Controller an der Stelle einbauen, an der das fachliche Ergebnis vor der Home-Assistant-Übergabe entsteht.

## Testablauf
- Projekttrennung prüfen.
- Router-Status prüfen.
- Kids-Controller-Quellstand aus dem Archiv lokal verfügbar machen.
- API-Aufruf vom Kids Controller zum Router prüfen.
- Bewertete Router-Antwort gegen einen Beispiel-Output verifizieren.
- Home-Assistant-Übergabe erst nach erfolgreicher Bewertung simulieren.

## Ergebnis
- Die Projekttrennung ist bestätigt und bleibt technisch sauber getrennt.
- Der Kids Controller nutzt den Router jetzt ausschließlich als externen Review-Dienst via HTTP.
- Die Fairness-Prüfung ist im Kids Controller vor der Home-Assistant-Übergabe aktiv.
- Der Router-Auth-Headername `X-API-Key` blieb unverändert.

## Offener Reststatus
- Die Router-Review-Latenz liegt beim ersten Aufruf bei rund 43 Sekunden; der Kids-Controller-Timeout wurde deshalb auf 60 Sekunden gesetzt.
- Der Loopback-Client `127.0.0.1` ist im Router für den Kids Controller freigegeben; andere LAN-IP-Hinweise bleiben weiterhin per Policy blockiert.
