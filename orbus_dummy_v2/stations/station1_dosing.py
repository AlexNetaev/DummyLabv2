"""Station 1: Dosing - Dispensiert Reagenzien."""

import time
from pathlib import Path
import random

from .base_station import BaseStation, EStopTriggered
from ..models import ExperimentJob, CalibrationData, DosingReagentCommand, Station1DosingOutput
from ..io import write_json_atomic


class Station1Dosing(BaseStation):
    """Station 1: Dosing."""
    
    def __init__(self, job: ExperimentJob, output_dir: Path, calibration: CalibrationData, rng: random.Random):
        super().__init__(job, output_dir, calibration, rng)
    
    def run(self) -> dict:
        """Führt die Dosing-Station aus."""
        self.check_estop()
        
        reagents_output = []
        total_dosing_time_ms = 0
        
        for reagent in self.job.parameters.reagents:
            # Simulierte dosing_time_ms basierend auf Volumen
            dosing_time_ms = int(reagent.volume_ul * 1.5 + 100)
            total_dosing_time_ms += dosing_time_ms
            
            cmd = DosingReagentCommand(
                name=reagent.reagent_name,
                target_volume_ul=reagent.volume_ul,
                concentration_mm=reagent.concentration_mm,
                dosing_time_ms=dosing_time_ms,
                pump_state="OK"
            )
            reagents_output.append(cmd)
        
        end_time = time.time()
        duration_s = end_time - self.start_time.timestamp()
        
        output_model = Station1DosingOutput(
            station=1,
            name="Dosing",
            status="OK",
            timestamp_start=self.start_time,
            timestamp_end=self.start_time.replace(second=int(self.start_time.second) + int(duration_s)),
            reagents=reagents_output,
            total_dosing_time_ms=total_dosing_time_ms
        )
        
        write_json_atomic(self.output_dir / "station1_dosing.json", output_model)
        
        # Kurze Pause für Dateisystem-Flushing
        time.sleep(0.05)
        
        return {
            "status": "OK",
            "duration_s": duration_s,
            "reagents_count": len(reagents_output)
        }
