"""Tests für den Protocol Builder."""
import pytest
from pathlib import Path
import csv
import json

from orbus_dummy_v2.io.protocol_builder import extract_achieved_parameters, build_and_write_protocol
from orbus_dummy_v2.models.protocol_schema import AchievedRawParameters
from orbus_dummy_v2.models import ExperimentJob, CalibrationData
from orbus_dummy_v2.io.calibration_loader import get_default_calibration


def test_extract_achieved_parameters_with_both_files(tmp_path):
    """Testet die Extraktion bei vorhandenen beiden CSV-Dateien."""
    # Temperatur-CSV erstellen
    temp_file = tmp_path / "station3_temperature.csv"
    with open(temp_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time_ms", "temp_c", "heater_power_w"])
        writer.writerow([0, 22.0, 5.0])
        writer.writerow([500, 25.0, 3.0])
        writer.writerow([1000, 30.0, 1.0])
    
    # Fluoreszenz-CSV erstellen
    fluo_file = tmp_path / "station4_fluorescence.csv"
    with open(fluo_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time_ms", "fluorescence_raw_au"])
        writer.writerow([0, 10.0])
        writer.writerow([500, 15.0])
        writer.writerow([1000, 20.0])
    
    result = extract_achieved_parameters(tmp_path)
    
    assert isinstance(result, AchievedRawParameters)
    assert result.final_temperature_c == 30.0
    assert result.mean_temperature_c == (22.0 + 25.0 + 30.0) / 3
    assert result.temperature_points == 3
    assert result.fluorescence_raw_initial_au == 10.0
    assert result.fluorescence_raw_final_au == 20.0
    assert result.fluorescence_raw_mean_au == (10.0 + 15.0 + 20.0) / 3
    assert result.fluorescence_points == 3
    # AUC: Trapezregel -> (0.5 * 10 + 0.5 * 15) * 0.5 + (0.5 * 15 + 0.5 * 20) * 0.5 = 6.25 + 8.75 = 15.0
    assert abs(result.fluorescence_raw_auc_au_s - 15.0) < 0.01


def test_extract_achieved_parameters_missing_temp_file(tmp_path):
    """Testet die Extraktion wenn nur Fluoreszenz-Datei existiert."""
    # Nur Fluoreszenz-CSV erstellen
    fluo_file = tmp_path / "station4_fluorescence.csv"
    with open(fluo_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time_ms", "fluorescence_raw_au"])
        writer.writerow([0, 10.0])
        writer.writerow([500, 15.0])
    
    result = extract_achieved_parameters(tmp_path)
    
    assert result.mean_temperature_c is None
    assert result.final_temperature_c is None
    assert result.temperature_points is None
    assert result.fluorescence_raw_initial_au == 10.0
    assert result.fluorescence_points == 2


def test_extract_achieved_parameters_missing_fluo_file(tmp_path):
    """Testet die Extraktion wenn nur Temperatur-Datei existiert."""
    # Nur Temperatur-CSV erstellen
    temp_file = tmp_path / "station3_temperature.csv"
    with open(temp_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time_ms", "temp_c", "heater_power_w"])
        writer.writerow([0, 22.0, 5.0])
    
    result = extract_achieved_parameters(tmp_path)
    
    assert result.mean_temperature_c == 22.0
    assert result.final_temperature_c == 22.0
    assert result.fluorescence_raw_initial_au is None
    assert result.fluorescence_raw_final_au is None
    assert result.fluorescence_points is None


def test_build_and_write_protocol(tmp_path):
    """Testet das Erstellen und Schreiben des Hardware-Protokolls."""
    # Dummy-Job erstellen
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
            "mixing_time_s": 30.0,
            "target_temperature_c": 37.0,
            "heating_time_s": 60.0,
            "measurement_interval_ms": 500,
            "fluorescence_duration_s": 120.0,
            "excitation_wavelength_nm": 490,
            "emission_wavelength_nm": 520,
        },
        "station_4_action": "FLUORESCENCE",
    }
    job = ExperimentJob.model_validate(job_data)
    calibration = get_default_calibration()
    station_logs = {
        "station_1_dosing": {"status": "OK", "name": "Dosing", "duration_s": 1.5},
    }
    
    build_and_write_protocol(job, station_logs, calibration, tmp_path, status="OK")
    
    protocol_file = tmp_path / "hardware_protocol.json"
    assert protocol_file.exists()
    
    with open(protocol_file, "r", encoding="utf-8") as f:
        protocol_data = json.load(f)
    
    assert protocol_data["job_id"] == "test-job-001"
    assert protocol_data["cycle_id"] == "Cycle_001"
    assert protocol_data["status"] == "OK"
    assert protocol_data["simulator_name"] == "OrbusSim Dummy V2"
    assert protocol_data["target_parameters"]["target_temperature_c"] == 37.0
    assert protocol_data["target_parameters"]["mixing_speed_rpm"] == 500
