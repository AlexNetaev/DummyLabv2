"""Fluorescence model for OrbusSim Dummy V2 - ideal fluorescence based on pH (Henderson-Hasselbalch)."""
import math
from ..models import OpticalCalibration


def calculate_ideal_fluorescence(
    ph: float,
    dye_concentration_um: float,
    temp_c: float,
    params: OpticalCalibration
) -> float:
    """Berechnet die ideale Fluoreszenz (ohne systematische Fehler)."""
    # Henderson-Hasselbalch für Fluorescein (pKa ~ 6.4)
    # Anteil der fluoreszierenden (deprotonierten) Form:
    ratio = 10 ** (ph - params.pka)
    fraction_deprotonated = ratio / (1.0 + ratio)
    
    # Basis-Signal proportional zur Konzentration und Quantenausbeute
    base_signal = dye_concentration_um * params.fluorescence_scale_au_per_um * fraction_deprotonated * params.quantum_yield_ref
    
    return max(0.0, base_signal)
