"""Basis-Klasse für alle Stationen mit E-Stop-Integration."""

from pathlib import Path
import random
from datetime import datetime, timezone

from ..models import ExperimentJob, CalibrationData
from .. import config


class EStopTriggered(Exception):
    """Wird geworfen, wenn der E-Stop während einer Station aktiviert wird."""
    pass


class BaseStation:
    """Basisklasse für alle Stationen."""
    
    def __init__(self, job: ExperimentJob, output_dir: Path, calibration: CalibrationData, rng: random.Random):
        self.job = job
        self.output_dir = output_dir
        self.calibration = calibration
        self.rng = rng
        self.start_time = datetime.now(timezone.utc)
        
    def check_estop(self):
        """Prüft, ob die E-Stop-Flag-Datei existiert."""
        if config.ESTOP_FLAG_FILE.exists():
            raise EStopTriggered(f"E-Stop flag detected before/during {self.__class__.__name__}.")
            
    def run(self) -> dict:
        """Führt die Station aus und gibt ein Log-Dictionary zurück."""
        raise NotImplementedError("Subclasses must implement run()")
