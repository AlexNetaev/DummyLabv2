"""Station 4: Fluorescence measurement with full physics simulation."""
from pathlib import Path
import time
import random
from datetime import datetime, timezone

from .base_station import BaseStation, EStopTriggered
from ..models import ExperimentJob, CalibrationData, Station4FluorescencePoint
from ..models.station_output_schema import Station4FluorescenceOutput
from ..io import write_csv_atomic
from .. import config
from ..physics import (
    redox_kinetics,
    ph_model,
    fluorescence_model,
    photobleaching,
    optical_effects,
    noise as noise_module,
)


class Station4Fluorescence(BaseStation):
    """Simuliert die Fluoreszenzmessung mit realistischer Physik."""

    def __init__(
        self,
        job: ExperimentJob,
        output_dir: Path,
        calibration: CalibrationData,
        rng: random.Random,
    ):
        super().__init__(job, output_dir, calibration, rng)

    def run(self) -> dict:
        """Führt die Fluoreszenzmessung aus."""
        self.check_estop()

        params = self.job.parameters
        duration_s = params.fluorescence_duration_s
        interval_ms = params.measurement_interval_ms
        target_temp = params.target_temperature_c

        # Reagenzien extrahieren
        reagents = {r.reagent_name.strip().lower(): r for r in params.reagents}

        # Konzentrationen extrahieren (mit Defaults)
        fluorescein = reagents.get("fluorescein")
        fecl3 = reagents.get("fecl3")
        phosphate_buffer = reagents.get("phosphate_buffer")
        ascorbic_acid = reagents.get("ascorbic_acid")
        h2o2 = reagents.get("h2o2")

        dye_concentration_um = (
            fluorescein.concentration_mm * 1000.0 if fluorescein else 10.0
        )
        fe3_initial_mm = fecl3.concentration_mm if fecl3 else 1.0
        buffer_capacity_mm = phosphate_buffer.concentration_mm if phosphate_buffer else 50.0
        ascorbic_acid_mm = ascorbic_acid.concentration_mm if ascorbic_acid else 10.0
        h2o2_mm = h2o2.concentration_mm if h2o2 else 10.0

        # Zeitpunkte generieren
        total_ms = int(duration_s * 1000)
        time_points = list(range(0, total_ms + 1, interval_ms))

        rows = []
        header = ["time_ms", "fluorescence_raw_au"]

        for time_ms in time_points:
            t_s = time_ms / 1000.0

            # Temperatur (vereinfacht: Zieltemperatur erreicht)
            temp_c = target_temp

            # Redox-Kinetik: Fe3+ -> Fe2+
            fe2_um = redox_kinetics.calculate_fe2_concentration(
                t_s=t_s,
                fe3_initial_mm=fe3_initial_mm,
                ascorbic_acid_mm=ascorbic_acid_mm,
                h2o2_mm=h2o2_mm,
                temp_c=temp_c,
                params=self.calibration.reaction,
            )

            # pH-Wert berechnen
            ph = ph_model.calculate_ph(
                t_s=t_s,
                initial_ph=self.calibration.reaction.ph_start,
                fe2_concentration_um=fe2_um,
                buffer_capacity_mm=buffer_capacity_mm,
                params=self.calibration.reaction,
            )

            # Ideale Fluoreszenz (pH-abhängig)
            ideal_fluo = fluorescence_model.calculate_ideal_fluorescence(
                ph=ph,
                dye_concentration_um=dye_concentration_um,
                temp_c=temp_c,
                params=self.calibration.optical,
            )

            # Bleaching-Faktor
            bleach_factor = photobleaching.calculate_bleaching_factor(
                t_s=t_s,
                excitation_power_mw=self.calibration.optical.excitation_power_mw,
                k_bleach_per_s=self.calibration.optical.k_bleach_per_s,
            )

            # Rohsignal mit optischen Effekten (Quenching, Inner-Filter, Autofluoreszenz)
            # Quencher-Konzentration in mM umrechnen
            quencher_mm = fe2_um / 1000.0
            raw_fluo = optical_effects.calculate_raw_fluorescence(
                ideal_fluorescence=ideal_fluo,
                bleaching_factor=bleach_factor,
                dye_concentration_um=dye_concentration_um,
                quencher_concentration_mm=quencher_mm,
                params=self.calibration.optical,
            )

            # Rauschen hinzufügen
            raw_fluo = noise_module.add_noise(
                raw_fluo, config.FLUORESCENCE_NOISE_STD_AU, self.rng
            )

            # Clamp auf >= 0
            raw_fluo = max(0.0, raw_fluo)

            rows.append([time_ms, round(raw_fluo, 2)])

        # CSV atomar schreiben
        output_file = self.output_dir / "station4_fluorescence.csv"
        write_csv_atomic(output_file, header, rows)

        # Kurze Pause für Dateisystem-Flush
        time.sleep(0.05)

        end_time = datetime.now(timezone.utc)
        duration_s = (end_time - self.start_time).total_seconds()

        return {
            "status": "OK",
            "duration_s": duration_s,
            "points": len(rows),
        }
