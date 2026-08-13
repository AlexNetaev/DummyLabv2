"""Queue management functions for job handling."""
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone


def find_next_job(queue_dir: Path) -> Optional[Path]:
    """
    Sucht nach der Datei experiment.json im queue_dir.
    Gibt den Pfad zurück oder None, wenn keine Datei existiert.
    """
    job_file = queue_dir / "experiment.json"
    if job_file.exists() and job_file.is_file():
        return job_file
    return None


def quarantine_job(job_path: Path, failed_dir: Path) -> None:
    """
    Verschiebt die Job-Datei in den failed_dir Ordner.
    Erstellt den Ordner falls nötig.
    """
    failed_dir.mkdir(parents=True, exist_ok=True)
    dest = failed_dir / job_path.name
    shutil.move(str(job_path), str(dest))


def archive_job(job_path: Path, processed_dir: Path, job_id: str) -> None:
    """
    Verschiebt die Job-Datei in den processed_dir Ordner.
    Benennt die Datei um: experiment_{job_id}_{timestamp}.json.
    """
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    new_filename = f"experiment_{job_id}_{timestamp}.json"
    dest = processed_dir / new_filename
    
    shutil.move(str(job_path), str(dest))
