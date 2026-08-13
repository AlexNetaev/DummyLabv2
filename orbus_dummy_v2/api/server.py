"""FastAPI-Server für das OrbusSim Dummy V2 Dashboard."""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .. import config
from ..models.experiment_schema import ExperimentJob
from ..models.status_schema import SimulatorStatus


app = FastAPI(title="OrbusSim Dummy V2 Dashboard")

# CORS für lokales Development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EStopRequest(BaseModel):
    active: bool


class JobSubmitResponse(BaseModel):
    message: str
    job_id: str
    queue_file: str


class EStopResponse(BaseModel):
    message: str
    estop_active: bool


@app.get("/health")
def health():
    """Health-Check."""
    return {"status": "ok", "service": "orbus-dummy-v2-dashboard"}


@app.get("/api/state")
def get_state():
    """Liest den aktuellen Simulator-Status."""
    status_path = config.SYSTEM_DIR / "simulator_status.json"
    estop_active = config.ESTOP_FLAG_FILE.exists()
    
    if not status_path.exists():
        # Default-Status
        default_status = {
            "state": "IDLE",
            "estop_active": estop_active,
            "simulator_name": "OrbusSim Dummy V2",
            "simulator_version": "2.0.0",
        }
        return default_status
    
    try:
        with open(status_path, "r") as f:
            data = json.load(f)
        data["estop_active"] = estop_active
        return data
    except (json.JSONDecodeError, IOError):
        return {"state": "IDLE", "estop_active": estop_active}


@app.get("/api/queue")
def get_queue():
    """Listet Dateien in der Queue auf."""
    queue_dir = config.HARDWARE_QUEUE_DIR
    if not queue_dir.exists():
        return []
    
    files = [f.name for f in queue_dir.iterdir() if f.is_file()]
    return sorted(files)


@app.get("/api/estop")
def get_estop():
    """Gibt den E-Stop-Status zurück."""
    return {"estop_active": config.ESTOP_FLAG_FILE.exists()}


@app.post("/api/estop")
def set_estop(request: EStopRequest):
    """Aktiviert oder deaktiviert den E-Stop."""
    if request.active:
        config.ESTOP_FLAG_FILE.touch()
        message = "E-Stop activated"
    else:
        if config.ESTOP_FLAG_FILE.exists():
            config.ESTOP_FLAG_FILE.unlink()
        message = "E-Stop deactivated"
    
    return EStopResponse(message=message, estop_active=request.active)


@app.post("/api/job", response_model=JobSubmitResponse)
def submit_job(payload: dict):
    """Reicht einen neuen Job ein."""
    try:
        job = ExperimentJob.model_validate(payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Validation failed", "details": str(e)}
        )
    
    # Atomar in die Queue schreiben
    queue_file = config.HARDWARE_QUEUE_DIR / "experiment.json"
    temp_file = config.HARDWARE_QUEUE_DIR / "experiment.json.tmp"
    
    try:
        with open(temp_file, "w") as f:
            json.dump(payload, f, indent=2)
        os.replace(temp_file, queue_file)
    except IOError as e:
        if temp_file.exists():
            temp_file.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write job: {str(e)}"
        )
    
    return JobSubmitResponse(
        message="Job submitted successfully",
        job_id=job.job_id,
        queue_file="experiment.json"
    )


@app.get("/api/jobs")
def get_jobs():
    """Listet alle Cycles mit Hardware-Daten auf."""
    research_dir = config.RESEARCH_CYCLES_DIR
    if not research_dir.exists():
        return []
    
    result = []
    for cycle_dir in sorted(research_dir.iterdir()):
        if not cycle_dir.is_dir():
            continue
        
        hardware_dir = cycle_dir / "B_Hardware"
        if not hardware_dir.exists():
            continue
        
        files = [f.name for f in hardware_dir.iterdir() if f.is_file()]
        result.append({
            "cycle_id": cycle_dir.name,
            "files": sorted(files)
        })
    
    return result


@app.get("/api/jobs/{cycle_id}/files")
def get_job_files(cycle_id: str):
    """Listet Dateien eines spezifischen Cycles."""
    hardware_dir = config.RESEARCH_CYCLES_DIR / cycle_id / "B_Hardware"
    if not hardware_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cycle {cycle_id} not found"
        )
    
    files = [f.name for f in hardware_dir.iterdir() if f.is_file()]
    return sorted(files)


@app.get("/api/jobs/{cycle_id}/telemetry")
def get_telemetry(cycle_id: str):
    """Gibt Temperatur- und Fluoreszenz-Zeitreihen zurück."""
    hardware_dir = config.RESEARCH_CYCLES_DIR / cycle_id / "B_Hardware"
    
    temperature_data: List[Dict[str, Any]] = []
    fluorescence_data: List[Dict[str, Any]] = []
    
    # Temperatur lesen
    temp_file = hardware_dir / "station3_temperature.csv"
    if temp_file.exists():
        try:
            with open(temp_file, "r") as f:
                lines = f.readlines()
            # Header überspringen
            for line in lines[1:]:
                parts = line.strip().split(",")
                if len(parts) >= 2:
                    temperature_data.append({
                        "time_ms": int(parts[0]),
                        "temp_c": float(parts[1])
                    })
        except (IOError, ValueError):
            pass
    
    # Fluoreszenz lesen
    fluo_file = hardware_dir / "station4_fluorescence.csv"
    if fluo_file.exists():
        try:
            with open(fluo_file, "r") as f:
                lines = f.readlines()
            # Header überspringen
            for line in lines[1:]:
                parts = line.strip().split(",")
                if len(parts) >= 2:
                    fluorescence_data.append({
                        "time_ms": int(parts[0]),
                        "fluorescence_raw_au": float(parts[1])
                    })
        except (IOError, ValueError):
            pass
    
    return {
        "temperature": temperature_data,
        "fluorescence": fluorescence_data
    }


# Statische Dateien mounten
static_dir = Path(config.STATIC_DIR)
if not static_dir.exists():
    static_dir.mkdir(parents=True, exist_ok=True)

try:
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
except Exception:
    # Falls kein Frontend vorhanden ist, ignorieren
    pass
