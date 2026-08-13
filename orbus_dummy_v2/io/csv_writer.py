"""Atomic CSV writer to prevent partial reads."""
import csv
import os
from pathlib import Path
from typing import List


def write_csv_atomic(path: Path, header: List[str], rows: List[List]) -> None:
    """
    Schreibt CSV-Daten atomar.
    
    1. Schreibt in eine temporäre Datei (.tmp).
    2. Benennt die Datei atomar um (os.replace).
    
    Nutzt utf-8 Encoding und newline="" für das csv-Modul.
    """
    # Stelle sicher, dass das Verzeichnis existiert
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Temporäre Datei im selben Verzeichnis
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    
    try:
        with open(tmp_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        
        # Atomares Umbenennen
        os.replace(tmp_path, path)
    except Exception:
        # Aufräumen bei Fehler
        if tmp_path.exists():
            tmp_path.unlink()
        raise
