"""pH model for OrbusSim Dummy V2 - pH drop simulation through H+ release."""
from ..models import ReactionCalibration


def calculate_ph(
    t_s: float,
    initial_ph: float,
    fe2_concentration_um: float,
    buffer_capacity_mm: float,
    params: ReactionCalibration
) -> float:
    """Berechnet den pH-Wert."""
    # pH sinkt proportional zur Fe2+ Entstehung (H+ Freisetzung)
    # Pufferkapazität dämpft den Abfall
    ph_drop_per_um_fe2 = 0.002  # Empirischer Faktor
    buffer_factor = 1.0 / (1.0 + buffer_capacity_mm / 10.0)  # Höherer Puffer = weniger pH-Änderung
    
    ph_drop = fe2_concentration_um * ph_drop_per_um_fe2 * buffer_factor
    ph_drop = min(ph_drop, params.delta_ph_max)
    
    return initial_ph - ph_drop
