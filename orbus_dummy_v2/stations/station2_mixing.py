"""Station 2: Mixing - Homogenisiert die Probe."""

import time
from pathlib import Path
import random

from .base_station import BaseStation, EStopTriggered
from ..models import ExperimentJob, CalibrationData, Station2MixingOutput
from ..io import write_json_atomic


class Station2Mixing(BaseStation):
    """Station 2: Mixing."""
    
    def __init__(self, job: ExperimentJob, output_dir: Path, calibration: CalibrationData, rng: random.Random):
        super().__init__(job, output_dir, calibration, rng)
    
    def run(self) -> dict:
        """Führt die Mixing-Station aus."""
        self.check_estop()
        
        params = self.job.parameters
        
        end_time = time.time()
        duration_s = end_time - self.start_time.timestamp()
        
        output_model = Station2MixingOutput(
            station=2,
            name="Mixing",
            status="OK",
            timestamp_start=self.start_time,
            timestamp_end=self.start_time.replace(second=int(self.start_time.second) + int(duration_s)),
            target_rpm=params.mixing_speed_rpm,
            mixing_time_s=params.mixing_time_s,
            motor_state="OK"
        )
        
        write_json_atomic(self.output_dir / "station2_mixing.json", output_model)
        
        # Kurze Pause für Dateisystem-Flushing
        time.sleep(0.05)
        
        return {
            "status": "OK",
            "duration_s": duration_s,
            "target_rpm": params.mixing_speed_rpm
        }
