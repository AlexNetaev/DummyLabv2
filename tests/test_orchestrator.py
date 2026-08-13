"""Tests für den Orchestrator."""
import pytest
from pathlib import Path
import json
import shutil
from unittest.mock import patch

from orbus_dummy_v2.orchestrator import execute_job
from orbus_dummy_v2 import config
from orbus_dummy_v2.models import ExperimentJob


@pytest.fixture
def setup_queue_dirs(tmp_path):
    """Erstellt temporäre Queue-Verzeichnisse und patcht die Config-Pfade."""
    queue_dir = tmp_path / "queue"
    processed_dir = tmp_path / "_processed"
    failed_dir = tmp_path / "_failed"
    estop_file = tmp_path / "ESTOP.flag"
    
    queue_dir.mkdir()
    processed_dir.mkdir()
    failed_dir.mkdir()
    
    # Patche die Config-Pfade für diesen Test
    with patch.object(config, 'HARDWARE_QUEUE_DIR', queue_dir), \
         patch.object(config, 'PROCESSED_QUEUE_DIR', processed_dir), \
         patch.object(config, 'FAILED_QUEUE_DIR', failed_dir), \
         patch.object(config, 'ESTOP_FLAG_FILE', estop_file), \
         patch.object(config, 'STATION_PAUSE_S', 0.0), \
         patch.object(config, 'RESEARCH_CYCLES_DIR', tmp_path / "02_Research_Cycles"):
        
        yield {
            "queue_dir": queue_dir,
            "processed_dir": processed_dir,
            "failed_dir": failed_dir,
            "estop_file": estop_file,
        }


def create_valid_job(queue_dir: Path) -> Path:
    """Erstellt einen gültigen Job in der Queue."""
    job_data = {
        "job_id": "test-job-001",
        "cycle_id": "Cycle_001",
        "parameters": {
            "reagents": [
                {"reagent_name": "ascorbic_acid", "volume_ul": 100.0, "concentration_mm": 10.0},
                {"reagent_name": "fecl3", "volume_ul": 100.0, "concentration_mm": 1.0},
                {"reagent_name": "h2o2", "volume_ul": 100.0, "concentration_mm": 50.0},
                {"reagent_name": "fluorescein", "volume_ul": 100.0, "concentration_mm": 0.01},
                {"reagent_name": "phosphate_buffer", "volume_ul": 100.0, "concentration_mm": 50.0},
            ],
            "mixing_speed_rpm": 500,
            "mixing_time_s": 5.0,
            "target_temperature_c": 37.0,
            "heating_time_s": 10.0,
            "measurement_interval_ms": 1000,
            "fluorescence_duration_s": 10.0,
            "excitation_wavelength_nm": 490,
            "emission_wavelength_nm": 520,
        },
        "station_4_action": "FLUORESCENCE",
    }
    
    job_path = queue_dir / "experiment.json"
    with open(job_path, "w", encoding="utf-8") as f:
        json.dump(job_data, f, indent=2)
    
    return job_path


def test_complete_job_run(setup_queue_dirs):
    """Testet einen vollständigen erfolgreichen Job-Lauf."""
    dirs = setup_queue_dirs
    job_path = create_valid_job(dirs["queue_dir"])
    
    # Job ausführen
    execute_job(job_path)
    
    # Output-Verzeichnis prüfen
    output_dir = dirs["queue_dir"].parent / "02_Research_Cycles" / "Cycle_001" / "B_Hardware"
    assert output_dir.exists()
    
    # Alle 7 Output-Dateien müssen existieren
    assert (output_dir / "station1_dosing.json").exists()
    assert (output_dir / "station2_mixing.json").exists()
    assert (output_dir / "station3_temperature.csv").exists()
    assert (output_dir / "station4_fluorescence.csv").exists()
    assert (output_dir / "station5_cleanup.json").exists()
    assert (output_dir / "measurement.csv").exists()
    assert (output_dir / "hardware_protocol.json").exists()
    
    # Job-Datei muss aus Queue entfernt und nach _processed verschoben worden sein
    assert not job_path.exists()
    processed_files = list(dirs["processed_dir"].glob("experiment_*.json"))
    assert len(processed_files) == 1
    
    # Hardware-Protokoll muss Status OK haben
    with open(output_dir / "hardware_protocol.json", "r", encoding="utf-8") as f:
        protocol = json.load(f)
    assert protocol["status"] == "OK"


def test_estop_aborts_job(setup_queue_dirs):
    """Testet dass E-Stop den Job abbricht."""
    dirs = setup_queue_dirs
    job_path = create_valid_job(dirs["queue_dir"])
    
    # E-Stop-Flag setzen VOR der Ausführung
    dirs["estop_file"].touch()
    
    # Job ausführen (sollte abbrechen)
    execute_job(job_path)
    
    # Job-Datei muss nach _failed verschoben worden sein
    assert not job_path.exists()
    failed_files = list(dirs["failed_dir"].glob("experiment.json"))
    assert len(failed_files) == 1
    
    # Output-Verzeichnis wurde angelegt, aber measurement.csv sollte fehlen
    output_dir = dirs["queue_dir"].parent / "02_Research_Cycles" / "Cycle_001" / "B_Hardware"
    # Station 1 sollte geschrieben worden sein (E-Stop wird zu Beginn geprüft)
    # Aber das Protokoll muss ABORTED_ESTOP zeigen
    if (output_dir / "hardware_protocol.json").exists():
        with open(output_dir / "hardware_protocol.json", "r", encoding="utf-8") as f:
            protocol = json.load(f)
        assert protocol["status"] == "ABORTED_ESTOP"


def test_invalid_json_job(setup_queue_dirs):
    """Testet dass ungültiges JSON zur Quarantäne führt."""
    dirs = setup_queue_dirs
    
    # Ungültige JSON-Datei erstellen
    job_path = dirs["queue_dir"] / "experiment.json"
    with open(job_path, "w", encoding="utf-8") as f:
        f.write("{ broken json")
    
    # Job ausführen
    execute_job(job_path)
    
    # Job-Datei muss nach _failed verschoben worden sein
    assert not job_path.exists()
    failed_files = list(dirs["failed_dir"].glob("experiment.json"))
    assert len(failed_files) == 1
    
    # Kein Output-Verzeichnis sollte angelegt worden sein
    output_dir = dirs["queue_dir"].parent / "02_Research_Cycles"
    assert not output_dir.exists()


def test_missing_reagents_job(setup_queue_dirs):
    """Testet dass fehlende Reagenzien zur Quarantäne führen."""
    dirs = setup_queue_dirs
    
    # Job mit fehlenden Reagenzien erstellen
    job_data = {
        "job_id": "test-job-bad",
        "cycle_id": "Cycle_Bad",
        "parameters": {
            "reagents": [
                # Nur 2 Reagenzien statt 5
                {"reagent_name": "ascorbic_acid", "volume_ul": 100.0, "concentration_mm": 10.0},
                {"reagent_name": "fecl3", "volume_ul": 100.0, "concentration_mm": 1.0},
            ],
            "mixing_speed_rpm": 500,
            "mixing_time_s": 5.0,
            "target_temperature_c": 37.0,
            "heating_time_s": 10.0,
            "measurement_interval_ms": 1000,
            "fluorescence_duration_s": 10.0,
            "excitation_wavelength_nm": 490,
            "emission_wavelength_nm": 520,
        },
        "station_4_action": "FLUORESCENCE",
    }
    
    job_path = dirs["queue_dir"] / "experiment.json"
    with open(job_path, "w", encoding="utf-8") as f:
        json.dump(job_data, f, indent=2)
    
    # Job ausführen
    execute_job(job_path)
    
    # Job-Datei muss nach _failed verschoben worden sein
    assert not job_path.exists()
    failed_files = list(dirs["failed_dir"].glob("experiment.json"))
    assert len(failed_files) == 1
