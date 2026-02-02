"""Tests for /convert command argument parser."""

from decimal import Decimal
import pytest

from armcalc.routers.tools_convert import parse_convert_args, detect_rub_method


class TestParseConvertArgs:
    """Test parse_convert_args function."""

    def test_basic_conversion(self):
        """Test basic /convert 100 usdt amd pattern."""
        parts = ["/convert", "100", "usdt", "amd"]
        amount, from_curr, to_curr, method = parse_convert_args(parts)

        assert amount == Decimal("100")
        assert from_curr == "USDT"
        assert to_curr == "AMD"
        assert method is None

    def test_reverse_conversion(self):
        """Test /convert 50000 amd usdt pattern."""
        parts = ["/convert", "50000", "amd", "usdt"]
        amount, from_curr, to_curr, method = parse_convert_args(parts)

        assert amount == Decimal("50000")
        assert from_curr == "AMD"
        assert to_curr == "USDT"
        assert method is None

    def test_with_rub_method_after(self):
        """Test /convert 100 usdt sberbank rub pattern."""
        parts = ["/convert", "100", "usdt", "sberbank", "rub"]
        amount, from_curr, to_curr, method = parse_convert_args(parts)

        assert amount == Decimal("100")
        assert from_curr == "USDT"
        assert to_curr == "RUB"
        assert method == "sberbank"

    def test_with_rub_method_before(self):
        """Test /convert 100 usdt rub sberbank pattern."""
        parts = ["/convert", "100", "usdt", "rub", "sberbank"]
        amount, from_curr, to_curr, method = parse_convert_args(parts)

        assert amount == Decimal("100")
        assert from_curr == "USDT"
        assert to_curr == "RUB"
        assert method == "sberbank"

    def test_tinkoff_method(self):
        """Test tinkoff RUB method."""
        parts = ["/convert", "100", "usdt", "tinkoff", "rub"]
        amount, from_curr, to_curr, method = parse_convert_args(parts)

        assert method == "tinkoff"

    def test_alfa_method_alias(self):
        """Test alfa alias for alfabank."""
        parts = ["/convert", "100", "usdt", "alfa", "rub"]
        amount, from_curr, to_curr, method = parse_convert_args(parts)

        assert method == "alfabank"

    def test_natural_input_with_to(self):
        """Test /convert 100 usdt to amd pattern."""
        parts = ["/convert", "100", "usdt", "to", "amd"]
        amount, from_curr, to_curr, method = parse_convert_args(parts)

        assert amount == Decimal("100")
        assert from_curr == "USDT"
        assert to_curr == "AMD"

    def test_natural_input_with_arrow(self):
        """Test /convert 100 usdt -> amd pattern."""
        parts = ["/convert", "100", "usdt", "->", "amd"]
        amount, from_curr, to_curr, method = parse_convert_args(parts)

        assert amount == Decimal("100")
        assert from_curr == "USDT"
        assert to_curr == "AMD"

    def test_amount_with_comma(self):
        """Test amount with comma separator."""
        parts = ["/convert", "1,000", "usdt", "amd"]
        amount, from_curr, to_curr, method = parse_convert_args(parts)

        assert amount == Decimal("1000")

    def test_decimal_amount(self):
        """Test decimal amount."""
        parts = ["/convert", "100.50", "usdt", "amd"]
        amount, from_curr, to_curr, method = parse_convert_args(parts)

        assert amount == Decimal("100.50")

    def test_insufficient_args(self):
        """Test with insufficient arguments."""
        parts = ["/convert", "100", "usdt"]
        amount, from_curr, to_curr, method = parse_convert_args(parts)

        assert amount is None

    def test_invalid_amount(self):
        """Test with invalid amount."""
        parts = ["/convert", "abc", "usdt", "amd"]
        amount, from_curr, to_curr, method = parse_convert_args(parts)

        assert amount is None

    def test_case_insensitive(self):
        """Test case insensitivity."""
        parts = ["/convert", "100", "USDT", "AMD"]
        amount, from_curr, to_curr, method = parse_convert_args(parts)

        assert from_curr == "USDT"
        assert to_curr == "AMD"


class TestDetectRubMethod:
    """Test detect_rub_method function."""

    def test_sberbank_rub(self):
        """Test sberbank rub detection."""
        to_curr, method = detect_rub_method(["sberbank", "rub"])
        assert to_curr == "RUB"
        assert method == "sberbank"

    def test_rub_sberbank(self):
        """Test rub sberbank detection (reversed order)."""
        to_curr, method = detect_rub_method(["rub", "sberbank"])
        assert to_curr == "RUB"
        assert method == "sberbank"

    def test_tinkoff(self):
        """Test tinkoff detection."""
        to_curr, method = detect_rub_method(["tinkoff", "rub"])
        assert method == "tinkoff"

    def test_tink_alias(self):
        """Test tink alias for tinkoff."""
        to_curr, method = detect_rub_method(["tink", "rub"])
        assert method == "tinkoff"

    def test_alfa_alias(self):
        """Test alfa alias for alfabank."""
        to_curr, method = detect_rub_method(["alfa", "rub"])
        assert method == "alfabank"

    def test_vtb(self):
        """Test vtb detection."""
        to_curr, method = detect_rub_method(["vtb", "rub"])
        assert method == "vtb"

    def test_just_rub(self):
        """Test just rub without method."""
        to_curr, method = detect_rub_method(["rub"])
        assert to_curr == "RUB"
        assert method is None

    def test_non_rub(self):
        """Test non-RUB currency."""
        to_curr, method = detect_rub_method(["amd"])
        assert to_curr == "AMD"
        assert method is None
