"""Tests for convert state management."""

from decimal import Decimal
import pytest

from armcalc.services.convert_state import (
    ConvertState,
    create_state,
    set_amount,
    set_from_code,
    set_to_code,
    swap_currencies,
    set_usdt_network,
    set_amd_unit,
    set_rub_method,
    set_result,
    get_xml_codes,
    get_display_from,
    get_display_to,
    involves_usdt,
    involves_amd,
    involves_rub,
)


class TestCreateState:
    """Test state creation."""

    def test_default_values(self):
        """Test default state values."""
        state = create_state()

        assert state.amount == Decimal("100")
        assert state.from_code == "usdt"
        assert state.to_code == "amd"
        assert state.usdt_network == "trc20"
        assert state.amd_unit == "cash"
        assert state.rub_method == "sberbank"
        assert state.last_result is None
        assert state.last_rate is None


class TestSetAmount:
    """Test amount setting."""

    def test_valid_amount(self):
        """Test setting valid amount."""
        state = create_state()
        state, error = set_amount(state, "500")

        assert error is None
        assert state.amount == Decimal("500")

    def test_decimal_amount(self):
        """Test setting decimal amount."""
        state = create_state()
        state, error = set_amount(state, "100.50")

        assert error is None
        assert state.amount == Decimal("100.50")

    def test_amount_with_comma(self):
        """Test amount with comma separator."""
        state = create_state()
        state, error = set_amount(state, "1,000")

        assert error is None
        assert state.amount == Decimal("1000")

    def test_negative_amount(self):
        """Test negative amount rejected."""
        state = create_state()
        state, error = set_amount(state, "-100")

        assert error == "Amount must be positive"
        assert state.amount == Decimal("100")  # Unchanged

    def test_invalid_amount(self):
        """Test invalid amount rejected."""
        state = create_state()
        state, error = set_amount(state, "abc")

        assert error == "Invalid number format"

    def test_too_large_amount(self):
        """Test too large amount rejected."""
        state = create_state()
        state, error = set_amount(state, "9999999999999")

        assert error == "Amount too large"

    def test_clears_result(self):
        """Test amount change clears previous result."""
        state = create_state()
        state = set_result(state, "Test result", "Test rate")
        state, _ = set_amount(state, "200")

        assert state.last_result is None


class TestSetCurrencies:
    """Test currency setting."""

    def test_set_from_code(self):
        """Test setting from currency."""
        state = create_state()
        state = set_from_code(state, "amd")

        assert state.from_code == "amd"

    def test_set_to_code(self):
        """Test setting to currency."""
        state = create_state()
        state = set_to_code(state, "rub")

        assert state.to_code == "rub"

    def test_set_from_same_as_to_swaps(self):
        """Test setting from same as to triggers swap."""
        state = create_state()
        assert state.from_code == "usdt"
        assert state.to_code == "amd"

        state = set_from_code(state, "amd")

        assert state.from_code == "amd"
        assert state.to_code == "usdt"  # Swapped

    def test_set_to_same_as_from_swaps(self):
        """Test setting to same as from triggers swap."""
        state = create_state()
        state = set_to_code(state, "usdt")

        assert state.to_code == "usdt"
        assert state.from_code == "amd"  # Swapped

    def test_swap_currencies(self):
        """Test swapping currencies."""
        state = create_state()
        state = swap_currencies(state)

        assert state.from_code == "amd"
        assert state.to_code == "usdt"


class TestSetOptions:
    """Test option setting."""

    def test_set_usdt_network(self):
        """Test setting USDT network."""
        state = create_state()
        state = set_usdt_network(state, "bep20")

        assert state.usdt_network == "bep20"

    def test_set_invalid_network_ignored(self):
        """Test invalid network is ignored."""
        state = create_state()
        state = set_usdt_network(state, "invalid")

        assert state.usdt_network == "trc20"  # Unchanged

    def test_set_amd_unit(self):
        """Test setting AMD unit."""
        state = create_state()
        state = set_amd_unit(state, "card")

        assert state.amd_unit == "card"

    def test_set_rub_method(self):
        """Test setting RUB method."""
        state = create_state()
        state = set_rub_method(state, "tinkoff")

        assert state.rub_method == "tinkoff"


class TestGetXmlCodes:
    """Test XML code generation."""

    def test_usdt_to_amd_default(self):
        """Test USDT to AMD with defaults."""
        state = create_state()
        from_code, to_code, method = get_xml_codes(state)

        assert from_code == "USDTTRC20"
        assert to_code == "CASHAMD"
        assert method is None

    def test_usdt_bep20(self):
        """Test USDT with BEP20 network."""
        state = create_state()
        state = set_usdt_network(state, "bep20")
        from_code, to_code, method = get_xml_codes(state)

        assert from_code == "USDTBEP20"

    def test_amd_card(self):
        """Test AMD with card unit."""
        state = create_state()
        state = set_amd_unit(state, "card")
        from_code, to_code, method = get_xml_codes(state)

        assert to_code == "CARDAMD"

    def test_rub_with_method(self):
        """Test RUB with method."""
        state = create_state()
        state = set_to_code(state, "rub")
        from_code, to_code, method = get_xml_codes(state)

        assert to_code == "RUB"
        assert method == "sberbank"


class TestDisplayNames:
    """Test display name generation."""

    def test_display_usdt(self):
        """Test USDT display name."""
        state = create_state()
        code, detail = get_display_from(state)

        assert code == "USDT"
        assert detail == "TRC20"

    def test_display_amd(self):
        """Test AMD display name."""
        state = create_state()
        code, detail = get_display_to(state)

        assert code == "AMD"
        assert detail == "Cash"

    def test_display_rub(self):
        """Test RUB display name."""
        state = create_state()
        state = set_to_code(state, "rub")
        code, detail = get_display_to(state)

        assert code == "RUB"
        assert detail == "Sberbank"


class TestInvolves:
    """Test involves_* functions."""

    def test_involves_usdt_from(self):
        """Test involves USDT when from is USDT."""
        state = create_state()
        assert involves_usdt(state) is True

    def test_involves_usdt_to(self):
        """Test involves USDT when to is USDT."""
        state = create_state()
        state = swap_currencies(state)
        assert involves_usdt(state) is True

    def test_not_involves_usdt(self):
        """Test not involves USDT."""
        state = create_state()
        state = set_from_code(state, "usd")
        state = set_to_code(state, "rub")
        assert involves_usdt(state) is False

    def test_involves_amd(self):
        """Test involves AMD."""
        state = create_state()
        assert involves_amd(state) is True

    def test_involves_rub(self):
        """Test involves RUB."""
        state = create_state()
        state = set_to_code(state, "rub")
        assert involves_rub(state) is True


class TestSetResult:
    """Test result setting."""

    def test_set_result(self):
        """Test setting result."""
        state = create_state()
        state = set_result(state, "38,500 AMD", "1 USDT = 385.00 AMD")

        assert state.last_result == "38,500 AMD"
        assert state.last_rate == "1 USDT = 385.00 AMD"


# =============================================================================
# Availability Engine Tests
# =============================================================================

from armcalc.services.convert_state import (
    check_availability,
    auto_fix_state,
    get_allowed_options,
    AUTO_FIX_UNAVAILABLE,
)


class TestCheckAvailability:
    """Test availability checking."""

    def test_available_pair(self):
        """Test checking an available pair."""
        state = create_state()  # usdt -> amd with trc20/cash defaults
        available_pairs = {("USDTTRC20", "CASHAMD")}

        result = check_availability(state, available_pairs)

        assert result.available is True
        assert result.from_xml == "USDTTRC20"
        assert result.to_xml == "CASHAMD"

    def test_unavailable_pair(self):
        """Test checking an unavailable pair (card AMD)."""
        state = create_state()
        state = set_amd_unit(state, "card")
        available_pairs = {("USDTTRC20", "CASHAMD")}  # Only cash available

        result = check_availability(state, available_pairs)

        assert result.available is False
        assert "CARDAMD" in result.to_xml
        assert result.reason is not None

    def test_suggests_alternative(self):
        """Test that unavailable pair suggests alternatives."""
        state = create_state()
        state = set_amd_unit(state, "card")
        available_pairs = {("USDTTRC20", "CASHAMD")}

        result = check_availability(state, available_pairs)

        assert result.available is False
        assert len(result.suggestions) > 0
        # Should suggest AMD Cash
        suggestion_values = [s[1] for s in result.suggestions]
        assert "cash" in suggestion_values

    def test_unavailable_network(self):
        """Test unavailable USDT network suggests alternatives."""
        state = create_state()
        state = set_usdt_network(state, "erc20")
        available_pairs = {("USDTTRC20", "CASHAMD"), ("USDTBEP20", "CASHAMD")}

        result = check_availability(state, available_pairs)

        assert result.available is False
        # Should suggest TRC20 or BEP20
        suggestion_values = [s[1] for s in result.suggestions]
        assert "trc20" in suggestion_values or "bep20" in suggestion_values


class TestAutoFixState:
    """Test auto-fix functionality."""

    def test_auto_fix_amd_unit(self):
        """Test auto-fix changes AMD card to cash."""
        state = create_state()
        state = set_amd_unit(state, "card")
        available_pairs = {("USDTTRC20", "CASHAMD")}

        fixed_state, result = auto_fix_state(state, available_pairs)

        if AUTO_FIX_UNAVAILABLE:
            assert fixed_state.amd_unit == "cash"
            assert result.adjusted is True
            assert result.adjustment_msg is not None

    def test_auto_fix_network(self):
        """Test auto-fix changes network if unavailable."""
        state = create_state()
        state = set_usdt_network(state, "sol")
        available_pairs = {("USDTTRC20", "CASHAMD")}

        fixed_state, result = auto_fix_state(state, available_pairs)

        if AUTO_FIX_UNAVAILABLE:
            assert fixed_state.usdt_network == "trc20"
            assert result.adjusted is True

    def test_no_fix_when_available(self):
        """Test no fix applied when already available."""
        state = create_state()  # Default: usdt trc20 -> amd cash
        available_pairs = {("USDTTRC20", "CASHAMD")}

        fixed_state, result = auto_fix_state(state, available_pairs)

        assert result.adjusted is False
        assert result.available is True


class TestGetAllowedOptions:
    """Test allowed options calculation."""

    def test_allowed_networks(self):
        """Test getting allowed USDT networks."""
        state = create_state()
        available_pairs = {
            ("USDTTRC20", "CASHAMD"),
            ("USDTBEP20", "CASHAMD"),
        }

        allowed = get_allowed_options(state, available_pairs)

        assert "trc20" in allowed["networks"]
        assert "bep20" in allowed["networks"]
        assert "erc20" not in allowed["networks"]

    def test_allowed_amd_units(self):
        """Test getting allowed AMD units."""
        state = create_state()
        available_pairs = {
            ("USDTTRC20", "CASHAMD"),
            ("USDTTRC20", "CARDAMD"),
        }

        allowed = get_allowed_options(state, available_pairs)

        assert "cash" in allowed["amd_units"]
        assert "card" in allowed["amd_units"]

    def test_allowed_rub_methods(self):
        """Test getting allowed RUB methods."""
        state = create_state()
        state = set_to_code(state, "rub")
        available_pairs = {
            ("USDTTRC20", "SBERRUB"),
            ("USDTTRC20", "TCSBRUB"),
        }

        allowed = get_allowed_options(state, available_pairs)

        assert "sberbank" in allowed["rub_methods"]
        assert "tinkoff" in allowed["rub_methods"]
        assert "vtb" not in allowed["rub_methods"]

    def test_only_cash_amd_available(self):
        """Test when only cash AMD is available."""
        state = create_state()
        available_pairs = {("USDTTRC20", "CASHAMD")}

        allowed = get_allowed_options(state, available_pairs)

        assert "cash" in allowed["amd_units"]
        assert "card" not in allowed["amd_units"]
