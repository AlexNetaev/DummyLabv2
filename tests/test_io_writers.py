"""Tests for JSON and CSV atomic writers."""
import json
import csv
from pathlib import Path

import pytest
from pydantic import BaseModel

from orbus_dummy_v2.io.json_writer import write_json_atomic
from orbus_dummy_v2.io.csv_writer import write_csv_atomic


class MockData(BaseModel):
    name: str
    value: int


def test_write_json_atomic(tmp_path):
    """Testet dass write_json_atomic eine gültige JSON-Datei erstellt."""
    output_path = tmp_path / "test.json"
    data = MockData(name="test", value=42)
    
    write_json_atomic(output_path, data)
    
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    parsed = json.loads(content)
    
    assert parsed["name"] == "test"
    assert parsed["value"] == 42
    # Keine .tmp Datei sollte übrig bleiben
    assert not (tmp_path / "test.json.tmp").exists()


def test_write_json_atomic_overwrites(tmp_path):
    """Testet dass eine existierende Datei überschrieben wird."""
    output_path = tmp_path / "test.json"
    output_path.write_text('{"old": "data"}')
    
    data = MockData(name="new", value=99)
    write_json_atomic(output_path, data)
    
    content = output_path.read_text(encoding="utf-8")
    parsed = json.loads(content)
    
    assert parsed["name"] == "new"
    assert parsed["value"] == 99


def test_write_csv_atomic(tmp_path):
    """Testet dass write_csv_atomic korrekte CSV-Daten schreibt."""
    output_path = tmp_path / "test.csv"
    header = ["time_ms", "value", "label"]
    rows = [
        [0, 1.5, "start"],
        [100, 2.5, "mid"],
        [200, 3.5, "end"]
    ]
    
    write_csv_atomic(output_path, header, rows)
    
    assert output_path.exists()
    
    with open(output_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        all_rows = list(reader)
    
    assert len(all_rows) == 4  # Header + 3 Datenzeilen
    assert all_rows[0] == header
    assert all_rows[1][0] == "0"
    assert all_rows[1][1] == "1.5"
    assert all_rows[3][2] == "end"
    
    # Keine .tmp Datei sollte übrig bleiben
    assert not (tmp_path / "test.csv.tmp").exists()


def test_write_csv_atomic_empty_rows(tmp_path):
    """Testet Schreiben mit leeren Rows."""
    output_path = tmp_path / "empty.csv"
    header = ["col1", "col2"]
    rows = []
    
    write_csv_atomic(output_path, header, rows)
    
    assert output_path.exists()
    with open(output_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        all_rows = list(reader)
    
    assert len(all_rows) == 1  # Nur Header
