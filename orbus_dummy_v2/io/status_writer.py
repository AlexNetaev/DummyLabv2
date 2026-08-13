"""Status-Writer für den Simulator."""
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from ..models.status_schema import SimulatorStatus
from ..models.experiment_schema import ExperimentJob
from .json_writer import write_json_atomic
from .. import config

logger = logging.getLogger("orbus_dummy_v2.status_writer")


def write_status(status: SimulatorStatus) -> None:
    """Schreibt den Status atomar nach config.SYSTEM_DIR / 'simulator_status.json'."""
    status_path = config.SYSTEM_DIR / "simulator_status.json"
    write_json_atomic(status_path, status)


def set_idle(last_job_id: Optional[str] = None, last_job_status: Optional[str] = None) -> None:
    """Setzt den Status auf IDLE."""
    status = SimulatorStatus(
        state="IDLE",
        last_job_id=last_job_id,
        last_job_status=last_job_status,
    )
    write_status(status)


def set_running(job: ExperimentJob, output_dir: Path) -> None:
    """Setzt den Status auf RUNNING."""
    status = SimulatorStatus(
        state="RUNNING",
        job_id=job.job_id,
        cycle_id=job.cycle_id,
        output_dir=str(output_dir),
    )
    write_status(status)


def set_station(
    job: ExperimentJob,
    station_number: int,
    station_name: str,
    stations_completed: list,
    output_dir: Path
) -> None:
    """Setzt den Status auf RUNNING mit aktueller Station."""
    status = SimulatorStatus(
        state="RUNNING",
        job_id=job.job_id,
        cycle_id=job.cycle_id,
        current_station=station_number,
        current_station_name=station_name,
        stations_completed=stations_completed,
        output_dir=str(output_dir),
    )
    write_status(status)


def set_estop(job_id: Optional[str] = None) -> None:
    """Setzt den Status auf ESTOP."""
    status = SimulatorStatus(
        state="ESTOP",
        job_id=job_id,
    )
    write_status(status)


def set_error(job_id: Optional[str], error_message: str) -> None:
    """Setzt den Status auf ERROR."""
    status = SimulatorStatus(
        state="ERROR",
        job_id=job_id,
        last_error=error_message,
    )
    write_status(status)
