"""Status-Schema für den Simulator."""
from datetime import datetime, timezone
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class SimulatorStatus(BaseModel):
    """Status des Simulators."""
    state: Literal["IDLE", "RUNNING", "ESTOP", "ERROR"]
    job_id: Optional[str] = None
    cycle_id: Optional[str] = None
    current_station: Optional[int] = Field(default=None, ge=1, le=5)
    current_station_name: Optional[str] = None
    stations_completed: List[str] = Field(default_factory=list)
    output_dir: Optional[str] = None
    last_job_id: Optional[str] = None
    last_job_status: Optional[str] = None
    last_error: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    simulator_name: str = "OrbusSim Dummy V2"
    simulator_version: str = "2.0.0"

    class Config:
        extra = "forbid"
