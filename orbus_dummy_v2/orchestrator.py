"""Orchestrator for OrbusSim Dummy V2 - führt Jobs aus und verwaltet die Queue."""
import time
import logging
import json
from pathlib import Path
from datetime import datetime, timezone

from . import config
from .models import ExperimentJob
from .models.calibration_schema import CalibrationData
from .io.path_resolver import resolve_output_dir
from .io.calibration_loader import load_calibration
from .io import queue_manager
from .io.json_writer import write_json_atomic
from .io.measurement_merger import merge_measurements
from .io.protocol_builder import build_and_write_protocol
from .physics.noise import create_rng
from .stations.base_station import EStopTriggered
from .stations.station1_dosing import Station1Dosing
from .stations.station2_mixing import Station2Mixing
from .stations.station3_reaction import Station3Reaction
from .stations.station4_fluorescence import Station4Fluorescence
from .stations.station5_cleanup import Station5Cleanup

logger = logging.getLogger("orbus_dummy_v2.orchestrator")


def execute_job(job_path: Path) -> None:
    """Führt einen einzelnen Job aus der Queue aus."""
    job = None
    output_dir = None
    station_logs = {}
    calibration = None
    rng = None
    
    # 1. Job laden und validieren
    try:
        with open(job_path, "r", encoding="utf-8") as f:
            job_data = json.load(f)
        
        job = ExperimentJob.model_validate(job_data)
        logger.info(f"Job {job.job_id} geladen und validiert.")
        
    except json.JSONDecodeError as e:
        logger.error(f"Ungültiges JSON in {job_path}: {e}")
        queue_manager.quarantine_job(job_path, config.FAILED_QUEUE_DIR)
        return
    except Exception as e:
        logger.error(f"Validierungsfehler für Job {job_path}: {e}")
        queue_manager.quarantine_job(job_path, config.FAILED_QUEUE_DIR)
        return
    
    # 2. Vorbereitung
    try:
        output_dir = resolve_output_dir(job)
        calibration = load_calibration(config.CALIBRATION_FILE)
        rng = create_rng(job.simulation_seed)
        station_logs = {}
        
        logger.info(f"Output-Verzeichnis: {output_dir}")
        logger.info(f"Kalibrierung geladen: {calibration.version}")
        
    except Exception as e:
        logger.error(f"Fehler bei der Vorbereitung: {e}")
        queue_manager.quarantine_job(job_path, config.FAILED_QUEUE_DIR)
        return
    
    # 3. Ausführung (Try-Block für alle Stationen)
    try:
        # Station 1: Dosing
        logger.info("Starte Station 1: Dosing")
        station_logs["station_1_dosing"] = Station1Dosing(job, output_dir, calibration, rng).run()
        time.sleep(config.STATION_PAUSE_S)
        
        # Station 2: Mixing
        logger.info("Starte Station 2: Mixing")
        station_logs["station_2_mixing"] = Station2Mixing(job, output_dir, calibration, rng).run()
        time.sleep(config.STATION_PAUSE_S)
        
        # Station 3: Reaction/Temperature
        logger.info("Starte Station 3: Reaction")
        station_logs["station_3_reaction"] = Station3Reaction(job, output_dir, calibration, rng).run()
        time.sleep(config.STATION_PAUSE_S)
        
        # Station 4: Fluorescence
        logger.info("Starte Station 4: Fluorescence")
        station_logs["station_4_fluorescence"] = Station4Fluorescence(job, output_dir, calibration, rng).run()
        time.sleep(config.STATION_PAUSE_S)
        
        # Station 5: Cleanup
        logger.info("Starte Station 5: Cleanup")
        station_logs["station_5_cleanup"] = Station5Cleanup(job, output_dir, calibration, rng).run()
        time.sleep(config.STATION_PAUSE_S)
        
        # Measurements mergen
        logger.info("Mergen der Messdaten...")
        merge_measurements(output_dir)
        
        # Protokoll schreiben
        logger.info("Schreibe Hardware-Protokoll...")
        build_and_write_protocol(job, station_logs, calibration, output_dir, status="OK")
        
        # Job archivieren
        logger.info("Archiviere Job...")
        queue_manager.archive_job(job_path, config.PROCESSED_QUEUE_DIR, job.job_id)
        logger.info(f"Job {job.job_id} erfolgreich abgeschlossen.")
        
    except EStopTriggered as e:
        logger.critical(f"E-Stop ausgelöst während Job {job.job_id}: {e}")
        # Protokoll mit E-Stop-Status schreiben
        try:
            build_and_write_protocol(
                job, 
                station_logs, 
                calibration, 
                output_dir, 
                status="ABORTED_ESTOP",
                fault_details=["E-Stop triggered"]
            )
        except Exception as proto_err:
            logger.error(f"Fehler beim Schreiben des E-Stop-Protokolls: {proto_err}")
        
        # Job in Failed-Queue verschieben
        queue_manager.quarantine_job(job_path, config.FAILED_QUEUE_DIR)
        
    except Exception as e:
        logger.error(f"Allgemeiner Fehler während Job {job.job_id}: {e}", exc_info=True)
        # Protokoll mit Error-Status schreiben
        try:
            build_and_write_protocol(
                job,
                station_logs,
                calibration,
                output_dir,
                status="ERROR",
                fault_details=[str(e)]
            )
        except Exception as proto_err:
            logger.error(f"Fehler beim Schreiben des Error-Protokolls: {proto_err}")
        
        # Job in Failed-Queue verschieben
        queue_manager.quarantine_job(job_path, config.FAILED_QUEUE_DIR)
