"""Optical effects model for OrbusSim Dummy V2 - simulates systematic errors in raw detector signal."""
from ..models import OpticalCalibration


def calculate_raw_fluorescence(
    ideal_fluorescence: float,
    bleaching_factor: float,
    dye_concentration_um: float,
    quencher_concentration_mm: float,  # z.B. Fe2+ in mM
    params: OpticalCalibration
) -> float:
    """Simuliert das rohe Detektorsignal inkl. systematischer Effekte."""
    # 1. Bleaching anwenden
    signal = ideal_fluorescence * bleaching_factor
    
    # 2. Quenching durch Reaktionsprodukte (Stern-Volmer: F_0/F = 1 + K_SV * [Q])
    stern_volmer_factor = 1.0 + params.k_sv_fe2 * quencher_concentration_mm
    signal = signal / stern_volmer_factor
    
    # 3. Inner-Filter-Effekt (Selbstabsorption bei hoher Konzentration)
    A_ex = params.epsilon_490nm * dye_concentration_um * 1e-6 * params.pathlength_cm  # c in M umrechnen (µM -> M)
    A_em = params.epsilon_450nm * dye_concentration_um * 1e-6 * params.pathlength_cm
    # Korrektur nach Lakowicz (wir kehren es um, um den Signalverlust zu simulieren)
    inner_filter_loss = 10 ** (-(A_ex + A_em) / 2.0)
    signal = signal * inner_filter_loss
    
    # 4. Autofluoreszenz und Detektor-Dark-Current addieren
    raw_signal = signal + params.autofluorescence_blank_au + params.detector_dark_au
    
    return max(0.0, raw_signal)
