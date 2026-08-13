"""Path resolution logic for output directories."""
from pathlib import Path
from typing import Optional

from ..models import ExperimentJob
from .. import config


def resolve_output_dir(job: ExperimentJob) -> Path:
    """
    Löst das Ausgabeverzeichnis für einen Job auf.
    
    Priorität:
    1. job.target_output_dir (wenn gesetzt)
       - Wenn der Pfad '02_Research_Cycles' enthält, wird er relativ zu config.RESEARCH_CYCLES_DIR aufgelöst.
       - Sonst als absoluter oder relativer Pfad zum Workspace behandelt.
    2. Standardpfad: config.RESEARCH_CYCLES_DIR / job.cycle_id / "B_Hardware"
    
    Das Verzeichnis wird automatisch erstellt.
    """
    target = job.target_output_dir
    
    if target:
        target_path = Path(target)
        # Intelligente Auflösung wenn '02_Research_Cycles' im Pfad vorkommt
        if "02_Research_Cycles" in str(target_path):
            # Wir nehmen an, der Pfad ist relativ zum Workspace oder ein Teilpfad
            # Wir bauen ihn sicher auf Basis von RESEARCH_CYCLES_DIR auf, falls er nicht absolut ist
            if not target_path.is_absolute():
                # Extrahiere den Teil nach '02_Research_Cycles' falls vorhanden, oder nutze den ganzen Pfad
                # Einfache Logik: Wenn es relativ ist, hängen wir es an RESEARCH_CYCLES_DIR an, 
                # aber da '02_Research_Cycles' schon im Namen ist, nehmen wir den Pfad wie er ist relativ zum Root?
                # Sicherer Ansatz: Wenn es relativ ist, behandeln wir es als Unterpfad von WORKSPACE_ROOT
                resolved = config.WORKSPACE_ROOT / target_path
            else:
                resolved = target_path
        else:
            # Normaler relativer oder absoluter Pfad
            if not target_path.is_absolute():
                resolved = config.WORKSPACE_ROOT / target_path
            else:
                resolved = target_path
    else:
        # Standardpfad
        resolved = config.RESEARCH_CYCLES_DIR / job.cycle_id / "B_Hardware"
    
    # Verzeichnis erstellen
    resolved.mkdir(parents=True, exist_ok=True)
    
    return resolved
