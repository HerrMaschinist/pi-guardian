# PI Guardian

**DE:**  
PI Guardian ist eine lokale, modulare Systemplattform für Überwachung, Bewertung und Schutz technischer Zustände auf einem Raspberry Pi.  
Das Projekt bildet die Grundlage für einen robusten Guardian Dienst, der Systemzustände analysieren, technische Risiken bewerten und später gezielt auf definierte Ereignisse reagieren kann.

**EN:**  
PI Guardian is a local, modular system platform for monitoring, evaluation, and protection of technical system states on a Raspberry Pi.  
The project provides the foundation for a robust guardian service that can analyze system states, assess technical risks, and later react to defined events in a controlled way.

---

## Kurzbeschreibung / Short Description

**DE:**  
PI Guardian ist das Überwachungs und Schutzsystem.  
Der zugehörige Model Router ist die lokale KI Schnittstelle des Systems und kann auch von anderen Programmen genutzt werden.

**EN:**  
PI Guardian is the monitoring and protection system.  
Its associated model router is the local AI interface of the system and can also be used by other programs.

---

## Projektziel / Project Goal

**DE:**  
Ziel von PI Guardian ist der Aufbau einer nachvollziehbaren, wartbaren und erweiterbaren Plattform für lokale Systemüberwachung, technische Bewertung und kontrollierte KI Nutzung auf einem Raspberry Pi.

Der Fokus liegt auf:

- klarer Architektur
- sauberer Trennung von Verantwortlichkeiten
- stabiler lokaler Ausführung
- kontrollierter Nutzung von CPU, RAM und Modellen
- nachvollziehbarer Dokumentation
- Docker fähigem Betrieb
- schrittweiser Erweiterbarkeit ohne Architekturbruch

PI Guardian soll nicht einfach nur ein einzelnes Skript oder ein Bot sein, sondern eine belastbare technische Kernplattform.

**EN:**  
The goal of PI Guardian is to build a traceable, maintainable, and extensible platform for local system monitoring, technical evaluation, and controlled AI usage on a Raspberry Pi.

The focus is on:

- clear architecture
- clean separation of responsibilities
- stable local execution
- controlled use of CPU, RAM, and models
- traceable documentation
- Docker ready operation
- stepwise extensibility without architectural breakage

PI Guardian is not intended to be just a single script or a bot, but a reliable technical core platform.

---

## Systemgrenze / System Boundary

**DE:**  
PI Guardian ist **kein** Dokumentenverwaltungssystem.  
PI Guardian ist **kein** allgemeines Fachsystem für externe Programme.  
PI Guardian ist das System für Überwachung, Bewertung und Schutz.

Der **Model Router** gehört technisch zum Gesamtprojekt, übernimmt jedoch eine andere Aufgabe:  
Er stellt eine lokale KI Schnittstelle bereit, über die PI Guardian und später auch andere Programme strukturierte KI Anfragen an lokale Modelle senden können.

Das bedeutet:

- **PI Guardian** = Überwachung, Bewertung, Schutz, Reaktion
- **Model Router** = Modellwahl, API, KI Zugriff, Ollama Steuerung
- **andere Programme** = optionale Nutzer des Routers, aber nicht Teil der Guardian Fachlogik

**EN:**  
PI Guardian is **not** a document management system.  
PI Guardian is **not** a general business application for external programs.  
PI Guardian is the system for monitoring, evaluation, and protection.

The **model router** is technically part of the overall project, but serves a different role:  
It provides a local AI interface through which PI Guardian and later other programs can send structured AI requests to local models.

This means:

- **PI Guardian** = monitoring, evaluation, protection, reaction
- **Model Router** = model selection, API, AI access, Ollama control
- **other programs** = optional users of the router, but not part of Guardian business logic

---

## Aktueller Fokus / Current Focus

**DE:**  
Der aktuelle Schwerpunkt liegt auf dem Aufbau des **PI Guardian Model Routers** als zentralem lokalen KI Zugriffspunkt.  
Der Router wird als eigenständiger FastAPI Dienst konzipiert und übernimmt die technische Steuerung lokaler LLM Aufrufe über Ollama.

PI Guardian selbst bleibt fachlich auf Systemüberwachung, Analyse technischer Zustände und Schutzlogik begrenzt.  
Der Router ist die standardisierte KI Zugriffsschicht für PI Guardian und kann später auch von anderen lokalen Diensten verwendet werden.

Der Router soll in der ersten Ausbaustufe insbesondere folgende Aufgaben übernehmen:

- Annahme strukturierter API Anfragen
- Klassifikation technischer Aufgaben
- Auswahl des passenden lokalen Modells
- kontrollierter Aufruf lokaler Modelle über Ollama
- erzwungene serielle Ausführung zur Schonung des Systems
- strukturierte Antwortvalidierung
- definierte Eskalation vom schnellen Modell zum tieferen Modell
- Schutz des Raspberry Pi vor unnötiger CPU und RAM Last

**EN:**  
The current focus is the development of the **PI Guardian Model Router** as the central local AI access layer.  
The router is designed as an independent FastAPI service and handles the technical control of local LLM calls through Ollama.

PI Guardian itself remains functionally limited to system monitoring, analysis of technical states, and protection logic.  
The router is the standardized AI access layer for PI Guardian and may later also be used by other local services.

In its first stage, the router is intended to provide the following functions:

- acceptance of structured API requests
- classification of technical tasks
- selection of the appropriate local model
- controlled execution of local models through Ollama
- enforced serial execution to protect system stability
- structured response validation
- defined escalation from fast model to deep model
- protection of the Raspberry Pi from unnecessary CPU and RAM load

---

## Kernkomponenten / Core Components

### 1. PI Guardian

**DE:**  
PI Guardian ist der fachliche Kern des Projekts für Überwachung, Bewertung und Schutz.  
Hier liegen die Regeln und Entscheidungen rund um technische Zustände des Systems.

Geplante Aufgaben von PI Guardian:

- Überwachung von CPU, RAM, Temperatur, Speicher und Diensten
- Bewertung technischer Zustände und Warnlagen
- Erkennung auffälliger Systemzustände
- definierte Reaktionen auf bekannte Ereignisse
- Integration mit lokalen Systemdiensten und Containern
- spätere Anbindung an Benachrichtigungs oder Steuerungsfunktionen

**EN:**  
PI Guardian is the functional core of the project for monitoring, evaluation, and protection.  
This is where the rules and decisions related to technical system states belong.

Planned responsibilities of PI Guardian:

- monitoring CPU, RAM, temperature, storage, and services
- evaluating technical states and warning situations
- detecting unusual system conditions
- reacting to known events in a controlled way
- integrating with local system services and containers
- later connecting to notification or control functions

---

### 2. PI Guardian Model Router

**DE:**  
Der Model Router ist die lokale KI Schnittstelle des Projekts.  
Er entkoppelt PI Guardian und spätere weitere Programme vom direkten Zugriff auf Ollama oder einzelne Modelle.

Geplante Eigenschaften:

- FastAPI basierte interne API
- Routing zwischen mehreren lokalen Modellen
- technische Klassifikation eingehender Aufgaben
- konfigurierbare Modellrollen wie `fast_model` und `deep_model`
- feste Ressourcenregeln für Threads, Kontext und Keep Alive
- kontrollierte Fallback Logik
- strukturierte Rückgaben für maschinelle Weiterverarbeitung
- nachvollziehbare Logs für Betrieb und Debugging

**EN:**  
The model router is the local AI interface of the project.  
It decouples PI Guardian and future programs from direct access to Ollama or specific models.

Planned properties:

- FastAPI based internal API
- routing between multiple local models
- technical classification of incoming tasks
- configurable model roles such as `fast_model` and `deep_model`
- fixed resource rules for threads, context, and keep alive
- controlled fallback logic
- structured outputs for machine processing
- traceable logs for operation and debugging

---

### 3. Router as AI Interface for Additional Services / Router als KI Schnittstelle für weitere Dienste

**DE:**  
Der Model Router ist nicht ausschließlich für PI Guardian vorgesehen.  
Er kann später auch von anderen lokalen Programmen oder Diensten verwendet werden, sofern diese eine standardisierte lokale KI Schnittstelle benötigen.

Wichtig ist dabei:  
Diese anderen Programme werden **nicht** Teil der Guardian Fachlogik.  
Sie nutzen nur dieselbe technische Router Schicht.

Mögliche Anwendungsfelder des Routers:

- strukturierte JSON Ausgaben
- technische Klassifikation
- lokale Analyseaufgaben
- Debugging Unterstützung
- SQL nahe Strukturierungsaufgaben
- standardisierte lokale Modellaufrufe über API

**EN:**  
The model router is not intended exclusively for PI Guardian.  
It may later also be used by other local programs or services if they require a standardized local AI interface.

Important:  
These other programs do **not** become part of Guardian business logic.  
They only use the same technical router layer.

Possible router use cases:

- structured JSON output
- technical classification
- local analysis tasks
- debugging assistance
- SQL related structuring tasks
- standardized local model calls through API

---

## Architekturprinzipien / Architectural Principles

**DE:**  
PI Guardian folgt einigen festen Grundregeln:

- **Ein Dienst, eine Aufgabe**  
  PI Guardian übernimmt Überwachung und Schutz.  
  Der Router übernimmt KI Routing und Modellsteuerung.

- **Stabilität vor Komfort**  
  Systemstabilität ist wichtiger als maximale KI Auslastung.

- **Keine direkte Modellnutzung durch Fachdienste**  
  Interne Dienste sollen nicht direkt mit Ollama sprechen, sondern über den Router.

- **Strukturierte Antworten vor Freitext**  
  Wo möglich werden JSON oder schemafähige Antworten bevorzugt.

- **Serielle Ausführung statt chaotischer Parallelisierung**  
  Auf dem Raspberry Pi ist Vorhersagbarkeit wichtiger als aggressive Parallelität.

- **Konfiguration nach außen, Regeln in den Code**  
  Modellnamen, Ports, URLs und Limits sind konfigurierbar.  
  Die eigentliche Routinglogik bleibt versioniert im Code.

**EN:**  
PI Guardian follows a set of strict design rules:

- **One service, one responsibility**  
  PI Guardian handles monitoring and protection.  
  The router handles AI routing and model control.

- **Stability over convenience**  
  System stability is more important than maximum AI throughput.

- **No direct model access for functional services**  
  Internal services should not talk to Ollama directly, but through the router.

- **Structured responses over free text**  
  Wherever possible, JSON or schema capable responses are preferred.

- **Serial execution instead of chaotic parallelism**  
  On a Raspberry Pi, predictability is more important than aggressive parallelism.

- **Configuration outside, rules in code**  
  Model names, ports, URLs, and limits are configurable.  
  The actual routing logic remains versioned in code.

---

## Geplante Fähigkeiten / Planned Capabilities

**DE:**  
PI Guardian ist als wachsendes System geplant.  
Neben der Basisarchitektur sind unter anderem folgende Erweiterungen vorgesehen:

- Guardian Anbindung über interne API
- strukturierte technische Bewertung per LLM
- Docker und Dienstestatus Auswertung
- Metrik und Statusendpunkte
- optionale technische Diagnosedaten
- Integration weiterer lokaler Dienste über den Router
- mögliche Hardware Erweiterungen für lokale KI Beschleunigung
- spätere Erweiterung um zusätzliche Schutz und Assistenzfunktionen

**EN:**  
PI Guardian is planned as a growing system.  
In addition to the base architecture, the following extensions are intended:

- Guardian integration through internal API
- structured technical evaluation through LLMs
- Docker and service status analysis
- metrics and status endpoints
- optional technical diagnostic data
- integration of additional local services through the router
- possible hardware extensions for local AI acceleration
- future expansion with additional protection and assistance functions

---

## Nicht Ziele / Non Goals

**DE:**  
Folgende Dinge gehören bewusst nicht zum Kern von Version 1:

- Dokumentenverwaltung als Bestandteil von PI Guardian
- unkontrollierte Parallelisierung mehrerer großer Modelle
- vermischte Fachlogik im Router
- direkte Produktivnutzung ohne Architekturtrennung
- chaotische Skriptsammlung ohne API Vertrag
- Speicherung produktiver Secrets im Repository
- offene Cloud Abhängigkeit als Pflichtbestandteil

**EN:**  
The following items are intentionally not part of the core of version 1:

- document management as part of PI Guardian
- uncontrolled parallel execution of multiple large models
- mixed business logic inside the router
- direct production use without architectural separation
- chaotic script collection without an API contract
- storage of production secrets in the repository
- mandatory public cloud dependency

---

## Repository Zweck / Repository Purpose

**DE:**  
Dieses Repository dient der technischen Nachvollziehbarkeit, Versionierung und Weiterentwicklung des Gesamtsystems.  
Es soll Code, Konfigurationsbeispiele, Dokumentation, Architekturentscheidungen und spätere Betriebsinformationen an einem Ort bündeln.

Geplant sind unter anderem Bereiche für:

- Guardian Code
- Router Code
- Konfigurationsbeispiele
- Docker Setup
- API Spezifikation
- Architektur und Betriebsdokumentation
- Integrationshinweise für interne Dienste

**EN:**  
This repository is intended to provide technical traceability, versioning, and long term development of the overall system.  
It is meant to bundle code, configuration examples, documentation, architectural decisions, and later operational information in one place.

Planned areas include:

- Guardian code
- router code
- configuration examples
- Docker setup
- API specification
- architecture and operations documentation
- integration notes for internal services

---

## Sicherheitshinweis / Security Notice

**DE:**  
Dieses Repository darf keine produktiven Secrets enthalten.  
Keine Tokens, keine echten Zugangsdaten, keine vollständigen `.env` Dateien und keine sensiblen internen Informationen committen.

Verwendet werden nur sichere Beispieldateien wie:

- `.env.example`
- Beispielkonfigurationen ohne produktive Inhalte
- dokumentierte Platzhalterwerte

**EN:**  
This repository must not contain production secrets.  
Do not commit tokens, real credentials, full `.env` files, or sensitive internal information.

Only safe example files should be used, such as:

- `.env.example`
- example configurations without production content
- documented placeholder values

---

## Status / Status

**DE:**  
Aktuelle Phase: Architektur und Grundstruktur des PI Guardian Model Routers.

**EN:**  
Current phase: architecture and base structure of the PI Guardian model router.
