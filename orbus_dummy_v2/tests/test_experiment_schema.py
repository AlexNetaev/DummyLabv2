"""Tests for experiment_schema models."""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from models.experiment_schema import (
    ReagentDose,
    ExperimentParameters,
    ExperimentJob,
)


def create_valid_reagents():
    """Create a list of 5 valid reagents."""
    return [
        ReagentDose(reagent_name="ascorbic_acid", volume_ul=100.0, concentration_mm=10.0),
        ReagentDose(reagent_name="fecl3", volume_ul=50.0, concentration_mm=5.0),
        ReagentDose(reagent_name="h2o2", volume_ul=75.0, concentration_mm=2.0),
        ReagentDose(reagent_name="fluorescein", volume_ul=25.0, concentration_mm=0.1),
        ReagentDose(reagent_name="phosphate_buffer", volume_ul=200.0, concentration_mm=50.0),
    ]


class TestReagentDose:
    """Tests for ReagentDose model."""
    
    def test_valid_reagent(self):
        """Test valid reagent dose."""
        reagent = ReagentDose(
            reagent_name="ascorbic_acid",
            volume_ul=100.0,
            concentration_mm=10.0
        )
        assert reagent.reagent_name == "ascorbic_acid"
        assert reagent.volume_ul == 100.0
        assert reagent.concentration_mm == 10.0
    
    def test_negative_volume_rejected(self):
        """Test that negative volume is rejected."""
        with pytest.raises(ValidationError):
            ReagentDose(
                reagent_name="ascorbic_acid",
                volume_ul=-10.0,
                concentration_mm=10.0
            )
    
    def test_negative_concentration_rejected(self):
        """Test that negative concentration is rejected."""
        with pytest.raises(ValidationError):
            ReagentDose(
                reagent_name="ascorbic_acid",
                volume_ul=100.0,
                concentration_mm=-5.0
            )
    
    def test_empty_name_rejected(self):
        """Test that empty name is rejected."""
        with pytest.raises(ValidationError):
            ReagentDose(
                reagent_name="",
                volume_ul=100.0,
                concentration_mm=10.0
            )


class TestExperimentParameters:
    """Tests for ExperimentParameters model."""
    
    def test_valid_experiment(self):
        """Test valid experiment with all 5 reagents."""
        params = ExperimentParameters(
            reagents=create_valid_reagents(),
            mixing_speed_rpm=300.0,
            mixing_time_s=60.0,
            target_temperature_c=37.0,
            heating_time_s=300.0,
            measurement_interval_ms=1000,
            fluorescence_duration_s=120.0,
        )
        assert len(params.reagents) == 5
    
    def test_missing_reagent_rejected(self):
        """Test that missing reagent is rejected."""
        # Create only 4 reagents - this will fail at the list length validation
        reagents = [
            ReagentDose(reagent_name="ascorbic_acid", volume_ul=100.0, concentration_mm=10.0),
            ReagentDose(reagent_name="fecl3", volume_ul=50.0, concentration_mm=5.0),
            ReagentDose(reagent_name="h2o2", volume_ul=75.0, concentration_mm=2.0),
            ReagentDose(reagent_name="fluorescein", volume_ul=25.0, concentration_mm=0.1),
        ]
        with pytest.raises(ValidationError) as exc_info:
            ExperimentParameters(
                reagents=reagents,
                mixing_speed_rpm=300.0,
                mixing_time_s=60.0,
                target_temperature_c=37.0,
                heating_time_s=300.0,
                measurement_interval_ms=1000,
                fluorescence_duration_s=120.0,
            )
        # The error message may be about list length or missing reagents
        assert "too_short" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()
    
    def test_duplicate_reagent_rejected(self):
        """Test that duplicate reagent is rejected."""
        reagents = [
            ReagentDose(reagent_name="ascorbic_acid", volume_ul=100.0, concentration_mm=10.0),
            ReagentDose(reagent_name="ascorbic_acid", volume_ul=50.0, concentration_mm=5.0),
            ReagentDose(reagent_name="h2o2", volume_ul=75.0, concentration_mm=2.0),
            ReagentDose(reagent_name="fluorescein", volume_ul=25.0, concentration_mm=0.1),
            ReagentDose(reagent_name="phosphate_buffer", volume_ul=200.0, concentration_mm=50.0),
        ]
        with pytest.raises(ValidationError) as exc_info:
            ExperimentParameters(
                reagents=reagents,
                mixing_speed_rpm=300.0,
                mixing_time_s=60.0,
                target_temperature_c=37.0,
                heating_time_s=300.0,
                measurement_interval_ms=1000,
                fluorescence_duration_s=120.0,
            )
        assert "Duplicate" in str(exc_info.value) or "Missing" in str(exc_info.value)
    
    def test_sixth_reagent_rejected(self):
        """Test that 6 reagents are rejected."""
        reagents = [
            ReagentDose(reagent_name="ascorbic_acid", volume_ul=100.0, concentration_mm=10.0),
            ReagentDose(reagent_name="fecl3", volume_ul=50.0, concentration_mm=5.0),
            ReagentDose(reagent_name="h2o2", volume_ul=75.0, concentration_mm=2.0),
            ReagentDose(reagent_name="fluorescein", volume_ul=25.0, concentration_mm=0.1),
            ReagentDose(reagent_name="phosphate_buffer", volume_ul=200.0, concentration_mm=50.0),
            ReagentDose(reagent_name="extra_reagent", volume_ul=10.0, concentration_mm=1.0),
        ]
        with pytest.raises(ValidationError):
            ExperimentParameters(
                reagents=reagents,
                mixing_speed_rpm=300.0,
                mixing_time_s=60.0,
                target_temperature_c=37.0,
                heating_time_s=300.0,
                measurement_interval_ms=1000,
                fluorescence_duration_s=120.0,
            )
    
    def test_negative_volume_in_reagent_rejected(self):
        """Test that negative volume in a reagent is rejected at ReagentDose level."""
        # This should fail when creating the ReagentDose, not at ExperimentParameters level
        with pytest.raises(ValidationError) as exc_info:
            ReagentDose(
                reagent_name="ascorbic_acid",
                volume_ul=-10.0,
                concentration_mm=10.0
            )
        assert "volume_ul" in str(exc_info.value).lower()
    
    def test_negative_concentration_in_reagent_rejected(self):
        """Test that negative concentration in a reagent is rejected at ReagentDose level."""
        # This should fail when creating the ReagentDose, not at ExperimentParameters level
        with pytest.raises(ValidationError) as exc_info:
            ReagentDose(
                reagent_name="ascorbic_acid",
                volume_ul=100.0,
                concentration_mm=-5.0
            )
        assert "concentration_mm" in str(exc_info.value).lower()
    
    def test_temperature_over_99_rejected(self):
        """Test that target_temperature_c > 99 is rejected."""
        with pytest.raises(ValidationError):
            ExperimentParameters(
                reagents=create_valid_reagents(),
                mixing_speed_rpm=300.0,
                mixing_time_s=60.0,
                target_temperature_c=100.0,
                heating_time_s=300.0,
                measurement_interval_ms=1000,
                fluorescence_duration_s=120.0,
            )
    
    def test_measurement_interval_under_50_rejected(self):
        """Test that measurement_interval_ms < 50 is rejected."""
        with pytest.raises(ValidationError):
            ExperimentParameters(
                reagents=create_valid_reagents(),
                mixing_speed_rpm=300.0,
                mixing_time_s=60.0,
                target_temperature_c=37.0,
                heating_time_s=300.0,
                measurement_interval_ms=49,
                fluorescence_duration_s=120.0,
            )
    
    def test_measurement_interval_over_5000_rejected(self):
        """Test that measurement_interval_ms > 5000 is rejected."""
        with pytest.raises(ValidationError):
            ExperimentParameters(
                reagents=create_valid_reagents(),
                mixing_speed_rpm=300.0,
                mixing_time_s=60.0,
                target_temperature_c=37.0,
                heating_time_s=300.0,
                measurement_interval_ms=5001,
                fluorescence_duration_s=120.0,
            )
    
    def test_emission_le_excitation_rejected(self):
        """Test that emission_wavelength_nm <= excitation_wavelength_nm is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ExperimentParameters(
                reagents=create_valid_reagents(),
                mixing_speed_rpm=300.0,
                mixing_time_s=60.0,
                target_temperature_c=37.0,
                heating_time_s=300.0,
                measurement_interval_ms=1000,
                fluorescence_duration_s=120.0,
                excitation_wavelength_nm=520.0,
                emission_wavelength_nm=520.0,
            )
        assert "emission_wavelength_nm" in str(exc_info.value)
    
    def test_unknown_fields_in_parameters_rejected(self):
        """Test that unknown fields in parameters are rejected."""
        with pytest.raises(ValidationError):
            ExperimentParameters(
                reagents=create_valid_reagents(),
                mixing_speed_rpm=300.0,
                mixing_time_s=60.0,
                target_temperature_c=37.0,
                heating_time_s=300.0,
                measurement_interval_ms=1000,
                fluorescence_duration_s=120.0,
                unknown_field="should_fail",
            )
    
    def test_case_insensitive_reagent_names(self):
        """Test that reagent names are case-insensitive."""
        reagents = [
            ReagentDose(reagent_name="ASCORBIC_ACID", volume_ul=100.0, concentration_mm=10.0),
            ReagentDose(reagent_name="FeCl3", volume_ul=50.0, concentration_mm=5.0),
            ReagentDose(reagent_name="H2O2", volume_ul=75.0, concentration_mm=2.0),
            ReagentDose(reagent_name="FLUORESCEIN", volume_ul=25.0, concentration_mm=0.1),
            ReagentDose(reagent_name="Phosphate_Buffer", volume_ul=200.0, concentration_mm=50.0),
        ]
        params = ExperimentParameters(
            reagents=reagents,
            mixing_speed_rpm=300.0,
            mixing_time_s=60.0,
            target_temperature_c=37.0,
            heating_time_s=300.0,
            measurement_interval_ms=1000,
            fluorescence_duration_s=120.0,
        )
        assert len(params.reagents) == 5
    
    def test_whitespace_stripped_from_reagent_names(self):
        """Test that whitespace is stripped from reagent names."""
        reagents = [
            ReagentDose(reagent_name="  ascorbic_acid  ", volume_ul=100.0, concentration_mm=10.0),
            ReagentDose(reagent_name=" fecl3", volume_ul=50.0, concentration_mm=5.0),
            ReagentDose(reagent_name="h2o2 ", volume_ul=75.0, concentration_mm=2.0),
            ReagentDose(reagent_name="  fluorescein  ", volume_ul=25.0, concentration_mm=0.1),
            ReagentDose(reagent_name="phosphate_buffer", volume_ul=200.0, concentration_mm=50.0),
        ]
        params = ExperimentParameters(
            reagents=reagents,
            mixing_speed_rpm=300.0,
            mixing_time_s=60.0,
            target_temperature_c=37.0,
            heating_time_s=300.0,
            measurement_interval_ms=1000,
            fluorescence_duration_s=120.0,
        )
        assert len(params.reagents) == 5


class TestExperimentJob:
    """Tests for ExperimentJob model."""
    
    def test_valid_job(self):
        """Test valid experiment job."""
        job = ExperimentJob(
            job_id="job_001",
            cycle_id="cycle_001",
            parameters=ExperimentParameters(
                reagents=create_valid_reagents(),
                mixing_speed_rpm=300.0,
                mixing_time_s=60.0,
                target_temperature_c=37.0,
                heating_time_s=300.0,
                measurement_interval_ms=1000,
                fluorescence_duration_s=120.0,
            ),
        )
        assert job.job_id == "job_001"
        assert job.cycle_id == "cycle_001"
        assert job.station_4_action == "FLUORESCENCE"
    
    def test_unknown_fields_on_job_level_ignored(self):
        """Test that unknown fields on job level are ignored."""
        job = ExperimentJob(
            job_id="job_001",
            cycle_id="cycle_001",
            parameters=ExperimentParameters(
                reagents=create_valid_reagents(),
                mixing_speed_rpm=300.0,
                mixing_time_s=60.0,
                target_temperature_c=37.0,
                heating_time_s=300.0,
                measurement_interval_ms=1000,
                fluorescence_duration_s=120.0,
            ),
            unknown_metadata="should_be_ignored",
            another_field=123,
        )
        assert job.job_id == "job_001"
        # The unknown fields should be silently ignored
    
    def test_empty_job_id_rejected(self):
        """Test that empty job_id is rejected."""
        with pytest.raises(ValidationError):
            ExperimentJob(
                job_id="",
                cycle_id="cycle_001",
                parameters=ExperimentParameters(
                    reagents=create_valid_reagents(),
                    mixing_speed_rpm=300.0,
                    mixing_time_s=60.0,
                    target_temperature_c=37.0,
                    heating_time_s=300.0,
                    measurement_interval_ms=1000,
                    fluorescence_duration_s=120.0,
                ),
            )
    
    def test_negative_seed_rejected(self):
        """Test that negative simulation_seed is rejected."""
        with pytest.raises(ValidationError):
            ExperimentJob(
                job_id="job_001",
                cycle_id="cycle_001",
                parameters=ExperimentParameters(
                    reagents=create_valid_reagents(),
                    mixing_speed_rpm=300.0,
                    mixing_time_s=60.0,
                    target_temperature_c=37.0,
                    heating_time_s=300.0,
                    measurement_interval_ms=1000,
                    fluorescence_duration_s=120.0,
                ),
                simulation_seed=-1,
            )
