"""Tests für den Status-Writer."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from orbus_dummy_v2.models.status_schema import SimulatorStatus
from orbus_dummy_v2.io.status_writer import (
    write_status,
    set_idle,
    set_running,
    set_station,
    set_estop,
    set_error,
)
from orbus_dummy_v2 import config


@pytest.fixture
def mock_system_dir(tmp_path):
    """Mockt SYSTEM_DIR auf ein temporäres Verzeichnis."""
    with patch.object(config, "SYSTEM_DIR", tmp_path):
        yield tmp_path


def test_set_idle_writes_status(mock_system_dir):
    """set_idle() schreibt eine Status-Datei mit state='IDLE'."""
    set_idle(last_job_id="job-123", last_job_status="OK")
    
    status_path = mock_system_dir / "simulator_status.json"
    assert status_path.exists()
    
    with open(status_path, "r") as f:
        data = json.load(f)
    
    assert data["state"] == "IDLE"
    assert data["last_job_id"] == "job-123"
    assert data["last_job_status"] == "OK"
    
    # Validierung gegen Schema
    status = SimulatorStatus(**data)
    assert status.state == "IDLE"


def test_set_running_writes_status(mock_system_dir, tmp_path):
    """set_running() schreibt state='RUNNING' mit job_id und cycle_id."""
    from orbus_dummy_v2.models.experiment_schema import ExperimentJob, ExperimentParameters, ReagentDose
    
    reagents = [
        ReagentDose(reagent_name="ascorbic_acid", volume_ul=100.0, concentration_mm=10.0),
        ReagentDose(reagent_name="fecl3", volume_ul=100.0, concentration_mm=1.0),
        ReagentDose(reagent_name="h2o2", volume_ul=100.0, concentration_mm=50.0),
        ReagentDose(reagent_name="fluorescein", volume_ul=100.0, concentration_mm=0.01),
        ReagentDose(reagent_name="phosphate_buffer", volume_ul=100.0, concentration_mm=50.0),
    ]
    params = ExperimentParameters(reagents=reagents)
    job = ExperimentJob(job_id="test-job", cycle_id="Cycle_001", parameters=params)
    
    output_dir = tmp_path / "output"
    set_running(job, output_dir)
    
    status_path = mock_system_dir / "simulator_status.json"
    assert status_path.exists()
    
    with open(status_path, "r") as f:
        data = json.load(f)
    
    assert data["state"] == "RUNNING"
    assert data["job_id"] == "test-job"
    assert data["cycle_id"] == "Cycle_001"
    assert data["output_dir"] == str(output_dir)


def test_set_station_writes_correct_values(mock_system_dir, tmp_path):
    """set_station() schreibt die korrekte current_station und stations_completed."""
    from orbus_dummy_v2.models.experiment_schema import ExperimentJob, ExperimentParameters, ReagentDose
    
    reagents = [
        ReagentDose(reagent_name="ascorbic_acid", volume_ul=100.0, concentration_mm=10.0),
        ReagentDose(reagent_name="fecl3", volume_ul=100.0, concentration_mm=1.0),
        ReagentDose(reagent_name="h2o2", volume_ul=100.0, concentration_mm=50.0),
        ReagentDose(reagent_name="fluorescein", volume_ul=100.0, concentration_mm=0.01),
        ReagentDose(reagent_name="phosphate_buffer", volume_ul=100.0, concentration_mm=50.0),
    ]
    params = ExperimentParameters(reagents=reagents)
    job = ExperimentJob(job_id="test-job", cycle_id="Cycle_001", parameters=params)
    
    output_dir = tmp_path / "output"
    set_station(job, 3, "Reaction", ["station_1_dosing", "station_2_mixing"], output_dir)
    
    status_path = mock_system_dir / "simulator_status.json"
    with open(status_path, "r") as f:
        data = json.load(f)
    
    assert data["current_station"] == 3
    assert data["current_station_name"] == "Reaction"
    assert data["stations_completed"] == ["station_1_dosing", "station_2_mixing"]


def test_set_estop_writes_status(mock_system_dir):
    """set_estop() schreibt state='ESTOP'."""
    set_estop(job_id="job-estop")
    
    status_path = mock_system_dir / "simulator_status.json"
    assert status_path.exists()
    
    with open(status_path, "r") as f:
        data = json.load(f)
    
    assert data["state"] == "ESTOP"
    assert data["job_id"] == "job-estop"


def test_set_error_writes_status(mock_system_dir):
    """set_error() schreibt state='ERROR' mit last_error."""
    set_error(job_id="job-error", error_message="Testfehler aufgetreten")
    
    status_path = mock_system_dir / "simulator_status.json"
    assert status_path.exists()
    
    with open(status_path, "r") as f:
        data = json.load(f)
    
    assert data["state"] == "ERROR"
    assert data["job_id"] == "job-error"
    assert data["last_error"] == "Testfehler aufgetreten"


def test_status_file_is_valid_json(mock_system_dir):
    """Die Status-Datei ist valides JSON und lässt sich in SimulatorStatus parsen."""
    set_idle()
    
    status_path = mock_system_dir / "simulator_status.json"
    with open(status_path, "r") as f:
        data = json.load(f)
    
    # Muss ohne Fehler parsen
    status = SimulatorStatus(**data)
    assert status.simulator_name == "OrbusSim Dummy V2"
    assert status.simulator_version == "2.0.0"
