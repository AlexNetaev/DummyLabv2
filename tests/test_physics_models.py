"""Tests for physics models in OrbusSim Dummy V2."""
import pytest
from orbus_dummy_v2.physics.noise import create_rng, add_noise
from orbus_dummy_v2.physics.temperature_model import calculate_temperature, calculate_heater_power
from orbus_dummy_v2.physics.redox_kinetics import calculate_fe2_concentration
from orbus_dummy_v2.physics.ph_model import calculate_ph
from orbus_dummy_v2.physics.fluorescence_model import calculate_ideal_fluorescence
from orbus_dummy_v2.physics.photobleaching import calculate_bleaching_factor
from orbus_dummy_v2.physics.optical_effects import calculate_raw_fluorescence
from orbus_dummy_v2.models import OpticalCalibration, ReactionCalibration


class TestTemperatureModel:
    def test_temperature_approaches_target(self):
        """Temperatur nähert sich exponentiell dem Zielwert an."""
        target = 37.0
        ambient = 22.0
        
        # Bei t=0 sollte Temperatur nahe ambient sein
        temp_0 = calculate_temperature(0.0, target, ambient)
        assert abs(temp_0 - ambient) < 0.1
        
        # Bei großem t sollte Temperatur nahe target sein
        temp_large = calculate_temperature(60.0, target, ambient)
        assert abs(temp_large - target) < 1.0
        
        # Temperatur steigt monoton
        temp_10 = calculate_temperature(10.0, target, ambient)
        temp_20 = calculate_temperature(20.0, target, ambient)
        assert temp_10 < temp_20 < target

    def test_heater_power_zero_when_at_target(self):
        """Heizleistung ist 0, wenn current_temp >= target_temp."""
        power = calculate_heater_power(40.0, 37.0)
        assert power == 0.0
        
        power_at_target = calculate_heater_power(37.0, 37.0)
        assert power_at_target == 0.0

    def test_heater_power_positive_when_below_target(self):
        """Heizleistung ist positiv, wenn current_temp < target_temp."""
        power = calculate_heater_power(22.0, 37.0)
        assert power > 0.0


class TestRedoxKinetics:
    def test_fe2_starts_at_zero(self):
        """Fe2+ Konzentration startet bei 0."""
        params = ReactionCalibration()
        fe2_0 = calculate_fe2_concentration(0.0, 1.0, 10.0, 10.0, 25.0, params)
        assert fe2_0 == 0.0

    def test_fe2_increases_monotonically(self):
        """Fe2+ Konzentration steigt monoton an."""
        params = ReactionCalibration()
        fe2_10 = calculate_fe2_concentration(10.0, 1.0, 10.0, 10.0, 25.0, params)
        fe2_20 = calculate_fe2_concentration(20.0, 1.0, 10.0, 10.0, 25.0, params)
        assert fe2_10 > 0.0
        assert fe2_20 > fe2_10

    def test_higher_temperature_increases_rate(self):
        """Höhere Temperatur führt zu schnellerem Anstieg."""
        params = ReactionCalibration()
        fe2_25c = calculate_fe2_concentration(10.0, 1.0, 10.0, 10.0, 25.0, params)
        fe2_37c = calculate_fe2_concentration(10.0, 1.0, 10.0, 10.0, 37.0, params)
        assert fe2_37c > fe2_25c


class TestPHModel:
    def test_ph_starts_at_initial(self):
        """pH startet bei initial_ph."""
        params = ReactionCalibration()
        ph_0 = calculate_ph(0.0, 7.4, 0.0, 50.0, params)
        assert abs(ph_0 - 7.4) < 0.01

    def test_ph_decreases_with_fe2(self):
        """pH sinkt, wenn fe2_concentration_um steigt."""
        params = ReactionCalibration()
        ph_low_fe2 = calculate_ph(0.0, 7.4, 100.0, 50.0, params)
        ph_high_fe2 = calculate_ph(0.0, 7.4, 500.0, 50.0, params)
        assert ph_low_fe2 < 7.4
        assert ph_high_fe2 < ph_low_fe2


class TestFluorescenceModel:
    def test_fluorescence_higher_at_high_ph(self):
        """Fluoreszenz ist höher bei pH 8.0 als bei pH 5.0 (wegen pKa 6.4)."""
        params = OpticalCalibration()
        fluo_ph5 = calculate_ideal_fluorescence(5.0, 10.0, 25.0, params)
        fluo_ph8 = calculate_ideal_fluorescence(8.0, 10.0, 25.0, params)
        assert fluo_ph8 > fluo_ph5

    def test_fluorescence_proportional_to_concentration(self):
        """Fluoreszenz ist proportional zur Konzentration."""
        params = OpticalCalibration()
        fluo_10 = calculate_ideal_fluorescence(7.4, 10.0, 25.0, params)
        fluo_20 = calculate_ideal_fluorescence(7.4, 20.0, 25.0, params)
        assert fluo_20 > fluo_10


class TestPhotobleaching:
    def test_bleaching_factor_one_at_start(self):
        """Bleaching-Faktor ist 1.0 bei t_s=0."""
        factor = calculate_bleaching_factor(0.0, 2.5, 0.0008)
        assert abs(factor - 1.0) < 0.001

    def test_bleaching_factor_decreases_with_time(self):
        """Bleaching-Faktor fällt mit der Zeit ab."""
        factor_0 = calculate_bleaching_factor(0.0, 2.5, 0.0008)
        factor_60 = calculate_bleaching_factor(60.0, 2.5, 0.0008)
        assert factor_60 < factor_0
        assert factor_60 >= 0.01  # Geclampt bei 0.01


class TestOpticalEffects:
    def test_raw_fluorescence_positive_with_zero_ideal(self):
        """Raw Fluoreszenz ist > 0 auch wenn ideal_fluorescence 0 ist (wegen Autofluoreszenz + Dark Current)."""
        params = OpticalCalibration()
        raw = calculate_raw_fluorescence(0.0, 1.0, 0.0, 0.0, params)
        assert raw > 0.0  # Sollte autofluorescence_blank_au + detector_dark_au sein

    def test_quencher_reduces_signal(self):
        """Höhere Quencher-Konzentration reduziert das Signal."""
        params = OpticalCalibration()
        raw_no_quencher = calculate_raw_fluorescence(100.0, 1.0, 10.0, 0.0, params)
        raw_with_quencher = calculate_raw_fluorescence(100.0, 1.0, 10.0, 0.5, params)
        assert raw_with_quencher < raw_no_quencher


class TestNoise:
    def test_create_rng_with_seed(self):
        """Seeded RNG erzeugt reproduzierbare Werte."""
        rng1 = create_rng(42)
        rng2 = create_rng(42)
        assert rng1.random() == rng2.random()

    def test_create_rng_without_seed(self):
        """RNG ohne Seed nutzt System-Zufall."""
        rng = create_rng(None)
        assert rng is not None

    def test_add_noise_with_zero_std(self):
        """Noise mit std=0 ändert den Wert nicht."""
        rng = create_rng(42)
        result = add_noise(10.0, 0.0, rng)
        assert result == 10.0

    def test_add_noise_changes_value(self):
        """Noise mit std>0 ändert den Wert."""
        rng = create_rng(42)
        result = add_noise(10.0, 1.0, rng)
        assert result != 10.0  # Mit hoher Wahrscheinlichkeit
