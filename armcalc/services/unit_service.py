"""Unit conversion service."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from armcalc.utils.logging import get_logger

logger = get_logger("unit_service")


@dataclass
class UnitConversionResult:
    """Unit conversion result."""

    amount: float
    from_unit: str
    to_unit: str
    result: float
    category: str

    @property
    def formatted(self) -> str:
        """Format the conversion result."""
        # Determine decimal places based on result magnitude
        if abs(self.result) >= 100:
            result_str = f"{self.result:,.2f}"
        elif abs(self.result) >= 1:
            result_str = f"{self.result:.4f}".rstrip("0").rstrip(".")
        else:
            result_str = f"{self.result:.6f}".rstrip("0").rstrip(".")

        if abs(self.amount) >= 100:
            amount_str = f"{self.amount:,.2f}"
        elif abs(self.amount) >= 1:
            amount_str = f"{self.amount:.4f}".rstrip("0").rstrip(".")
        else:
            amount_str = f"{self.amount:.6f}".rstrip("0").rstrip(".")

        return f"{amount_str} {self.from_unit} = {result_str} {self.to_unit}"


class UnitService:
    """
    Unit conversion service.

    Supports:
    - Distance: km, m, cm, mm, miles, ft, in, yd
    - Weight: kg, g, mg, lbs, oz
    - Temperature: c, f, k
    - Volume: l, ml, gal, qt, pt, cup, fl_oz
    - Area: sqm, sqkm, sqft, sqmi, acre, hectare
    - Speed: kmh, mph, ms, knot
    - Data: b, kb, mb, gb, tb, pb
    """

    # Conversion factors to base unit within each category
    # Distance -> meters
    DISTANCE = {
        "km": 1000.0,
        "m": 1.0,
        "cm": 0.01,
        "mm": 0.001,
        "mi": 1609.344,
        "mile": 1609.344,
        "miles": 1609.344,
        "ft": 0.3048,
        "feet": 0.3048,
        "foot": 0.3048,
        "in": 0.0254,
        "inch": 0.0254,
        "inches": 0.0254,
        "yd": 0.9144,
        "yard": 0.9144,
        "yards": 0.9144,
        "nm": 1852.0,  # nautical mile
    }

    # Weight -> grams
    WEIGHT = {
        "kg": 1000.0,
        "g": 1.0,
        "mg": 0.001,
        "lb": 453.592,
        "lbs": 453.592,
        "pound": 453.592,
        "pounds": 453.592,
        "oz": 28.3495,
        "ounce": 28.3495,
        "ounces": 28.3495,
        "ton": 1000000.0,
        "tonne": 1000000.0,
        "st": 6350.29,  # stone
        "stone": 6350.29,
    }

    # Volume -> liters
    VOLUME = {
        "l": 1.0,
        "liter": 1.0,
        "litre": 1.0,
        "ml": 0.001,
        "gal": 3.78541,
        "gallon": 3.78541,
        "qt": 0.946353,
        "quart": 0.946353,
        "pt": 0.473176,
        "pint": 0.473176,
        "cup": 0.236588,
        "fl_oz": 0.0295735,
        "floz": 0.0295735,
    }

    # Area -> square meters
    AREA = {
        "sqm": 1.0,
        "m2": 1.0,
        "sqkm": 1000000.0,
        "km2": 1000000.0,
        "sqft": 0.092903,
        "ft2": 0.092903,
        "sqmi": 2589988.0,
        "mi2": 2589988.0,
        "acre": 4046.86,
        "hectare": 10000.0,
        "ha": 10000.0,
    }

    # Speed -> meters per second
    SPEED = {
        "ms": 1.0,
        "m/s": 1.0,
        "kmh": 0.277778,
        "km/h": 0.277778,
        "kph": 0.277778,
        "mph": 0.44704,
        "mi/h": 0.44704,
        "knot": 0.514444,
        "knots": 0.514444,
        "kt": 0.514444,
    }

    # Data -> bytes
    DATA = {
        "b": 1.0,
        "byte": 1.0,
        "bytes": 1.0,
        "kb": 1024.0,
        "kilobyte": 1024.0,
        "mb": 1048576.0,
        "megabyte": 1048576.0,
        "gb": 1073741824.0,
        "gigabyte": 1073741824.0,
        "tb": 1099511627776.0,
        "terabyte": 1099511627776.0,
        "pb": 1125899906842624.0,
        "petabyte": 1125899906842624.0,
    }

    # All categories
    CATEGORIES = {
        "distance": DISTANCE,
        "weight": WEIGHT,
        "volume": VOLUME,
        "area": AREA,
        "speed": SPEED,
        "data": DATA,
    }

    def __init__(self):
        """Initialize the unit service."""
        # Build reverse lookup
        self._unit_to_category: Dict[str, str] = {}
        for category, units in self.CATEGORIES.items():
            for unit in units:
                self._unit_to_category[unit.lower()] = category

    def _normalize_unit(self, unit: str) -> str:
        """Normalize unit name."""
        return unit.lower().strip().replace(" ", "_")

    def _find_category(self, unit: str) -> Optional[str]:
        """Find the category for a unit."""
        normalized = self._normalize_unit(unit)
        return self._unit_to_category.get(normalized)

    def _get_factor(self, unit: str, category: str) -> Optional[float]:
        """Get conversion factor for a unit."""
        normalized = self._normalize_unit(unit)
        category_units = self.CATEGORIES.get(category)
        if category_units:
            return category_units.get(normalized)
        return None

    def convert_temperature(
        self, amount: float, from_unit: str, to_unit: str
    ) -> Optional[UnitConversionResult]:
        """
        Convert temperature between Celsius, Fahrenheit, and Kelvin.

        Special handling because temperature conversions are not simple ratios.
        """
        from_u = self._normalize_unit(from_unit)
        to_u = self._normalize_unit(to_unit)

        # Normalize aliases
        temp_aliases = {
            "c": "c", "celsius": "c",
            "f": "f", "fahrenheit": "f",
            "k": "k", "kelvin": "k",
        }

        from_u = temp_aliases.get(from_u)
        to_u = temp_aliases.get(to_u)

        if not from_u or not to_u:
            return None

        # Convert to Celsius first
        if from_u == "c":
            celsius = amount
        elif from_u == "f":
            celsius = (amount - 32) * 5 / 9
        elif from_u == "k":
            celsius = amount - 273.15
        else:
            return None

        # Convert from Celsius to target
        if to_u == "c":
            result = celsius
        elif to_u == "f":
            result = celsius * 9 / 5 + 32
        elif to_u == "k":
            result = celsius + 273.15
        else:
            return None

        return UnitConversionResult(
            amount=amount,
            from_unit=from_unit.upper() if len(from_unit) == 1 else from_unit.title(),
            to_unit=to_unit.upper() if len(to_unit) == 1 else to_unit.title(),
            result=result,
            category="temperature",
        )

    def convert(
        self, amount: float, from_unit: str, to_unit: str
    ) -> Optional[UnitConversionResult]:
        """
        Convert amount between units.

        Args:
            amount: Amount to convert
            from_unit: Source unit
            to_unit: Target unit

        Returns:
            UnitConversionResult or None if conversion not possible
        """
        # Check for temperature first (special case)
        temp_units = {"c", "f", "k", "celsius", "fahrenheit", "kelvin"}
        from_norm = self._normalize_unit(from_unit)
        to_norm = self._normalize_unit(to_unit)

        if from_norm in temp_units or to_norm in temp_units:
            return self.convert_temperature(amount, from_unit, to_unit)

        # Find categories
        from_category = self._find_category(from_unit)
        to_category = self._find_category(to_unit)

        if not from_category or not to_category:
            logger.debug(f"Unknown unit: {from_unit} or {to_unit}")
            return None

        if from_category != to_category:
            logger.debug(f"Category mismatch: {from_category} vs {to_category}")
            return None

        # Get conversion factors
        from_factor = self._get_factor(from_unit, from_category)
        to_factor = self._get_factor(to_unit, to_category)

        if from_factor is None or to_factor is None:
            return None

        # Convert: amount * from_factor / to_factor
        result = amount * from_factor / to_factor

        return UnitConversionResult(
            amount=amount,
            from_unit=from_unit,
            to_unit=to_unit,
            result=result,
            category=from_category,
        )

    def get_supported_units(self) -> Dict[str, List[str]]:
        """Get dictionary of supported units by category."""
        result = {}
        for category, units in self.CATEGORIES.items():
            # Get unique base forms
            result[category] = sorted(set(units.keys()))
        result["temperature"] = ["c", "f", "k"]
        return result

    def get_unit_info(self, unit: str) -> Optional[Tuple[str, float]]:
        """Get category and factor for a unit."""
        category = self._find_category(unit)
        if category:
            factor = self._get_factor(unit, category)
            return (category, factor) if factor else None
        return None


# Global service instance
_unit_service: Optional[UnitService] = None


def get_unit_service() -> UnitService:
    """Get or create unit service instance."""
    global _unit_service
    if _unit_service is None:
        _unit_service = UnitService()
    return _unit_service
