"""Tests for unit conversion service."""

import pytest

from armcalc.services.unit_service import UnitService


@pytest.fixture
def unit_service():
    """Create a unit service instance."""
    return UnitService()


class TestDistanceConversions:
    """Test distance unit conversions."""

    def test_km_to_miles(self, unit_service):
        result = unit_service.convert(10, "km", "miles")
        assert result is not None
        assert abs(result.result - 6.21371) < 0.001

    def test_miles_to_km(self, unit_service):
        result = unit_service.convert(5, "miles", "km")
        assert result is not None
        assert abs(result.result - 8.04672) < 0.001

    def test_meters_to_feet(self, unit_service):
        result = unit_service.convert(100, "m", "ft")
        assert result is not None
        assert abs(result.result - 328.084) < 0.1

    def test_inches_to_cm(self, unit_service):
        result = unit_service.convert(1, "inch", "cm")
        assert result is not None
        assert abs(result.result - 2.54) < 0.01


class TestWeightConversions:
    """Test weight unit conversions."""

    def test_kg_to_lbs(self, unit_service):
        result = unit_service.convert(100, "kg", "lbs")
        assert result is not None
        assert abs(result.result - 220.462) < 0.1

    def test_lbs_to_kg(self, unit_service):
        result = unit_service.convert(150, "lbs", "kg")
        assert result is not None
        assert abs(result.result - 68.0389) < 0.1

    def test_grams_to_oz(self, unit_service):
        result = unit_service.convert(100, "g", "oz")
        assert result is not None
        assert abs(result.result - 3.5274) < 0.01


class TestTemperatureConversions:
    """Test temperature conversions."""

    def test_celsius_to_fahrenheit(self, unit_service):
        result = unit_service.convert(0, "c", "f")
        assert result is not None
        assert result.result == 32

    def test_fahrenheit_to_celsius(self, unit_service):
        result = unit_service.convert(212, "f", "c")
        assert result is not None
        assert result.result == 100

    def test_celsius_to_kelvin(self, unit_service):
        result = unit_service.convert(0, "c", "k")
        assert result is not None
        assert abs(result.result - 273.15) < 0.01

    def test_kelvin_to_celsius(self, unit_service):
        result = unit_service.convert(300, "k", "c")
        assert result is not None
        assert abs(result.result - 26.85) < 0.01

    def test_room_temperature(self, unit_service):
        # 20°C should be about 68°F
        result = unit_service.convert(20, "c", "f")
        assert result is not None
        assert result.result == 68


class TestInvalidConversions:
    """Test invalid conversion handling."""

    def test_unknown_unit(self, unit_service):
        result = unit_service.convert(10, "unknown", "km")
        assert result is None

    def test_category_mismatch(self, unit_service):
        # Cannot convert km to kg
        result = unit_service.convert(10, "km", "kg")
        assert result is None


class TestVolumeConversions:
    """Test volume conversions."""

    def test_liters_to_gallons(self, unit_service):
        result = unit_service.convert(3.78541, "l", "gal")
        assert result is not None
        assert abs(result.result - 1) < 0.01

    def test_ml_to_liters(self, unit_service):
        result = unit_service.convert(1000, "ml", "l")
        assert result is not None
        assert result.result == 1


class TestSpeedConversions:
    """Test speed conversions."""

    def test_kmh_to_mph(self, unit_service):
        result = unit_service.convert(100, "kmh", "mph")
        assert result is not None
        assert abs(result.result - 62.137) < 0.1

    def test_mph_to_kmh(self, unit_service):
        result = unit_service.convert(60, "mph", "kmh")
        assert result is not None
        assert abs(result.result - 96.56) < 0.1
