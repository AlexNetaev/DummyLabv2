"""Temperature model for OrbusSim Dummy V2 - PT1 thermal inertia simulation."""
import math


def calculate_temperature(
    t_s: float,
    target_temp_c: float,
    ambient_temp_c: float = 22.0,
    tau_s: float = 12.0
) -> float:
    """Berechnet die Temperatur zum Zeitpunkt t_s (exponentielle Annäherung)."""
    # T(t) = target - (target - ambient) * exp(-t / tau)
    return target_temp_c - (target_temp_c - ambient_temp_c) * math.exp(-t_s / tau_s)


def calculate_heater_power(
    current_temp_c: float,
    target_temp_c: float,
    max_power_w: float = 5.0
) -> float:
    """Schätzt die Heizleistung (proportional zur Regelabweichung, min 0)."""
    error = target_temp_c - current_temp_c
    # Einfaches P-Verhalten: 100% Leistung bei > 5°C Fehler, linear abfallend
    power_fraction = max(0.0, min(1.0, error / 5.0))
    return power_fraction * max_power_w
