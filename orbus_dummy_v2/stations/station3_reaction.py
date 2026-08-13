"""Station 3: Reaction/Temperature - Heizt und inkubiert die Probe."""

import time
from pathlib import Path
import random

from .base_station import BaseStation, EStopTriggered
from ..models import ExperimentJob, CalibrationData, Station3TemperaturePoint
from ..io import write_csv_atomic
from ..physics import calculate_temperature, calculate_heater_power, add_noise
from .. import config


class Station3Reaction(BaseStation):
    """Station 3: Reaction/Temperature."""
    
    def __init__(self, job: ExperimentJob, output_dir: Path, calibration: CalibrationData, rng: random.Random):
        super().__init__(job, output_dir, calibration, rng)
    
    def run(self) -> dict:
        """Führt die Reaction/Temperature-Station aus."""
        self.check_estop()
        
        params = self.job.parameters
        target_temp_c = params.target_temperature_c
        heating_time_s = params.heating_time_s
        measurement_interval_ms = params.measurement_interval_ms
        
        # Generiere Zeitpunkte von 0 bis heating_time_s * 1000
        time_points = []
        current_ms = 0
        end_ms = int(heating_time_s * 1000)
        
        while current_ms <= end_ms:
            time_points.append(current_ms)
            current_ms += measurement_interval_ms
        
        # Berechne Temperaturwerte für jeden Zeitpunkt
        rows = []
        header = ["time_ms", "temp_c", "heater_power_w"]
        
        for time_ms in time_points:
            t_s = time_ms / 1000.0
            
            # Temperatur berechnen (PT1-Glied)
            temp_c = calculate_temperature(t_s, target_temp_c)
            
            # Noise hinzufügen
            temp_c = add_noise(temp_c, config.TEMP_NOISE_STD_C, self.rng)
            
            # Heater Power berechnen
            heater_power_w = calculate_heater_power(temp_c, target_temp_c)
            
            rows.append([time_ms, round(temp_c, 3), round(heater_power_w, 3)])
        
        # CSV schreiben
        write_csv_atomic(self.output_dir / "station3_temperature.csv", header, rows)
        
        end_time = time.time()
        duration_s = end_time - self.start_time.timestamp()
        
        # Kurze Pause für Dateisystem-Flushing
        time.sleep(0.05)
        
        return {
            "status": "OK",
            "duration_s": duration_s,
            "data_points": len(rows),
            "target_temperature_c": target_temp_c
        }
