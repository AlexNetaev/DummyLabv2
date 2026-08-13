"""Kalibrierungs-Loader für OrbusSim Dummy V2.

Lädt Kalibrierungsdaten aus einer JSON-Datei oder verwendet Default-Werte,
wenn die Datei nicht existiert oder ungültig ist.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from models.calibration_schema import (
    CalibrationData,
    OpticalCalibration,
    ReactionCalibration,
    SpectralOverlapCalibration,
)

logger = logging.getLogger("orbus_dummy_v2.calibration_loader")


def get_default_calibration() -> CalibrationData:
    """Erzeugt eine Default-Kalibrierung mit den Standardwerten.
    
    Diese Funktion ist idempotent und liefert bei jedem Aufruf
    äquivalente Default-Objekte.
    
    Returns:
        CalibrationData: Ein gültiges Kalibrierungsobjekt mit Default-Werten.
    """
    spectral_overlap = SpectralOverlapCalibration(
        scatter_490nm_fraction=0.02,
        raman_water_fraction=0.005,
    )
    
    optical = OpticalCalibration(
        fluorophore="Fluorescein",
        pka=6.4,
        epsilon_490nm=76900.0,
        epsilon_450nm=11500.0,
        quantum_yield_ref=0.93,
        t_ref_c=25.0,
        ea_quench_j_per_mol=12500.0,
        k_bleach_per_s=0.0008,
        excitation_power_mw=2.5,
        pathlength_cm=1.0,
        k_sv_fe2=0.035,
        autofluorescence_blank_au=3.2,
        detector_dark_au=0.5,
        detector_gain=1.0,
        fluorescence_scale_au_per_um=5.0,
        spectral_overlap=spectral_overlap,
    )
    
    reaction = ReactionCalibration(
        ph_start=7.4,
        delta_ph_max=2.0,
        k_redox_per_s=0.08,
        k_ph_per_s=0.06,
        fe2_max_um_per_mm_fecl3=500.0,
        activation_energy_j_per_mol=25000.0,
    )
    
    return CalibrationData(
        version="orbus_dummy_v2",
        optical=optical,
        reaction=reaction,
    )


def load_calibration(calibration_path: Path) -> CalibrationData:
    """Lädt Kalibrierungsdaten aus einer JSON-Datei.
    
    Wenn die Datei nicht existiert, ungültiges JSON enthält oder gegen das
    Schema verstößt, wird eine Default-Kalibrierung zurückgegeben.
    
    Diese Funktion wirft niemals Exceptions nach oben. Sie gibt immer ein
    gültiges CalibrationData-Objekt zurück.
    
    Args:
        calibration_path: Pfad zur Kalibrierungs-JSON-Datei.
        
    Returns:
        CalibrationData: Ein validiertes Kalibrierungsobjekt.
    """
    # Prüfen ob Datei existiert
    if not calibration_path.exists():
        logger.warning(f"Kalibrierungsdatei nicht gefunden: {calibration_path}. Verwende Default-Kalibrierung.")
        return get_default_calibration()
    
    # Versuch die Datei zu lesen
    try:
        with open(calibration_path, "r", encoding="utf-8") as f:
            content = f.read()
    except PermissionError:
        logger.error(f"Keine Leseberechtigung für Kalibrierungsdatei: {calibration_path}. Verwende Default-Kalibrierung.")
        return get_default_calibration()
    except Exception as e:
        logger.error(f"Fehler beim Lesen der Kalibrierungsdatei: {e}. Verwende Default-Kalibrierung.")
        return get_default_calibration()
    
    # Versuch JSON zu parsen
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Ungültiges JSON in Kalibrierungsdatei: {e}. Verwende Default-Kalibrierung.")
        return get_default_calibration()
    
    # Versuch gegen Schema zu validieren
    try:
        calibration = CalibrationData.model_validate(data)
        logger.info(f"Kalibrierung erfolgreich geladen von: {calibration_path}")
        return calibration
    except Exception as e:
        logger.error(f"Schema-Validierung fehlgeschlagen für Kalibrierungsdatei: {e}. Verwende Default-Kalibrierung.")
        return get_default_calibration()
