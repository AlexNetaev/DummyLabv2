"""Tests für Stationen 1-3."""

import time
from pathlib import Path
from datetime import timezone

import pytest

from orbus_dummy_v2.stations import Station1Dosing, Station2Mixing, Station3Reaction, EStopTriggered
from orbus_dummy_v2.models import ExperimentJob, ExperimentParameters, ReagentDose, CalibrationData
from orbus_dummy_v2.io.calibration_loader import get_default_calibration
from orbus_dummy_v2.physics.noise import create_rng
from orbus_dummy_v2 import config


def create_valid_job():
    """Erstellt einen gültigen Test-Job."""
    reagents = [
        ReagentDose(reagent_name="ascorbic_acid", volume_ul=500.0, concentration_mm=25.0),
        ReagentDose(reagent_name="fecl3", volume_ul=100.0, concentration_mm=1.0),
        ReagentDose(reagent_name="h2o2", volume_ul=200.0, concentration_mm=50.0),
        ReagentDose(reagent_name="fluorescein", volume_ul=100.0, concentration_mm=0.01),
        ReagentDose(reagent_name="phosphate_buffer", volume_ul=100.0, concentration_mm=50.0),
    ]
    
    params = ExperimentParameters(
        reagents=reagents,
        mixing_speed_rpm=600.0,
        mixing_time_s=15.0,
        target_temperature_c=37.0,
        heating_time_s=30.0,
        measurement_interval_ms=500,
        fluorescence_duration_s=60.0,
    )
    
    return ExperimentJob(
        job_id="test-job-001",
        cycle_id="Cycle_001",
        parameters=params
    )


class TestStation1Dosing:
    """Tests für Station 1 (Dosing)."""
    
    def test_station1_writes_json(self, tmp_path, monkeypatch):
        """Station 1 schreibt station1_dosing.json mit 5 Reagenzien."""
        # Setup
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        job = create_valid_job()
        calibration = get_default_calibration()
        rng = create_rng(42)
        
        # Patch ESTOP_FLAG_FILE
        estop_file = tmp_path / "ESTOP.flag"
        monkeypatch.setattr(config, "ESTOP_FLAG_FILE", estop_file)
        
        # Execute
        station = Station1Dosing(job, output_dir, calibration, rng)
        log = station.run()
        
        # Verify
        json_file = output_dir / "station1_dosing.json"
        assert json_file.exists()
        
        import json
        data = json.loads(json_file.read_text())
        assert len(data["reagents"]) == 5
        assert "actual_volume_ul" not in data["reagents"][0]
        assert log["status"] == "OK"
    
    def test_station1_estop_raises(self, tmp_path, monkeypatch):
        """Station 1 wirft EStopTriggered bei gesetzter Flag."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        job = create_valid_job()
        calibration = get_default_calibration()
        rng = create_rng(42)
        
        # Create ESTOP flag
        estop_file = tmp_path / "ESTOP.flag"
        estop_file.touch()
        monkeypatch.setattr(config, "ESTOP_FLAG_FILE", estop_file)
        
        # Execute & Verify
        station = Station1Dosing(job, output_dir, calibration, rng)
        with pytest.raises(EStopTriggered):
            station.run()
        
        # No output file should be written
        assert not (output_dir / "station1_dosing.json").exists()


class TestStation2Mixing:
    """Tests für Station 2 (Mixing)."""
    
    def test_station2_writes_json(self, tmp_path, monkeypatch):
        """Station 2 schreibt station2_mixing.json mit korrekten RPM."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        job = create_valid_job()
        calibration = get_default_calibration()
        rng = create_rng(42)
        
        estop_file = tmp_path / "ESTOP.flag"
        monkeypatch.setattr(config, "ESTOP_FLAG_FILE", estop_file)
        
        station = Station2Mixing(job, output_dir, calibration, rng)
        log = station.run()
        
        json_file = output_dir / "station2_mixing.json"
        assert json_file.exists()
        
        import json
        data = json.loads(json_file.read_text())
        assert data["target_rpm"] == 600.0
        assert data["mixing_time_s"] == 15.0
    
    def test_station2_estop_raises(self, tmp_path, monkeypatch):
        """Station 2 wirft EStopTriggered bei gesetzter Flag."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        job = create_valid_job()
        calibration = get_default_calibration()
        rng = create_rng(42)
        
        estop_file = tmp_path / "ESTOP.flag"
        estop_file.touch()
        monkeypatch.setattr(config, "ESTOP_FLAG_FILE", estop_file)
        
        station = Station2Mixing(job, output_dir, calibration, rng)
        with pytest.raises(EStopTriggered):
            station.run()
        
        assert not (output_dir / "station2_mixing.json").exists()


class TestStation3Reaction:
    """Tests für Station 3 (Reaction/Temperature)."""
    
    def test_station3_writes_csv(self, tmp_path, monkeypatch):
        """Station 3 schreibt station3_temperature.csv mit korrektem Header und Werten."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        job = create_valid_job()
        calibration = get_default_calibration()
        rng = create_rng(42)
        
        estop_file = tmp_path / "ESTOP.flag"
        monkeypatch.setattr(config, "ESTOP_FLAG_FILE", estop_file)
        
        station = Station3Reaction(job, output_dir, calibration, rng)
        log = station.run()
        
        csv_file = output_dir / "station3_temperature.csv"
        assert csv_file.exists()
        
        lines = csv_file.read_text().strip().split("\n")
        header = lines[0]
        assert header == "time_ms,temp_c,heater_power_w"
        
        # Erwarte mindestens einige Datenpunkte (30s / 0.5s = 61 Punkte + 1)
        assert len(lines) > 10
        
        # Temperatur sollte von ~22°C auf ~37°C steigen
        first_temp = float(lines[1].split(",")[1])
        last_temp = float(lines[-1].split(",")[1])
        
        assert first_temp < 30.0  # Start nahe Raumtemperatur
        assert last_temp > 35.0  # Ende nahe Zieltemperatur
    
    def test_station3_estop_raises(self, tmp_path, monkeypatch):
        """Station 3 wirft EStopTriggered bei gesetzter Flag."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        job = create_valid_job()
        calibration = get_default_calibration()
        rng = create_rng(42)
        
        estop_file = tmp_path / "ESTOP.flag"
        estop_file.touch()
        monkeypatch.setattr(config, "ESTOP_FLAG_FILE", estop_file)
        
        station = Station3Reaction(job, output_dir, calibration, rng)
        with pytest.raises(EStopTriggered):
            station.run()
        
        assert not (output_dir / "station3_temperature.csv").exists()
