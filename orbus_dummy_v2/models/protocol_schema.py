"""Protocol schema models for OrbusSim Dummy V2.

These models describe the final hardware_protocol.json output.

CRITICAL RULE: No derived chemical quantities in output.
The following fields MUST NOT appear:
- ph_calculated
- ph_end
- target_ph_end
- achieved_ph_end
- fe2_concentration_um
- fluorescence_corrected_au
- absorbance_ratio
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class TargetParameters(BaseModel):
    """Target parameters for the experiment."""
    
    target_temperature_c: float
    mixing_speed_rpm: float
    mixing_time_s: float
    heating_time_s: float
    fluorescence_duration_s: float
    measurement_interval_ms: int
    excitation_wavelength_nm: float
    emission_wavelength_nm: float


class AchievedRawParameters(BaseModel):
    """Achieved raw parameters - NO derived chemical quantities allowed.
    
    This model explicitly forbids extra fields to prevent accidental
    inclusion of pH, Fe²⁺, or corrected fluorescence values.
    """
    
    model_config = {"extra": "forbid"}
    
    mean_temperature_c: Optional[float] = None
    final_temperature_c: Optional[float] = None
    fluorescence_raw_initial_au: Optional[float] = None
    fluorescence_raw_final_au: Optional[float] = None
    fluorescence_raw_mean_au: Optional[float] = None
    fluorescence_raw_auc_au_s: Optional[float] = None
    fluorescence_raw_slope_au_per_s: Optional[float] = None
    temperature_points: Optional[int] = None
    fluorescence_points: Optional[int] = None


class FaultDetail(BaseModel):
    """Details about a hardware fault."""
    
    fault_type: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    station: Optional[int] = Field(default=None, ge=1, le=5)
    timestamp: datetime
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp_utc(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware UTC."""
        if v.tzinfo is None:
            # Assume UTC if naive
            return v.replace(tzinfo=timezone.utc)
        return v


class StationLog(BaseModel):
    """Log entry for a station execution.
    
    Allowed status values (not enforced as enum):
    - OK
    - ERROR
    - ABORTED_ESTOP
    - SKIPPED
    """
    
    station: int = Field(..., ge=1, le=5)
    name: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    timestamp_start: Optional[datetime] = None
    timestamp_end: Optional[datetime] = None
    duration_s: Optional[float] = Field(default=None, ge=0)
    details: Dict = Field(default_factory=dict)


class HardwareProtocol(BaseModel):
    """Top-level hardware protocol model for hardware_protocol.json output."""
    
    model_config = {"extra": "forbid"}
    
    job_id: str = Field(..., min_length=1)
    cycle_id: str = Field(..., min_length=1)
    execution_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    simulator_name: str = Field(default="OrbusSim Dummy V2")
    simulator_version: str = Field(default="2.0.0")
    status: str = Field(default="OK")
    total_execution_time_s: float = Field(..., ge=0)
    hardware_faults_detected: bool = Field(default=False)
    fault_details: List[FaultDetail] = Field(default_factory=list)
    target_parameters: TargetParameters
    achieved_parameters: AchievedRawParameters
    stations_log: Dict[str, StationLog] = Field(default_factory=dict)
    simulation_seed: Optional[int] = None
    calibration_loaded: bool = Field(default=True)
    calibration_source: str = Field(default="internal_default")
    output_files: List[str] = Field(default_factory=list)
