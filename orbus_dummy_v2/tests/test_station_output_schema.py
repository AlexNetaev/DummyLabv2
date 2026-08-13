"""Tests for station_output_schema models."""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError, BaseModel

from models.station_output_schema import (
    DosingReagentCommand,
    Station1DosingOutput,
    Station2MixingOutput,
    Station3TemperaturePoint,
    Station4FluorescencePoint,
    Station5CleanupOutput,
    MeasurementPoint,
)


class TestDosingReagentCommand:
    """Tests for DosingReagentCommand model."""
    
    def test_valid_command(self):
        """Test valid dosing command."""
        cmd = DosingReagentCommand(
            name="ascorbic_acid",
            target_volume_ul=100.0,
            concentration_mm=10.0,
            dosing_time_ms=5000,
        )
        assert cmd.name == "ascorbic_acid"
        assert cmd.target_volume_ul == 100.0
        assert cmd.pump_state == "OK"
    
    def test_no_actual_volume_field(self):
        """Test that actual_volume_ul field does not exist."""
        # The model should not have this field
        fields = DosingReagentCommand.model_fields
        assert "actual_volume_ul" not in fields
    
    def test_negative_volume_rejected(self):
        """Test that negative volume is rejected."""
        with pytest.raises(ValidationError):
            DosingReagentCommand(
                name="ascorbic_acid",
                target_volume_ul=-10.0,
                concentration_mm=10.0,
                dosing_time_ms=5000,
            )
    
    def test_empty_name_rejected(self):
        """Test that empty name is rejected."""
        with pytest.raises(ValidationError):
            DosingReagentCommand(
                name="",
                target_volume_ul=100.0,
                concentration_mm=10.0,
                dosing_time_ms=5000,
            )


class TestStation1DosingOutput:
    """Tests for Station1DosingOutput model."""
    
    def create_valid_reagents(self):
        """Create 5 valid reagent commands."""
        return [
            DosingReagentCommand(name="ascorbic_acid", target_volume_ul=100.0, concentration_mm=10.0, dosing_time_ms=5000),
            DosingReagentCommand(name="fecl3", target_volume_ul=50.0, concentration_mm=5.0, dosing_time_ms=2500),
            DosingReagentCommand(name="h2o2", target_volume_ul=75.0, concentration_mm=2.0, dosing_time_ms=3750),
            DosingReagentCommand(name="fluorescein", target_volume_ul=25.0, concentration_mm=0.1, dosing_time_ms=1250),
            DosingReagentCommand(name="phosphate_buffer", target_volume_ul=200.0, concentration_mm=50.0, dosing_time_ms=10000),
        ]
    
    def test_valid_output(self):
        """Test valid station 1 output."""
        now = datetime.now(timezone.utc)
        output = Station1DosingOutput(
            status="OK",
            timestamp_start=now,
            timestamp_end=now,
            reagents=self.create_valid_reagents(),
            total_dosing_time_ms=22500,
        )
        assert output.station == 1
        assert output.name == "Dosing"
        assert len(output.reagents) == 5
    
    def test_exactly_five_reagents_required(self):
        """Test that exactly 5 reagents are required."""
        now = datetime.now(timezone.utc)
        
        # Too few reagents
        with pytest.raises(ValidationError):
            Station1DosingOutput(
                status="OK",
                timestamp_start=now,
                timestamp_end=now,
                reagents=self.create_valid_reagents()[:4],
                total_dosing_time_ms=17500,
            )
        
        # Too many reagents
        extra_reagents = self.create_valid_reagents()
        extra_reagents.append(
            DosingReagentCommand(name="extra", target_volume_ul=10.0, concentration_mm=1.0, dosing_time_ms=500)
        )
        with pytest.raises(ValidationError):
            Station1DosingOutput(
                status="OK",
                timestamp_start=now,
                timestamp_end=now,
                reagents=extra_reagents,
                total_dosing_time_ms=23000,
            )
    
    def test_no_actual_volume_ul_field(self):
        """Test that no reagent has actual_volume_ul field."""
        for reagent in self.create_valid_reagents():
            fields = DosingReagentCommand.model_fields
            assert "actual_volume_ul" not in fields


class TestStation2MixingOutput:
    """Tests for Station2MixingOutput model."""
    
    def test_valid_output(self):
        """Test valid station 2 output."""
        now = datetime.now(timezone.utc)
        output = Station2MixingOutput(
            status="OK",
            timestamp_start=now,
            timestamp_end=now,
            target_rpm=300.0,
            mixing_time_s=60.0,
        )
        assert output.station == 2
        assert output.name == "Mixing"
        assert output.motor_state == "OK"
    
    def test_no_required_achieved_rpm_avg_field(self):
        """Test that achieved_rpm_avg is not a required field."""
        fields = Station2MixingOutput.model_fields
        # The field should not exist or be optional
        assert "achieved_rpm_avg" not in fields
    
    def test_negative_target_rpm_rejected(self):
        """Test that negative target_rpm is rejected."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            Station2MixingOutput(
                status="OK",
                timestamp_start=now,
                timestamp_end=now,
                target_rpm=-100.0,
                mixing_time_s=60.0,
            )


class TestStation3TemperaturePoint:
    """Tests for Station3TemperaturePoint model."""
    
    def test_valid_point(self):
        """Test valid temperature point."""
        point = Station3TemperaturePoint(
            time_ms=1000,
            temp_c=37.0,
            heater_power_w=5.0,
        )
        assert point.time_ms == 1000
        assert point.temp_c == 37.0
    
    def test_negative_time_rejected(self):
        """Test that negative time_ms is rejected."""
        with pytest.raises(ValidationError):
            Station3TemperaturePoint(
                time_ms=-100,
                temp_c=37.0,
                heater_power_w=5.0,
            )
    
    def test_negative_heater_power_rejected(self):
        """Test that negative heater_power_w is rejected."""
        with pytest.raises(ValidationError):
            Station3TemperaturePoint(
                time_ms=1000,
                temp_c=37.0,
                heater_power_w=-1.0,
            )


class TestStation4FluorescencePoint:
    """Tests for Station4FluorescencePoint model."""
    
    def test_valid_point(self):
        """Test valid fluorescence point."""
        point = Station4FluorescencePoint(
            time_ms=1000,
            fluorescence_raw_au=12.5,
        )
        assert point.time_ms == 1000
        assert point.fluorescence_raw_au == 12.5
    
    def test_only_two_fields(self):
        """Test that only time_ms and fluorescence_raw_au fields exist."""
        fields = Station4FluorescencePoint.model_fields
        expected_fields = {"time_ms", "fluorescence_raw_au"}
        assert set(fields.keys()) == expected_fields
    
    def test_no_fluorescence_corrected_au_field(self):
        """Test that fluorescence_corrected_au field does not exist."""
        fields = Station4FluorescencePoint.model_fields
        assert "fluorescence_corrected_au" not in fields
    
    def test_no_ph_field(self):
        """Test that no pH field exists."""
        fields = Station4FluorescencePoint.model_fields
        assert "ph" not in fields
        assert "ph_calculated" not in fields
    
    def test_no_fe2_field(self):
        """Test that no Fe²⁺ field exists."""
        fields = Station4FluorescencePoint.model_fields
        assert "fe2_concentration" not in fields
        assert "fe2_concentration_um" not in fields
    
    def test_negative_fluorescence_rejected(self):
        """Test that negative fluorescence is rejected."""
        with pytest.raises(ValidationError):
            Station4FluorescencePoint(
                time_ms=1000,
                fluorescence_raw_au=-5.0,
            )


class TestStation5CleanupOutput:
    """Tests for Station5CleanupOutput model."""
    
    def test_valid_output(self):
        """Test valid station 5 cleanup output."""
        now = datetime.now(timezone.utc)
        output = Station5CleanupOutput(
            status="OK",
            timestamp_start=now,
            timestamp_end=now,
            rinse_cycles=3,
            rinse_volume_ml=50.0,
            purge_time_s=30.0,
        )
        assert output.station == 5
        assert output.name == "Cleanup"
    
    def test_station_is_five(self):
        """Test that station defaults to 5."""
        now = datetime.now(timezone.utc)
        output = Station5CleanupOutput(
            status="OK",
            timestamp_start=now,
            timestamp_end=now,
            rinse_cycles=3,
            rinse_volume_ml=50.0,
            purge_time_s=30.0,
        )
        assert output.station == 5
    
    def test_no_ph_monitor_station(self):
        """Test that this is Cleanup, not pH-Monitor."""
        now = datetime.now(timezone.utc)
        output = Station5CleanupOutput(
            status="OK",
            timestamp_start=now,
            timestamp_end=now,
            rinse_cycles=3,
            rinse_volume_ml=50.0,
            purge_time_s=30.0,
        )
        assert output.name == "Cleanup"
        assert "pH" not in output.name
        assert "Monitor" not in output.name
    
    def test_negative_rinse_cycles_rejected(self):
        """Test that negative rinse_cycles is rejected."""
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            Station5CleanupOutput(
                status="OK",
                timestamp_start=now,
                timestamp_end=now,
                rinse_cycles=-1,
                rinse_volume_ml=50.0,
                purge_time_s=30.0,
            )


class TestMeasurementPoint:
    """Tests for MeasurementPoint model."""
    
    def test_valid_point(self):
        """Test valid measurement point."""
        point = MeasurementPoint(
            time_ms=1000,
            temp_c=37.0,
            fluorescence_raw_au=12.5,
        )
        assert point.time_ms == 1000
        assert point.temp_c == 37.0
        assert point.fluorescence_raw_au == 12.5
    
    def test_exactly_three_fields(self):
        """Test that exactly three fields exist: time_ms, temp_c, fluorescence_raw_au."""
        fields = MeasurementPoint.model_fields
        expected_fields = {"time_ms", "temp_c", "fluorescence_raw_au"}
        assert set(fields.keys()) == expected_fields
    
    def test_no_ph_field(self):
        """Test that no pH field exists."""
        fields = MeasurementPoint.model_fields
        assert "ph" not in fields
        assert "ph_calculated" not in fields
        assert "ph_end" not in fields
    
    def test_no_fe2_field(self):
        """Test that no Fe²⁺ field exists."""
        fields = MeasurementPoint.model_fields
        assert "fe2_concentration" not in fields
        assert "fe2_concentration_um" not in fields
    
    def test_no_absorbance_field(self):
        """Test that no absorbance field exists."""
        fields = MeasurementPoint.model_fields
        assert "absorbance" not in fields
        assert "absorbance_ratio" not in fields
    
    def test_no_correction_fields(self):
        """Test that no correction fields exist."""
        fields = MeasurementPoint.model_fields
        assert "fluorescence_corrected_au" not in fields
        assert "bleaching_factor" not in fields
        assert "quenching_factor" not in fields
    
    def test_negative_time_rejected(self):
        """Test that negative time_ms is rejected."""
        with pytest.raises(ValidationError):
            MeasurementPoint(
                time_ms=-100,
                temp_c=37.0,
                fluorescence_raw_au=12.5,
            )
    
    def test_negative_fluorescence_rejected(self):
        """Test that negative fluorescence is rejected."""
        with pytest.raises(ValidationError):
            MeasurementPoint(
                time_ms=1000,
                temp_c=37.0,
                fluorescence_raw_au=-5.0,
            )
