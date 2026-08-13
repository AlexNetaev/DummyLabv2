"""Tests for path_resolver module."""
import pytest
from pathlib import Path

from orbus_dummy_v2.models import ExperimentJob, ExperimentParameters, ReagentDose
from orbus_dummy_v2.io.path_resolver import resolve_output_dir
from orbus_dummy_v2 import config


def _create_mock_job(cycle_id: str = "TestCycle", target_output_dir: str = None) -> ExperimentJob:
    """Hilfsfunktion zum Erstellen eines Mock-Jobs."""
    reagents = [
        ReagentDose(reagent_name="ascorbic_acid", volume_ul=100.0, concentration_mm=10.0),
        ReagentDose(reagent_name="fecl3", volume_ul=100.0, concentration_mm=1.0),
        ReagentDose(reagent_name="h2o2", volume_ul=100.0, concentration_mm=50.0),
        ReagentDose(reagent_name="fluorescein", volume_ul=100.0, concentration_mm=0.01),
        ReagentDose(reagent_name="phosphate_buffer", volume_ul=100.0, concentration_mm=50.0),
    ]
    params = ExperimentParameters(
        reagents=reagents,
        mixing_speed_rpm=500,
        mixing_time_s=30.0,
        target_temperature_c=37.0,
        heating_time_s=60.0,
        measurement_interval_ms=500,
        fluorescence_duration_s=30.0
    )
    return ExperimentJob(
        job_id="test_job_001",
        cycle_id=cycle_id,
        parameters=params,
        target_output_dir=target_output_dir
    )


def test_resolve_output_dir_default(tmp_path, monkeypatch):
    """Testet den Standardpfad wenn target_output_dir nicht gesetzt ist."""
    # Patche RESEARCH_CYCLES_DIR auf tmp_path
    monkeypatch.setattr(config, "RESEARCH_CYCLES_DIR", tmp_path)
    
    job = _create_mock_job(cycle_id="Cycle_001")
    output_dir = resolve_output_dir(job)
    
    expected = tmp_path / "Cycle_001" / "B_Hardware"
    assert output_dir == expected
    assert output_dir.exists()
    assert output_dir.is_dir()


def test_resolve_output_dir_creates_parents(tmp_path, monkeypatch):
    """Testet dass übergeordnete Verzeichnisse erstellt werden."""
    monkeypatch.setattr(config, "RESEARCH_CYCLES_DIR", tmp_path)
    
    job = _create_mock_job(cycle_id="Deep/Nested/Cycle")
    output_dir = resolve_output_dir(job)
    
    assert output_dir.exists()
    assert output_dir.is_dir()


def test_resolve_output_dir_custom_path(tmp_path, monkeypatch):
    """Testet einen benutzerdefinierten Pfad."""
    monkeypatch.setattr(config, "WORKSPACE_ROOT", tmp_path)
    monkeypatch.setattr(config, "RESEARCH_CYCLES_DIR", tmp_path / "02_Research_Cycles")
    
    custom_dir = "custom_output"
    job = _create_mock_job(cycle_id="Ignored", target_output_dir=custom_dir)
    output_dir = resolve_output_dir(job)
    
    expected = tmp_path / custom_dir
    assert output_dir == expected
    assert output_dir.exists()
