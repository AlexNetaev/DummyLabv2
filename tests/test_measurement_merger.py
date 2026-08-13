"""Tests for measurement merger with linear interpolation."""
import csv
from pathlib import Path

import pytest

from orbus_dummy_v2.io.measurement_merger import merge_measurements
from orbus_dummy_v2.io.csv_writer import write_csv_atomic


def _write_dummy_csv(path: Path, header: list, rows: list):
    """Hilfsfunktion zum Schreiben von Test-CSVs."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def test_merge_measurements_basic(tmp_path):
    """Testet grundlegende Merge-Funktionalität mit Interpolation."""
    # Station 3: Zeitpunkte [0, 500, 1000], Temperaturen [20.0, 25.0, 30.0]
    temp_data = [
        [0, 20.0, 1.0],
        [500, 25.0, 2.0],
        [1000, 30.0, 3.0]
    ]
    _write_dummy_csv(tmp_path / "station3_temperature.csv", ["time_ms", "temp_c", "heater_power_w"], temp_data)
    
    # Station 4: Zeitpunkte [0, 250, 500, 750, 1000], Fluoreszenz [10.0, 12.0, 14.0, 16.0, 18.0]
    fluo_data = [
        [0, 10.0],
        [250, 12.0],
        [500, 14.0],
        [750, 16.0],
        [1000, 18.0]
    ]
    _write_dummy_csv(tmp_path / "station4_fluorescence.csv", ["time_ms", "fluorescence_raw_au"], fluo_data)
    
    rows_written = merge_measurements(tmp_path)
    
    assert rows_written == 5
    
    # Ergebnis lesen
    out_file = tmp_path / "measurement.csv"
    assert out_file.exists()
    
    with open(out_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        result = list(reader)
    
    assert len(result) == 5
    
    # Prüfe erste Zeile
    assert int(result[0]["time_ms"]) == 0
    assert float(result[0]["temp_c"]) == 20.0
    assert float(result[0]["fluorescence_raw_au"]) == 10.0
    
    # Prüfe interpolierte Zeile bei 250ms (sollte 22.5 sein)
    assert int(result[1]["time_ms"]) == 250
    temp_250 = float(result[1]["temp_c"])
    assert 22.4 < temp_250 < 22.6  # Toleranz für Rundung
    
    # Prüfe letzte Zeile
    assert int(result[4]["time_ms"]) == 1000
    assert float(result[4]["temp_c"]) == 30.0
    assert float(result[4]["fluorescence_raw_au"]) == 18.0


def test_merge_measurements_missing_temp_file(tmp_path):
    """Testet Verhalten wenn Temperaturdatei fehlt."""
    # Nur Fluoreszenz schreiben
    fluo_data = [[0, 10.0]]
    _write_dummy_csv(tmp_path / "station4_fluorescence.csv", ["time_ms", "fluorescence_raw_au"], fluo_data)
    
    with pytest.raises(FileNotFoundError):
        merge_measurements(tmp_path)


def test_merge_measurements_missing_fluo_file(tmp_path):
    """Testet Verhalten wenn Fluoreszenzdatei fehlt."""
    # Nur Temperatur schreiben
    temp_data = [[0, 20.0, 1.0]]
    _write_dummy_csv(tmp_path / "station3_temperature.csv", ["time_ms", "temp_c", "heater_power_w"], temp_data)
    
    with pytest.raises(FileNotFoundError):
        merge_measurements(tmp_path)


def test_merge_measurements_empty_fluo(tmp_path):
    """Testet Verhalten wenn Fluoreszenzdatei leer ist (nur Header)."""
    _write_dummy_csv(tmp_path / "station3_temperature.csv", ["time_ms", "temp_c", "heater_power_w"], [[0, 20.0, 1.0]])
    _write_dummy_csv(tmp_path / "station4_fluorescence.csv", ["time_ms", "fluorescence_raw_au"], [])
    
    rows_written = merge_measurements(tmp_path)
    
    assert rows_written == 0
    assert (tmp_path / "measurement.csv").exists()
