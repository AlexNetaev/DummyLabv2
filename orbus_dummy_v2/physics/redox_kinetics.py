"""Redox kinetics model for OrbusSim Dummy V2 - Fe3+ to Fe2+ conversion."""
import math
from ..models import ReactionCalibration


def calculate_fe2_concentration(
    t_s: float,
    fe3_initial_mm: float,
    ascorbic_acid_mm: float,
    h2o2_mm: float,
    temp_c: float,
    params: ReactionCalibration
) -> float:
    """Berechnet die Fe2+ Konzentration in µM."""
    # Basis-Kinetik: Sättigungskurve
    # Arrhenius-Temperaturabhängigkeit für die Rate
    R_GAS = 8.314
    T_kelvin = temp_c + 273.15
    T_ref_kelvin = 25.0 + 273.15
    temp_factor = math.exp(-params.activation_energy_j_per_mol / R_GAS * (1.0/T_kelvin - 1.0/T_ref_kelvin))
    
    k_eff = params.k_redox_per_s * temp_factor
    fe2_max_um = fe3_initial_mm * params.fe2_max_um_per_mm_fecl3
    
    # Limitierend ist das Substrat (Ascorbinsäure/H2O2), aber wir vereinfachen zu einer Sättigung
    fe2_um = fe2_max_um * (1.0 - math.exp(-k_eff * t_s))
    return max(0.0, fe2_um)
