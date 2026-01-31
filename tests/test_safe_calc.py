"""Tests for safe calculator service."""

import math
import pytest

from armcalc.services.safe_calc import SafeCalculator, CalcResult


@pytest.fixture
def calc():
    """Create a calculator instance."""
    return SafeCalculator()


class TestBasicMath:
    """Test basic arithmetic operations."""

    def test_addition(self, calc):
        result = calc.calculate("2 + 2")
        assert result.success
        assert result.value == 4

    def test_subtraction(self, calc):
        result = calc.calculate("10 - 3")
        assert result.success
        assert result.value == 7

    def test_multiplication(self, calc):
        result = calc.calculate("6 * 7")
        assert result.success
        assert result.value == 42

    def test_division(self, calc):
        result = calc.calculate("20 / 4")
        assert result.success
        assert result.value == 5

    def test_power_caret(self, calc):
        result = calc.calculate("2^8")
        assert result.success
        assert result.value == 256

    def test_power_double_star(self, calc):
        result = calc.calculate("2**10")
        assert result.success
        assert result.value == 1024

    def test_parentheses(self, calc):
        result = calc.calculate("(2 + 3) * 4")
        assert result.success
        assert result.value == 20

    def test_complex_expression(self, calc):
        result = calc.calculate("(10 + 5) * 2 - 8 / 4")
        assert result.success
        assert result.value == 28

    def test_negative_numbers(self, calc):
        result = calc.calculate("-5 + 10")
        assert result.success
        assert result.value == 5

    def test_decimals(self, calc):
        result = calc.calculate("3.14 * 2")
        assert result.success
        assert abs(result.value - 6.28) < 0.001


class TestPercentOperations:
    """Test percent handling."""

    def test_percent_addition(self, calc):
        # 100 + 10% should be 110 (add 10% of 100)
        result = calc.calculate("100 + 10%")
        assert result.success
        assert result.value == 110

    def test_percent_subtraction(self, calc):
        # 200 - 5% should be 190 (subtract 5% of 200)
        result = calc.calculate("200 - 5%")
        assert result.success
        assert result.value == 190

    def test_percent_multiplication(self, calc):
        # 50 * 10% should be 5 (50 * 0.1)
        result = calc.calculate("50 * 10%")
        assert result.success
        assert result.value == 5

    def test_percent_division(self, calc):
        # 100 / 10% should be 1000 (100 / 0.1)
        result = calc.calculate("100 / 10%")
        assert result.success
        assert result.value == 1000

    def test_standalone_percent(self, calc):
        # 25% alone should be 0.25
        result = calc.calculate("25%")
        assert result.success
        assert result.value == 0.25


class TestScientificFunctions:
    """Test scientific calculator functions."""

    def test_sqrt(self, calc):
        result = calc.calculate("sqrt(16)")
        assert result.success
        assert result.value == 4

    def test_sqrt_float(self, calc):
        result = calc.calculate("sqrt(2)")
        assert result.success
        assert abs(result.value - 1.41421356) < 0.0001

    def test_sin_90(self, calc):
        # sin(90 degrees) should be 1
        result = calc.calculate("sin(90)")
        assert result.success
        assert abs(result.value - 1) < 0.0001

    def test_sin_0(self, calc):
        result = calc.calculate("sin(0)")
        assert result.success
        assert abs(result.value) < 0.0001

    def test_cos_0(self, calc):
        # cos(0 degrees) should be 1
        result = calc.calculate("cos(0)")
        assert result.success
        assert abs(result.value - 1) < 0.0001

    def test_cos_90(self, calc):
        result = calc.calculate("cos(90)")
        assert result.success
        assert abs(result.value) < 0.0001

    def test_tan_45(self, calc):
        # tan(45 degrees) should be 1
        result = calc.calculate("tan(45)")
        assert result.success
        assert abs(result.value - 1) < 0.0001

    def test_log_base10(self, calc):
        result = calc.calculate("log(100)")
        assert result.success
        assert result.value == 2

    def test_ln_e(self, calc):
        result = calc.calculate("ln(e)")
        assert result.success
        assert abs(result.value - 1) < 0.0001

    def test_abs_negative(self, calc):
        result = calc.calculate("abs(-42)")
        assert result.success
        assert result.value == 42

    def test_round(self, calc):
        result = calc.calculate("round(3.7)")
        assert result.success
        assert result.value == 4

    def test_pow(self, calc):
        result = calc.calculate("pow(2, 10)")
        assert result.success
        assert result.value == 1024


class TestConstants:
    """Test mathematical constants."""

    def test_pi(self, calc):
        result = calc.calculate("pi")
        assert result.success
        assert abs(result.value - math.pi) < 0.0001

    def test_e(self, calc):
        result = calc.calculate("e")
        assert result.success
        assert abs(result.value - math.e) < 0.0001

    def test_pi_expression(self, calc):
        result = calc.calculate("2 * pi")
        assert result.success
        assert abs(result.value - 2 * math.pi) < 0.0001


class TestErrors:
    """Test error handling."""

    def test_division_by_zero(self, calc):
        result = calc.calculate("1/0")
        assert not result.success
        assert "zero" in result.error.lower()

    def test_invalid_syntax(self, calc):
        result = calc.calculate("2 + + 2")
        assert not result.success

    def test_empty_expression(self, calc):
        result = calc.calculate("")
        assert not result.success
        assert "empty" in result.error.lower()

    def test_unknown_function(self, calc):
        result = calc.calculate("unknown(5)")
        assert not result.success
        assert "unknown" in result.error.lower()

    def test_dangerous_pattern_import(self, calc):
        result = calc.calculate("__import__('os')")
        assert not result.success

    def test_dangerous_pattern_eval(self, calc):
        result = calc.calculate("eval('1+1')")
        assert not result.success


class TestFormatting:
    """Test result formatting."""

    def test_integer_result(self, calc):
        result = calc.calculate("2 + 2")
        assert result.formatted == "4"

    def test_float_result(self, calc):
        result = calc.calculate("1 / 3")
        assert "0.333" in result.formatted

    def test_large_number(self, calc):
        result = calc.calculate("2^30")
        assert result.success
        assert result.value == 1073741824
