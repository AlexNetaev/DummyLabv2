"""Station output schema models for OrbusSim Dummy V2.

CRITICAL DESIGN RULES:
- Station 5 is Cleanup (NO pH-Monitor station exists)
- There is NO Station 6
- NO pH fields in any output
- NO Fe²⁺ fields in any output
- NO corrected fluorescence values in any output
- Only RAW data is output
"""

from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel, Field, field_validator


class DosingReagentCommand(BaseModel):
    """Command for dosing a single reagent.
    
    IMPORTANT: No actual_volume_ul field because the dummy does not
    simulate flow measurement without real sensors.
    """
    
    name: str = Field(..., min_length=1)
    target_volume_ul: float = Field(..., ge=0)
    concentration_mm: float = Field(..., ge=0)
    dosing_time_ms: int = Field(..., ge=0)
    pump_state: str = Field(default="OK")


class Station1DosingOutput(BaseModel):
    """Output model for Station 1: Dosing."""
    
    station: int = Field(default=1)
    name: str = Field(default="Dosing")
    status: str = Field(..., min_length=1)
    timestamp_start: datetime
    timestamp_end: datetime
    reagents: List[DosingReagentCommand] = Field(..., min_length=5, max_length=5)
    total_dosing_time_ms: int = Field(..., ge=0)


class Station2MixingOutput(BaseModel):
    """Output model for Station 2: Mixing.
    
    IMPORTANT: No required achieved_rpm_avg field because no RPM sensor
    is assumed.
    """
    
    station: int = Field(default=2)
    name: str = Field(default="Mixing")
    status: str = Field(..., min_length=1)
    timestamp_start: datetime
    timestamp_end: datetime
    target_rpm: float = Field(..., ge=0)
    mixing_time_s: float = Field(..., ge=0)
    motor_state: str = Field(default="OK")


class Station3TemperaturePoint(BaseModel):
    """Single temperature measurement point for Station 3."""
    
    time_ms: int = Field(..., ge=0)
    temp_c: float
    heater_power_w: float = Field(..., ge=0)


class Station4FluorescencePoint(BaseModel):
    """Single fluorescence measurement point for Station 4.
    
    CRITICAL: Only raw fluorescence values.
    NO fields for:
    - fluorescence_corrected_au
    - bleaching_factor
    - ph
    - fe2_concentration
    """
    
    time_ms: int = Field(..., ge=0)
    fluorescence_raw_au: float = Field(..., ge=0)


class Station5CleanupOutput(BaseModel):
    """Output model for Station 5: Cleanup.
    
    NOTE: This is Station 5. There is NO Station 5 pH-Monitor.
    The former Station 6 Cleanup is now Station 5.
    """
    
    station: int = Field(default=5)
    name: str = Field(default="Cleanup")
    status: str = Field(..., min_length=1)
    timestamp_start: datetime
    timestamp_end: datetime
    rinse_cycles: int = Field(..., ge=0)
    rinse_volume_ml: float = Field(..., ge=0)
    purge_time_s: float = Field(..., ge=0)


class MeasurementPoint(BaseModel):
    """Single measurement point for measurement.csv.
    
    CRITICAL: Only these three fields are allowed.
    NO pH, Fe²⁺, absorbance, or correction fields.
    """
    
    time_ms: int = Field(..., ge=0)
    temp_c: float
    fluorescence_raw_au: float = Field(..., ge=0)
