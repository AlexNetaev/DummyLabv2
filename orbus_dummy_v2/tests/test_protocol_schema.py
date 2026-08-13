"""Tests for protocol_schema models."""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from models.protocol_schema import (
    TargetParameters,
    AchievedRawParameters,
    FaultDetail,
    StationLog,
    HardwareProtocol,
)


class TestTargetParameters:
    """Tests for TargetParameters model."""
    
    def test_valid_target_parameters(self):
        """Test valid target parameters."""
        params = TargetParameters(
            target_temperature_c=37.0,
            mixing_speed_rpm=300.0,
            mixing_time_s=60.0,
            heating_time_s=300.0,
            fluorescence_duration_s=120.0,
            measurement_interval_ms=1000,
            excitation_wavelength_nm=490.0,
            emission_wavelength_nm=520.0,
        )
        assert params.target_temperature_c == 37.0
        assert params.mixing_speed_rpm == 300.0


class TestAchievedRawParameters:
    """Tests for AchievedRawParameters model."""
    
    def test_valid_with_all_fields(self):
        """Test valid achieved parameters with all fields."""
        params = AchievedRawParameters(
            mean_temperature_c=36.5,
            final_temperature_c=37.0,
            fluorescence_raw_initial_au=10.0,
            fluorescence_raw_final_au=15.0,
            fluorescence_raw_mean_au=12.5,
            fluorescence_raw_auc_au_s=1500.0,
            fluorescence_raw_slope_au_per_s=0.05,
            temperature_points=100,
            fluorescence_points=120,
        )
        assert params.mean_temperature_c == 36.5
        assert params.fluorescence_points == 120
    
    def test_valid_with_no_fields(self):
        """Test valid achieved parameters with no fields (all optional)."""
        params = AchievedRawParameters()
        assert params.mean_temperature_c is None
        assert params.fluorescence_points is None
    
    def test_ph_calculated_rejected(self):
        """Test that ph_calculated field is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AchievedRawParameters(
                mean_temperature_c=36.5,
                ph_calculated=7.4,
            )
        assert "extra" in str(exc_info.value).lower() or "ph_calculated" in str(exc_info.value)
    
    def test_ph_end_rejected(self):
        """Test that ph_end field is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AchievedRawParameters(ph_end=7.2)
        assert "extra" in str(exc_info.value).lower() or "ph_end" in str(exc_info.value)
    
    def test_target_ph_end_rejected(self):
        """Test that target_ph_end field is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AchievedRawParameters(target_ph_end=7.4)
        assert "extra" in str(exc_info.value).lower() or "target_ph_end" in str(exc_info.value)
    
    def test_achieved_ph_end_rejected(self):
        """Test that achieved_ph_end field is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AchievedRawParameters(achieved_ph_end=7.3)
        assert "extra" in str(exc_info.value).lower() or "achieved_ph_end" in str(exc_info.value)
    
    def test_fe2_concentration_um_rejected(self):
        """Test that fe2_concentration_um field is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AchievedRawParameters(fe2_concentration_um=100.0)
        assert "extra" in str(exc_info.value).lower() or "fe2_concentration_um" in str(exc_info.value)
    
    def test_fluorescence_corrected_au_rejected(self):
        """Test that fluorescence_corrected_au field is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AchievedRawParameters(fluorescence_corrected_au=20.0)
        assert "extra" in str(exc_info.value).lower() or "fluorescence_corrected_au" in str(exc_info.value)
    
    def test_absorbance_ratio_rejected(self):
        """Test that absorbance_ratio field is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AchievedRawParameters(absorbance_ratio=0.85)
        assert "extra" in str(exc_info.value).lower() or "absorbance_ratio" in str(exc_info.value)
    
    def test_unknown_field_rejected(self):
        """Test that any unknown field is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AchievedRawParameters(unknown_field="should_fail")
        assert "extra" in str(exc_info.value).lower()


class TestFaultDetail:
    """Tests for FaultDetail model."""
    
    def test_valid_fault_detail(self):
        """Test valid fault detail."""
        now = datetime.now(timezone.utc)
        fault = FaultDetail(
            fault_type="SENSOR_ERROR",
            message="Temperature sensor out of range",
            station=3,
            timestamp=now,
        )
        assert fault.fault_type == "SENSOR_ERROR"
        assert fault.station == 3
        assert fault.timestamp.tzinfo is not None
    
    def test_station_out_of_range_rejected(self):
        """Test that station outside 1-5 is rejected."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            FaultDetail(
                fault_type="ERROR",
                message="Test",
                station=6,
                timestamp=now,
            )
        
        with pytest.raises(ValidationError):
            FaultDetail(
                fault_type="ERROR",
                message="Test",
                station=0,
                timestamp=now,
            )
    
    def test_empty_fault_type_rejected(self):
        """Test that empty fault_type is rejected."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            FaultDetail(
                fault_type="",
                message="Test",
                timestamp=now,
            )
    
    def test_empty_message_rejected(self):
        """Test that empty message is rejected."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            FaultDetail(
                fault_type="ERROR",
                message="",
                timestamp=now,
            )
    
    def test_naive_timestamp_converted_to_utc(self):
        """Test that naive timestamp is converted to UTC."""
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        fault = FaultDetail(
            fault_type="ERROR",
            message="Test",
            timestamp=naive_dt,
        )
        assert fault.timestamp.tzinfo is not None
        assert fault.timestamp.tzinfo == timezone.utc


class TestStationLog:
    """Tests for StationLog model."""
    
    def test_valid_station_log(self):
        """Test valid station log."""
        now = datetime.now(timezone.utc)
        log = StationLog(
            station=1,
            name="Dosing",
            status="OK",
            timestamp_start=now,
            timestamp_end=now,
            duration_s=5.0,
        )
        assert log.station == 1
        assert log.name == "Dosing"
        assert log.status == "OK"
    
    def test_station_out_of_range_rejected(self):
        """Test that station outside 1-5 is rejected."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            StationLog(
                station=6,
                name="Invalid",
                status="OK",
                timestamp_start=now,
            )
        
        with pytest.raises(ValidationError):
            StationLog(
                station=0,
                name="Invalid",
                status="OK",
                timestamp_start=now,
            )
    
    def test_negative_duration_rejected(self):
        """Test that negative duration is rejected."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            StationLog(
                station=1,
                name="Dosing",
                status="OK",
                timestamp_start=now,
                duration_s=-1.0,
            )
    
    def test_allowed_status_values(self):
        """Test that various allowed status values are accepted."""
        now = datetime.now(timezone.utc)
        for status in ["OK", "ERROR", "ABORTED_ESTOP", "SKIPPED"]:
            log = StationLog(
                station=1,
                name="Dosing",
                status=status,
                timestamp_start=now,
            )
            assert log.status == status


class TestHardwareProtocol:
    """Tests for HardwareProtocol model."""
    
    def create_valid_target_params(self):
        """Create valid target parameters."""
        return TargetParameters(
            target_temperature_c=37.0,
            mixing_speed_rpm=300.0,
            mixing_time_s=60.0,
            heating_time_s=300.0,
            fluorescence_duration_s=120.0,
            measurement_interval_ms=1000,
            excitation_wavelength_nm=490.0,
            emission_wavelength_nm=520.0,
        )
    
    def create_valid_achieved_params(self):
        """Create valid achieved parameters."""
        return AchievedRawParameters(
            mean_temperature_c=36.5,
            final_temperature_c=37.0,
            fluorescence_raw_mean_au=12.5,
            temperature_points=100,
            fluorescence_points=120,
        )
    
    def test_valid_protocol(self):
        """Test valid hardware protocol."""
        protocol = HardwareProtocol(
            job_id="job_001",
            cycle_id="cycle_001",
            total_execution_time_s=600.0,
            target_parameters=self.create_valid_target_params(),
            achieved_parameters=self.create_valid_achieved_params(),
        )
        assert protocol.job_id == "job_001"
        assert protocol.cycle_id == "cycle_001"
        assert protocol.simulator_name == "OrbusSim Dummy V2"
        assert protocol.simulator_version == "2.0.0"
        assert protocol.status == "OK"
        assert protocol.hardware_faults_detected is False
        assert protocol.calibration_loaded is True
        assert protocol.calibration_source == "internal_default"
        assert protocol.execution_timestamp.tzinfo is not None
    
    def test_hardware_faults_with_details(self):
        """Test that hardware_faults_detected can be true with fault_details."""
        now = datetime.now(timezone.utc)
        protocol = HardwareProtocol(
            job_id="job_001",
            cycle_id="cycle_001",
            total_execution_time_s=600.0,
            hardware_faults_detected=True,
            fault_details=[
                FaultDetail(
                    fault_type="SENSOR_ERROR",
                    message="Temperature sensor failed",
                    station=3,
                    timestamp=now,
                )
            ],
            target_parameters=self.create_valid_target_params(),
            achieved_parameters=self.create_valid_achieved_params(),
        )
        assert protocol.hardware_faults_detected is True
        assert len(protocol.fault_details) == 1
    
    def test_stations_log_with_five_stations(self):
        """Test that stations_log can contain five stations."""
        now = datetime.now(timezone.utc)
        protocol = HardwareProtocol(
            job_id="job_001",
            cycle_id="cycle_001",
            total_execution_time_s=600.0,
            target_parameters=self.create_valid_target_params(),
            achieved_parameters=self.create_valid_achieved_params(),
            stations_log={
                "station_1": StationLog(station=1, name="Dosing", status="OK", timestamp_start=now),
                "station_2": StationLog(station=2, name="Mixing", status="OK", timestamp_start=now),
                "station_3": StationLog(station=3, name="Reaction", status="OK", timestamp_start=now),
                "station_4": StationLog(station=4, name="Fluorescence", status="OK", timestamp_start=now),
                "station_5": StationLog(station=5, name="Cleanup", status="OK", timestamp_start=now),
            },
        )
        assert len(protocol.stations_log) == 5
    
    def test_execution_timestamp_is_utc(self):
        """Test that execution_timestamp is timezone-aware UTC."""
        protocol = HardwareProtocol(
            job_id="job_001",
            cycle_id="cycle_001",
            total_execution_time_s=600.0,
            target_parameters=self.create_valid_target_params(),
            achieved_parameters=self.create_valid_achieved_params(),
        )
        assert protocol.execution_timestamp.tzinfo is not None
    
    def test_empty_job_id_rejected(self):
        """Test that empty job_id is rejected."""
        with pytest.raises(ValidationError):
            HardwareProtocol(
                job_id="",
                cycle_id="cycle_001",
                total_execution_time_s=600.0,
                target_parameters=self.create_valid_target_params(),
                achieved_parameters=self.create_valid_achieved_params(),
            )
    
    def test_empty_cycle_id_rejected(self):
        """Test that empty cycle_id is rejected."""
        with pytest.raises(ValidationError):
            HardwareProtocol(
                job_id="job_001",
                cycle_id="",
                total_execution_time_s=600.0,
                target_parameters=self.create_valid_target_params(),
                achieved_parameters=self.create_valid_achieved_params(),
            )
    
    def test_negative_execution_time_rejected(self):
        """Test that negative total_execution_time_s is rejected."""
        with pytest.raises(ValidationError):
            HardwareProtocol(
                job_id="job_001",
                cycle_id="cycle_001",
                total_execution_time_s=-10.0,
                target_parameters=self.create_valid_target_params(),
                achieved_parameters=self.create_valid_achieved_params(),
            )
    
    def test_unknown_field_rejected(self):
        """Test that unknown fields are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            HardwareProtocol(
                job_id="job_001",
                cycle_id="cycle_001",
                total_execution_time_s=600.0,
                target_parameters=self.create_valid_target_params(),
                achieved_parameters=self.create_valid_achieved_params(),
                unknown_field="should_fail",
            )
        assert "extra" in str(exc_info.value).lower()
