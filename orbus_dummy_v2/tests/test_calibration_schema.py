"""Tests for calibration_schema models."""

import pytest
from pydantic import ValidationError

from models.calibration_schema import (
    SpectralOverlapCalibration,
    OpticalCalibration,
    ReactionCalibration,
    CalibrationData,
)


class TestSpectralOverlapCalibration:
    """Tests for SpectralOverlapCalibration model."""
    
    def test_valid_with_defaults(self):
        """Test valid spectral overlap calibration with defaults."""
        cal = SpectralOverlapCalibration()
        assert cal.scatter_490nm_fraction == 0.02
        assert cal.raman_water_fraction == 0.005
    
    def test_negative_scatter_rejected(self):
        """Test that negative scatter fraction is rejected."""
        with pytest.raises(ValidationError):
            SpectralOverlapCalibration(scatter_490nm_fraction=-0.01)
    
    def test_negative_raman_rejected(self):
        """Test that negative raman fraction is rejected."""
        with pytest.raises(ValidationError):
            SpectralOverlapCalibration(raman_water_fraction=-0.001)


class TestOpticalCalibration:
    """Tests for OpticalCalibration model."""
    
    def test_valid_with_defaults(self):
        """Test valid optical calibration with defaults."""
        cal = OpticalCalibration()
        assert cal.fluorophore == "Fluorescein"
        assert cal.pka == 6.4
        assert cal.epsilon_490nm == 76900
        assert cal.quantum_yield_ref == 0.93
        assert cal.pathlength_cm == 1.0
        assert cal.detector_gain == 1.0
    
    def test_negative_k_bleach_rejected(self):
        """Test that negative k_bleach_per_s is rejected."""
        with pytest.raises(ValidationError):
            OpticalCalibration(k_bleach_per_s=-0.0001)
    
    def test_negative_quantum_yield_rejected(self):
        """Test that negative quantum_yield_ref is rejected."""
        with pytest.raises(ValidationError):
            OpticalCalibration(quantum_yield_ref=-0.1)
    
    def test_quantum_yield_over_1_rejected(self):
        """Test that quantum_yield_ref > 1 is rejected."""
        with pytest.raises(ValidationError):
            OpticalCalibration(quantum_yield_ref=1.5)
    
    def test_zero_pathlength_rejected(self):
        """Test that pathlength_cm <= 0 is rejected."""
        with pytest.raises(ValidationError):
            OpticalCalibration(pathlength_cm=0.0)
    
    def test_zero_detector_gain_rejected(self):
        """Test that detector_gain <= 0 is rejected."""
        with pytest.raises(ValidationError):
            OpticalCalibration(detector_gain=0.0)
    
    def test_negative_epsilon_rejected(self):
        """Test that negative epsilon is rejected."""
        with pytest.raises(ValidationError):
            OpticalCalibration(epsilon_490nm=-100)
    
    def test_unknown_field_rejected(self):
        """Test that unknown fields are rejected."""
        with pytest.raises(ValidationError):
            OpticalCalibration(unknown_field="should_fail")


class TestReactionCalibration:
    """Tests for ReactionCalibration model."""
    
    def test_valid_with_defaults(self):
        """Test valid reaction calibration with defaults."""
        cal = ReactionCalibration()
        assert cal.ph_start == 7.4
        assert cal.delta_ph_max == 2.0
        assert cal.k_redox_per_s == 0.08
        assert cal.fe2_max_um_per_mm_fecl3 == 500.0
    
    def test_negative_delta_ph_max_rejected(self):
        """Test that negative delta_ph_max is rejected."""
        with pytest.raises(ValidationError):
            ReactionCalibration(delta_ph_max=-0.5)
    
    def test_negative_k_redox_rejected(self):
        """Test that negative k_redox_per_s is rejected."""
        with pytest.raises(ValidationError):
            ReactionCalibration(k_redox_per_s=-0.01)
    
    def test_negative_fe2_max_rejected(self):
        """Test that negative fe2_max_um_per_mm_fecl3 is rejected."""
        with pytest.raises(ValidationError):
            ReactionCalibration(fe2_max_um_per_mm_fecl3=-100.0)
    
    def test_unknown_field_rejected(self):
        """Test that unknown fields are rejected."""
        with pytest.raises(ValidationError):
            ReactionCalibration(unknown_field="should_fail")


class TestCalibrationData:
    """Tests for CalibrationData model."""
    
    def test_valid_complete_calibration(self):
        """Test valid complete calibration data."""
        cal = CalibrationData(
            optical=OpticalCalibration(),
            reaction=ReactionCalibration(),
        )
        assert cal.version == "orbus_dummy_v2"
        assert isinstance(cal.optical, OpticalCalibration)
        assert isinstance(cal.reaction, ReactionCalibration)
    
    def test_defaults_created_correctly(self):
        """Test that defaults are created correctly."""
        cal = CalibrationData(
            optical=OpticalCalibration(),
            reaction=ReactionCalibration(),
        )
        assert cal.optical.spectral_overlap.scatter_490nm_fraction == 0.02
        assert cal.optical.spectral_overlap.raman_water_fraction == 0.005
    
    def test_missing_optical_rejected(self):
        """Test that missing optical calibration is rejected."""
        with pytest.raises(ValidationError):
            CalibrationData(reaction=ReactionCalibration())
    
    def test_missing_reaction_rejected(self):
        """Test that missing reaction calibration is rejected."""
        with pytest.raises(ValidationError):
            CalibrationData(optical=OpticalCalibration())
    
    def test_unknown_field_rejected(self):
        """Test that unknown fields are rejected."""
        with pytest.raises(ValidationError):
            CalibrationData(
                optical=OpticalCalibration(),
                reaction=ReactionCalibration(),
                unknown_field="should_fail",
            )
