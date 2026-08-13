"""Tests für Station 4 (Fluorescence) und Station 5 (Cleanup)."""
import pytest
from pathlib import Path
from datetime import datetime, timezone
import json

from orbus_dummy_v2.models import ExperimentJob, ExperimentParameters, ReagentDose, CalibrationData
from orbus_dummy_v2.io.calibration_loader import get_default_calibration
from orbus_dummy_v2.stations.station4_fluorescence import Station4Fluorescence
from orbus_dummy_v2.stations.station5_cleanup import Station5Cleanup
from orbus_dummy_v2.stations.base_station import EStopTriggered
from orbus_dummy_v2 import config
from orbus_dummy_v2.physics.noise import create_rng


def _create_valid_job():
    """Erstellt einen gültigen ExperimentJob mit allen 5 Reagenzien."""
    reagents = [
        ReagentDose(reagent_name="ascorbic_acid", volume_ul=500.0, concentration_mm=25.0),
        ReagentDose(reagent_name="fecl3", volume_ul=100.0, concentration_mm=1.0),
        ReagentDose(reagent_name="h2o2", volume_ul=200.0, concentration_mm=50.0),
        ReagentDose(reagent_name="fluorescein", volume_ul=100.0, concentration_mm=0.01),
        ReagentDose(reagent_name="phosphate_buffer", volume_ul=100.0, concentration_mm=50.0),
    ]
    params = ExperimentParameters(
        reagents=reagents,
        mixing_speed_rpm=600,
        mixing_time_s=15.0,
        target_temperature_c=37.0,
        heating_time_s=30.0,
        measurement_interval_ms=500,
        fluorescence_duration_s=10.0,
        excitation_wavelength_nm=490,
        emission_wavelength_nm=520,
    )
    return ExperimentJob(
        job_id="test-job-004",
        cycle_id="Cycle_004",
        parameters=params,
        station_4_action="FLUORESCENCE",
        simulation_seed=42,
    )


class TestStation4Fluorescence:
    """Tests für Station 4."""

    def test_station4_schreibt_csv(self, tmp_path):
        """Station 4 schreibt station4_fluorescence.csv mit korrektem Header."""
        job = _create_valid_job()
        calibration = get_default_calibration()
        rng = create_rng(job.simulation_seed)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        station = Station4Fluorescence(job, output_dir, calibration, rng)
        station.run()

        csv_file = output_dir / "station4_fluorescence.csv"
        assert csv_file.exists()

        content = csv_file.read_text()
        lines = content.strip().split("\n")
        assert lines[0] == "time_ms,fluorescence_raw_au"
        assert len(lines) > 1  # Mindestens Header + 1 Datenzeile

    def test_station4_header_korrekt(self, tmp_path):
        """Der CSV-Header ist korrekt."""
        job = _create_valid_job()
        calibration = get_default_calibration()
        rng = create_rng(job.simulation_seed)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        station = Station4Fluorescence(job, output_dir, calibration, rng)
        station.run()

        csv_file = output_dir / "station4_fluorescence.csv"
        header = csv_file.read_text().split("\n")[0]
        assert header == "time_ms,fluorescence_raw_au"

    def test_station4_anzahl_zeilen(self, tmp_path):
        """Die Anzahl der Zeilen entspricht der Dauer und dem Intervall."""
        job = _create_valid_job()
        # 10 Sekunden, 500ms Intervall -> ca. 21 Punkte (0 bis 10000 in 500er Schritten)
        calibration = get_default_calibration()
        rng = create_rng(job.simulation_seed)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        station = Station4Fluorescence(job, output_dir, calibration, rng)
        station.run()

        csv_file = output_dir / "station4_fluorescence.csv"
        lines = csv_file.read_text().strip().split("\n")
        # Header + Datenzeilen
        expected_points = int(job.parameters.fluorescence_duration_s * 1000 // job.parameters.measurement_interval_ms) + 1
        assert len(lines) == expected_points + 1  # +1 für Header

    def test_station4_fluoreszenz_werte_nicht_negativ(self, tmp_path):
        """Alle Fluoreszenzwerte sind >= 0.0."""
        job = _create_valid_job()
        calibration = get_default_calibration()
        rng = create_rng(job.simulation_seed)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        station = Station4Fluorescence(job, output_dir, calibration, rng)
        station.run()

        csv_file = output_dir / "station4_fluorescence.csv"
        lines = csv_file.read_text().strip().split("\n")[1:]  # Ohne Header
        for line in lines:
            parts = line.split(",")
            fluoro_value = float(parts[1])
            assert fluoro_value >= 0.0, f"Negativer Fluoreszenzwert: {fluoro_value}"

    def test_station4_estop_wirft_exception(self, tmp_path, monkeypatch):
        """Bei E-Stop wird EStopTriggered geworfen und keine CSV geschrieben."""
        estop_file = tmp_path / "ESTOP.flag"
        estop_file.touch()
        monkeypatch.setattr(config, "ESTOP_FLAG_FILE", estop_file)

        job = _create_valid_job()
        calibration = get_default_calibration()
        rng = create_rng(job.simulation_seed)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        station = Station4Fluorescence(job, output_dir, calibration, rng)

        with pytest.raises(EStopTriggered):
            station.run()

        csv_file = output_dir / "station4_fluorescence.csv"
        assert not csv_file.exists()


class TestStation5Cleanup:
    """Tests für Station 5."""

    def test_station5_schreibt_json(self, tmp_path):
        """Station 5 schreibt station5_cleanup.json."""
        job = _create_valid_job()
        calibration = get_default_calibration()
        rng = create_rng(42)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        station = Station5Cleanup(job, output_dir, calibration, rng)
        station.run()

        json_file = output_dir / "station5_cleanup.json"
        assert json_file.exists()

    def test_station5_station_feld_ist_5(self, tmp_path):
        """Das Feld station ist 5."""
        job = _create_valid_job()
        calibration = get_default_calibration()
        rng = create_rng(42)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        station = Station5Cleanup(job, output_dir, calibration, rng)
        station.run()

        json_file = output_dir / "station5_cleanup.json"
        data = json.loads(json_file.read_text())
        assert data["station"] == 5

    def test_station5_name_ist_cleanup(self, tmp_path):
        """Das Feld name ist 'Cleanup'."""
        job = _create_valid_job()
        calibration = get_default_calibration()
        rng = create_rng(42)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        station = Station5Cleanup(job, output_dir, calibration, rng)
        station.run()

        json_file = output_dir / "station5_cleanup.json"
        data = json.loads(json_file.read_text())
        assert data["name"] == "Cleanup"

    def test_station5_estop_wirft_exception(self, tmp_path, monkeypatch):
        """Bei E-Stop wird EStopTriggered geworfen und kein JSON geschrieben."""
        estop_file = tmp_path / "ESTOP.flag"
        estop_file.touch()
        monkeypatch.setattr(config, "ESTOP_FLAG_FILE", estop_file)

        job = _create_valid_job()
        calibration = get_default_calibration()
        rng = create_rng(42)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        station = Station5Cleanup(job, output_dir, calibration, rng)

        with pytest.raises(EStopTriggered):
            station.run()

        json_file = output_dir / "station5_cleanup.json"
        assert not json_file.exists()
