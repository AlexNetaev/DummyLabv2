"""Experiment input schema models for OrbusSim Dummy V2."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class ReagentDose(BaseModel):
    """Model for a single reagent dose command."""
    
    model_config = {"extra": "forbid"}
    
    reagent_name: str = Field(..., min_length=1)
    volume_ul: float = Field(..., ge=0)
    concentration_mm: float = Field(..., ge=0)


class ExperimentParameters(BaseModel):
    """Parameters for an experiment job."""
    
    model_config = {"extra": "forbid"}
    
    reagents: List[ReagentDose] = Field(..., min_length=5, max_length=5)
    mixing_speed_rpm: float = Field(..., ge=0, le=5000)
    mixing_time_s: float = Field(..., ge=0, le=3600)
    target_temperature_c: float = Field(..., ge=0, le=99)
    heating_time_s: float = Field(..., ge=0, le=3600)
    measurement_interval_ms: int = Field(..., ge=50, le=5000)
    fluorescence_duration_s: float = Field(..., ge=5, le=600)
    excitation_wavelength_nm: float = Field(default=490.0, ge=200, le=900)
    emission_wavelength_nm: float = Field(default=520.0, ge=200, le=1000)
    
    @field_validator('reagents')
    @classmethod
    def validate_reagents(cls, v: List[ReagentDose]) -> List[ReagentDose]:
        """Validate that exactly 5 unique required reagents are present."""
        if len(v) != 5:
            raise ValueError("Exactly 5 reagents are required")
        
        required_reagents = {
            "ascorbic_acid",
            "fecl3",
            "h2o2",
            "fluorescein",
            "phosphate_buffer"
        }
        
        seen_names = set()
        for reagent in v:
            # Normalize name: lowercase and strip whitespace
            normalized_name = reagent.reagent_name.lower().strip()
            
            if normalized_name in seen_names:
                raise ValueError(f"Duplicate reagent: {reagent.reagent_name}")
            seen_names.add(normalized_name)
            
            if normalized_name not in required_reagents:
                raise ValueError(f"Unknown reagent: {reagent.reagent_name}")
        
        # Check all required reagents are present
        if seen_names != required_reagents:
            missing = required_reagents - seen_names
            raise ValueError(f"Missing required reagents: {missing}")
        
        return v
    
    @model_validator(mode='after')
    def validate_wavelengths(self) -> 'ExperimentParameters':
        """Ensure emission wavelength is greater than excitation wavelength."""
        if self.emission_wavelength_nm <= self.excitation_wavelength_nm:
            raise ValueError(
                f"emission_wavelength_nm ({self.emission_wavelength_nm}) must be "
                f"greater than excitation_wavelength_nm ({self.excitation_wavelength_nm})"
            )
        return self


class ExperimentJob(BaseModel):
    """Top-level experiment job model."""
    
    model_config = {"extra": "ignore"}
    
    job_id: str = Field(..., min_length=1)
    cycle_id: str = Field(..., min_length=1)
    target_output_dir: Optional[str] = Field(default=None)
    parameters: ExperimentParameters
    station_4_action: str = Field(default="FLUORESCENCE", min_length=1)
    simulation_seed: Optional[int] = Field(default=None, ge=0)
