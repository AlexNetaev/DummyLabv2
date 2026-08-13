"""Station 5: Cleanup process."""
from pathlib import Path
import time
from datetime import datetime, timezone

from .base_station import BaseStation, EStopTriggered
from ..models.station_output_schema import Station5CleanupOutput
from ..io import write_json_atomic


class Station5Cleanup(BaseStation):
    """Simuliert den Cleanup-Prozess (Spülen und Entlüften)."""

    def __init__(self, job, output_dir, calibration, rng):
        super().__init__(job, output_dir, calibration, rng)

    def run(self) -> dict:
        """Führt den Cleanup-Prozess aus."""
        self.check_estop()

        # Plausible Default-Werte für Cleanup
        rinse_cycles = 3
        rinse_volume_ml = 15.0
        purge_time_s = 5.0

        output_model = Station5CleanupOutput(
            station=5,
            name="Cleanup",
            status="OK",
            timestamp_start=self.start_time,
            timestamp_end=datetime.now(timezone.utc),
            rinse_cycles=rinse_cycles,
            rinse_volume_ml=rinse_volume_ml,
            purge_time_s=purge_time_s,
        )

        # JSON atomar schreiben
        output_file = self.output_dir / "station5_cleanup.json"
        write_json_atomic(output_file, output_model)

        # Kurze Pause für Dateisystem-Flush
        time.sleep(0.05)

        end_time = datetime.now(timezone.utc)
        duration_s = (end_time - self.start_time).total_seconds()

        return {
            "status": "OK",
            "duration_s": duration_s,
            "rinse_cycles": rinse_cycles,
        }
