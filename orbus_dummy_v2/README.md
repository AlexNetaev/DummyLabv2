# OrbusSim Dummy V2

## System Name
**OrbusSim Dummy V2** - Realistischer Hardware-Dummy-Simulator für ein Self-Driving-Lab

## Zweck des Systems
OrbusSim Dummy V2 ist ein Simulator, der die Kommunikation mit einem übergeordneten Automatisierungssystem über das Dateisystem simuliert. Das System liest Experiment-Anfragen aus einer Queue-Datei und führt fünf Stationen sequenziell aus, wobei es realistische Rohdaten erzeugt.

## Kommunikationsmodell
- **Eingabe**: `03_Hardware_Queue/experiment.json`
- **Ausgabe**: `02_Research_Cycles/{cycle_id}/B_Hardware/`
- **Kommunikationsart**: Datei-basiert (Filesystem)

## Stationen (5 Stationen)
Das System verfügt über genau **fünf Stationen**, die sequenziell durchlaufen werden:

1. **Station 1: Dosing** - Dosierung von Reagenzien
2. **Station 2: Mixing** - Mischen der Lösungen
3. **Station 3: Reaction / Temperature** - Temperaturreaktion und -messung
4. **Station 4: Fluorescence** - Fluoreszenzmessung
5. **Station 5: Cleanup** - Reinigung und Vorbereitung für nächsten Zyklus

## Wichtige Designentscheidungen

### Keine pH-Monitor-Station
- Es gibt **keine Station 5 pH-Monitor** mehr
- Die ehemalige Station 6 Cleanup wurde zu **Station 5 Cleanup**
- Es gibt **keine pH-Sonde** im System

### Nur Rohdaten als Output
- Das System erzeugt bewusst **nur Rohdaten**
- Es werden **keine automatisch umgerechneten oder abgeleiteten Analysedaten** ausgegeben
- Es werden **keine pH-Werte** als Output geschrieben
- Es werden **keine Fe²⁺-Konzentrationen** als Output geschrieben
- Es werden **keine kompensierten oder korrigierten Fluoreszenzwerte** ausgegeben

### Interne Simulation
- Intern darf der Simulator Chemie und Optik realistisch simulieren
- Diese internen Größen dürfen jedoch **nicht als fertige Analysedaten** ausgegeben werden
- Das System liefert nur Rohdaten für ein lernendes Analysesystem

## Erwartete Output-Dateien (Reihenfolge)
Die folgenden 7 Dateien werden pro Messzyklus erwartet:

1. `station1_dosing.json` - Rohdaten der Dosierstation
2. `station2_mixing.json` - Rohdaten der Mischstation
3. `station3_temperature.csv` - Temperatur-Rohdaten
4. `station4_fluorescence.csv` - Fluoreszenz-Rohdaten
5. `station5_cleanup.json` - Rohdaten der Reinigungsstation
6. `measurement.csv` - Zusammengefasste Messdaten
7. `hardware_protocol.json` - Hardware-Protokoll

## Projektstruktur
```
orbus_dummy_v2/
├── main.py              # Platzhalter-Einstiegspunkt
├── config.py            # Konfiguration und Pfadmanagement
├── requirements.txt     # Minimale Abhängigkeiten
├── .env.example         # Beispiel-Umgebungsvariablen
├── README.md            # Diese Dokumentation
├── models/              # Datenmodelle (to be implemented)
├── stations/            # Stationslogik (to be implemented)
├── physics/             # Physikmodule (to be implemented)
├── io/                  # Datei-I/O (to be implemented)
├── calibration/         # Kalibrierungsdaten
└── tests/               # Tests
```

## Installation
```bash
pip install -r requirements.txt
```

## Konfiguration
Kopiere `.env.example` nach `.env` und passe die Werte an:
- `WORKSPACE_ROOT`: Pfad zum Workspace-Verzeichnis
- `EXTERNAL_WORKSPACE_PATH`: Alternativer Workspace-Pfad (optional)
- `QUEUE_POLL_INTERVAL_S`: Polling-Intervall für die Queue
- `STATION_PAUSE_S`: Pause zwischen Stationen
- `MEASUREMENT_INTERVAL_MS`: Messintervall in Millisekunden
- `FLUORESCENCE_DURATION_S`: Dauer der Fluoreszenzmessung
- `TEMP_NOISE_STD_C`: Standardabweichung für Temperaturrauschen
- `FLUORESCENCE_NOISE_STD_AU`: Standardabweichung für Fluoreszenzrauschen
- `DOSING_NOISE_PERCENT`: Rauschprozentsatz für Dosierung
- `SIMULATION_SEED`: Optionaler Seed für reproduzierbare Simulation

## Hinweis
Dies ist Schritt 1 des Projekts: Projektgerüst, Basiskonfiguration und Dokumentation.
Stationslogik, Physikmodule, CSV-Auswertung, Queue-Verarbeitung und API werden in späteren Schritten implementiert.
