"""Calibration schema models for OrbusSim Dummy V2.

These models are for INTERNAL simulation only.
They may contain chemical and optical parameters, but they must NOT define
any output fields for pH, Fe²⁺, or corrected fluorescence.
"""

from typing import Optional
from pydantic import BaseModel, Field


class SpectralOverlapCalibration(BaseModel):
    """Calibration for spectral overlap effects."""
    
    model_config = {"extra": "forbid"}
    
    scatter_490nm_fraction: float = Field(default=0.02, ge=0)
    raman_water_fraction: float = Field(default=0.005, ge=0)


class OpticalCalibration(BaseModel):
    """Optical calibration parameters for internal simulation."""
    
    model_config = {"extra": "forbid"}
    
    fluorophore: str = Field(default="Fluorescein")
    pka: float = Field(default=6.4)
    epsilon_490nm: float = Field(default=76900, ge=0)
    epsilon_450nm: float = Field(default=11500, ge=0)
    quantum_yield_ref: float = Field(default=0.93, ge=0, le=1)
    t_ref_c: float = Field(default=25.0)
    ea_quench_j_per_mol: float = Field(default=12500, ge=0)
    k_bleach_per_s: float = Field(default=0.0008, ge=0)
    excitation_power_mw: float = Field(default=2.5, ge=0)
    pathlength_cm: float = Field(default=1.0, gt=0)
    k_sv_fe2: float = Field(default=0.035, ge=0)
    autofluorescence_blank_au: float = Field(default=3.2, ge=0)
    detector_dark_au: float = Field(default=0.5, ge=0)
    detector_gain: float = Field(default=1.0, gt=0)
    fluorescence_scale_au_per_um: float = Field(default=5.0, ge=0)
    spectral_overlap: SpectralOverlapCalibration = Field(
        default_factory=SpectralOverlapCalibration
    )


class ReactionCalibration(BaseModel):
    """Reaction calibration parameters for internal simulation."""
    
    model_config = {"extra": "forbid"}
    
    ph_start: float = Field(default=7.4)
    delta_ph_max: float = Field(default=2.0, ge=0)
    k_redox_per_s: float = Field(default=0.08, ge=0)
    k_ph_per_s: float = Field(default=0.06, ge=0)
    fe2_max_um_per_mm_fecl3: float = Field(default=500.0, ge=0)
    activation_energy_j_per_mol: float = Field(default=25000, ge=0)


class CalibrationData(BaseModel):
    """Top-level calibration data container."""
    
    model_config = {"extra": "forbid"}
    
    version: str = Field(default="orbus_dummy_v2")
    optical: OpticalCalibration
    reaction: ReactionCalibration
