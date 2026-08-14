"""Protocol builder for OrbusSim Dummy V2."""
from pathlib import Path
import csv
from datetime import datetime, timezone
from typing import Optional

from ..models.protocol_schema import (
    HardwareProtocol,
    TargetParameters,
    AchievedRawParameters,
    StationLog,
    FaultDetail,
)
from ..models import ExperimentJob, CalibrationData
from .json_writer import write_json_atomic


def extract_achieved_parameters(output_dir: Path) -> AchievedRawParameters:
    """Liest station3_temperature.csv und station4_fluorescence.csv, um die AchievedRawParameters zu berechnen."""
    temp_data = []
    fluo_data = []
    
    # Temperaturdaten lesen
    temp_file = output_dir / "station3_temperature.csv"
    if temp_file.exists():
        with open(temp_file, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                temp_data.append({
                    "time_ms": int(row["time_ms"]),
                    "temp_c": float(row["temp_c"]),
                    "heater_power_w": float(row["heater_power_w"]),
                })
    
    # Fluoreszenzdaten lesen
    fluo_file = output_dir / "station4_fluorescence.csv"
    if fluo_file.exists():
        with open(fluo_file, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fluo_data.append({
                    "time_ms": int(row["time_ms"]),
                    "fluorescence_raw_au": float(row["fluorescence_raw_au"]),
                })
    
    # Temperatur-Statistiken berechnen
    mean_temp: Optional[float] = None
    final_temp: Optional[float] = None
    temp_points: Optional[int] = None
    
    if temp_data:
        temps = [d["temp_c"] for d in temp_data]
        mean_temp = sum(temps) / len(temps)
        final_temp = temps[-1]
        temp_points = len(temps)
    
    # Fluoreszenz-Statistiken berechnen
    fluo_initial: Optional[float] = None
    fluo_final: Optional[float] = None
    fluo_mean: Optional[float] = None
    fluo_auc: Optional[float] = None
    fluo_points: Optional[int] = None
    
    if fluo_data:
        fluo_values = [d["fluorescence_raw_au"] for d in fluo_data]
        fluo_initial = fluo_values[0]
        fluo_final = fluo_values[-1]
        fluo_mean = sum(fluo_values) / len(fluo_values)
        fluo_points = len(fluo_values)
        
        # AUC mit Trapezregel berechnen (time_ms in Sekunden umrechnen)
        auc = 0.0
        for i in range(1, len(fluo_data)):
            dt_s = (fluo_data[i]["time_ms"] - fluo_data[i-1]["time_ms"]) / 1000.0
            avg_fluo = (fluo_data[i]["fluorescence_raw_au"] + fluo_data[i-1]["fluorescence_raw_au"]) / 2.0
            auc += avg_fluo * dt_s
        fluo_auc = auc
    
    return AchievedRawParameters(
        mean_temperature_c=mean_temp,
        final_temperature_c=final_temp,
        fluorescence_raw_initial_au=fluo_initial,
        fluorescence_raw_final_au=fluo_final,
        fluorescence_raw_mean_au=fluo_mean,
        fluorescence_raw_auc_au_s=fluo_auc,
        temperature_points=temp_points,
        fluorescence_points=fluo_points,
    )


def build_and_write_protocol(
    job: ExperimentJob,
    station_logs: dict,
    calibration: CalibrationData,
    output_dir: Path,
    status: str = "OK",
    fault_details: list = None,
) -> None:
    """Erstellt und schreibt hardware_protocol.json."""
    # TargetParameters aus Job erstellen
    target_params = TargetParameters(
        target_temperature_c=job.parameters.target_temperature_c,
        mixing_speed_rpm=job.parameters.mixing_speed_rpm,
        mixing_time_s=job.parameters.mixing_time_s,
        heating_time_s=job.parameters.heating_time_s,
        fluorescence_duration_s=job.parameters.fluorescence_duration_s,
        measurement_interval_ms=job.parameters.measurement_interval_ms,
        excitation_wavelength_nm=job.parameters.excitation_wavelength_nm,
        emission_wavelength_nm=job.parameters.emission_wavelength_nm,
    )
    
    # AchievedRawParameters extrahieren
    achieved_params = extract_achieved_parameters(output_dir)
    
    # Stations-Logs in StationLog-Objekte umwandeln
    stations_log_dict = {}
    for key, log_data in station_logs.items():
        if isinstance(log_data, dict):
            # Extrahiere Stationsnummer aus dem Key (z.B. "station_1_dosing" -> 1)
            station_num = None
            station_name = log_data.get("name", key)
            if "station_1" in key:
                station_num = 1
            elif "station_2" in key:
                station_num = 2
            elif "station_3" in key:
                station_num = 3
            elif "station_4" in key:
                station_num = 4
            elif "station_5" in key:
                station_num = 5
            
            stations_log_dict[key] = StationLog(
                station=station_num if station_num else 0,
                name=station_name,
                status=log_data.get("status", "UNKNOWN"),
                timestamp_start=log_data.get("timestamp_start"),
                timestamp_end=log_data.get("timestamp_end"),
                duration_s=max(0.0, log_data.get("duration_s", 0.0)),  # Defensive: niemals negativ
                details=log_data.get("details", {}),
            )
    
    # FaultDetails verarbeiten
    fault_detail_list = []
    if fault_details:
        for fd in fault_details:
            if isinstance(fd, str):
                fault_detail_list.append(FaultDetail(
                    fault_type="GENERAL_ERROR",
                    message=fd,
                    timestamp=datetime.now(timezone.utc),
                ))
            elif isinstance(fd, FaultDetail):
                fault_detail_list.append(fd)
    
    # HardwareProtocol erstellen
    protocol = HardwareProtocol(
        job_id=job.job_id,
        cycle_id=job.cycle_id,
        execution_timestamp=datetime.now(timezone.utc),
        simulator_name="OrbusSim Dummy V2",
        simulator_version="2.0.0",
        status=status,
        total_execution_time_s=0.0,  # Wird später ggf. berechnet
        hardware_faults_detected=len(fault_detail_list) > 0,
        fault_details=fault_detail_list,
        target_parameters=target_params,
        achieved_parameters=achieved_params,
        stations_log=stations_log_dict,
        simulation_seed=job.simulation_seed,
        calibration_loaded=True,
        calibration_source="internal_default",
        output_files=[
            "station1_dosing.json",
            "station2_mixing.json",
            "station3_temperature.csv",
            "station4_fluorescence.csv",
            "station5_cleanup.json",
            "measurement.csv",
            "hardware_protocol.json",
        ],
    )
    
    # Protokoll atomar schreiben
    write_json_atomic(output_dir / "hardware_protocol.json", protocol)
