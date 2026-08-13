"""Atomic JSON writer to prevent partial reads."""
import os
from pathlib import Path
from pydantic import BaseModel


def write_json_atomic(path: Path, data: BaseModel) -> None:
    """
    Schreibt ein Pydantic-Modell atomar als JSON-Datei.
    
    1. Serialisiert das Modell mit model_dump_json(indent=2).
    2. Schreibt in eine temporäre Datei (.tmp).
    3. Benennt die Datei atomar um (os.replace).
    """
    # Stelle sicher, dass das Verzeichnis existiert
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Temporäre Datei im selben Verzeichnis
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    
    try:
        content = data.model_dump_json(indent=2)
        tmp_path.write_text(content, encoding="utf-8")
        # Atomares Umbenennen
        os.replace(tmp_path, path)
    except Exception:
        # Aufräumen bei Fehler
        if tmp_path.exists():
            tmp_path.unlink()
        raise
