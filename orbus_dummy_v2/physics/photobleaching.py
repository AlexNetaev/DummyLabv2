"""Photobleaching model for OrbusSim Dummy V2."""
import math


def calculate_bleaching_factor(
    t_s: float,
    excitation_power_mw: float,
    k_bleach_per_s: float
) -> float:
    """Berechnet den Bleaching-Faktor (1.0 am Anfang, fällt exponentiell)."""
    # Faktor >= 0.01 clampen, damit das Signal nie ganz auf 0 fällt
    factor = math.exp(-k_bleach_per_s * excitation_power_mw * t_s)
    return max(0.01, factor)
