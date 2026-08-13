"""Tests for queue manager functions."""
import json
from pathlib import Path
from datetime import datetime, timezone

import pytest

from orbus_dummy_v2.io.queue_manager import find_next_job, quarantine_job, archive_job


def test_find_next_job_not_found(tmp_path):
    """Testet dass None zurückgegeben wird wenn keine Datei existiert."""
    result = find_next_job(tmp_path)
    assert result is None


def test_find_next_job_found(tmp_path):
    """Testet dass der Pfad zurückgegeben wird wenn experiment.json existiert."""
    job_file = tmp_path / "experiment.json"
    job_file.write_text('{"job_id": "test"}')
    
    result = find_next_job(tmp_path)
    
    assert result == job_file


def test_find_next_job_ignores_other_files(tmp_path):
    """Testet dass nur experiment.json gefunden wird."""
    (tmp_path / "other.json").write_text('{}')
    (tmp_path / "experiment.txt").write_text('{}')
    
    result = find_next_job(tmp_path)
    assert result is None


def test_quarantine_job(tmp_path):
    """Testet das Verschieben in den failed Ordner."""
    queue_dir = tmp_path / "queue"
    failed_dir = tmp_path / "failed"
    queue_dir.mkdir()
    
    job_file = queue_dir / "experiment.json"
    job_file.write_text('{"job_id": "fail_test"}')
    
    quarantine_job(job_file, failed_dir)
    
    # Datei sollte im failed Ordner sein
    assert not job_file.exists()
    assert (failed_dir / "experiment.json").exists()
    assert (failed_dir / "experiment.json").read_text() == '{"job_id": "fail_test"}'


def test_archive_job(tmp_path):
    """Testet das Archivieren mit Umbenennung."""
    queue_dir = tmp_path / "queue"
    processed_dir = tmp_path / "processed"
    queue_dir.mkdir()
    
    job_file = queue_dir / "experiment.json"
    job_file.write_text('{"job_id": "archived_test"}')
    
    archive_job(job_file, processed_dir, "archived_test")
    
    # Original sollte weg sein
    assert not job_file.exists()
    
    # Neue Datei sollte im processed Ordner sein mit Timestamp
    files = list(processed_dir.glob("experiment_archived_test_*.json"))
    assert len(files) == 1
    
    # Inhalt prüfen
    content = files[0].read_text()
    data = json.loads(content)
    assert data["job_id"] == "archived_test"


def test_archive_job_creates_dir(tmp_path):
    """Testet dass der processed Ordner erstellt wird falls nötig."""
    queue_dir = tmp_path / "queue"
    processed_dir = tmp_path / "new_processed"  # Existiert noch nicht
    queue_dir.mkdir()
    
    job_file = queue_dir / "experiment.json"
    job_file.write_text('{}')
    
    archive_job(job_file, processed_dir, "test")
    
    assert processed_dir.exists()
