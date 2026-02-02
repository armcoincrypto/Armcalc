"""
Convert panel state management.

Pure functions for managing conversion state, enabling easy testing.
"""

import time
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional, Tuple

# State TTL in seconds (30 minutes)
STATE_TTL_SEC = 1800


@dataclass
class ConvertState:
    """User's conversion panel state."""

    amount: Decimal = Decimal("100")
    from_code: str = "usdt"
    to_code: str = "amd"
    usdt_network: str = "trc20"  # trc20, bep20, erc20, ton, sol
    amd_unit: str = "cash"  # cash, card
    rub_method: str = "sberbank"  # sberbank, tinkoff, alfa, vtb
    last_result: Optional[str] = None  # Last conversion result
    last_rate: Optional[str] = None  # Last rate used
    timestamp: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        """Check if state has expired."""
        return time.time() - self.timestamp > STATE_TTL_SEC

    def touch(self) -> "ConvertState":
        """Update timestamp to keep state alive."""
        self.timestamp = time.time()
        return self


# Available options
CURRENCIES = ["usdt", "amd", "usd", "rub"]
USDT_NETWORKS = ["trc20", "bep20", "erc20", "ton", "sol"]
AMD_UNITS = ["cash", "card"]
RUB_METHODS = ["sberbank", "tinkoff", "alfa", "vtb"]


def create_state() -> ConvertState:
    """Create a new default state."""
    return ConvertState()


def set_amount(state: ConvertState, amount_str: str) -> Tuple[ConvertState, Optional[str]]:
    """
    Set amount from string input.

    Returns (updated_state, error_message).
    """
    try:
        # Clean input: remove commas, spaces
        cleaned = amount_str.replace(",", "").replace(" ", "").strip()
        amount = Decimal(cleaned)

        if amount <= 0:
            return state, "Amount must be positive"
        if amount > Decimal("1000000000"):
            return state, "Amount too large"

        state.amount = amount
        state.last_result = None  # Clear previous result
        state.touch()
        return state, None
    except InvalidOperation:
        return state, "Invalid number format"


def set_from_code(state: ConvertState, code: str) -> ConvertState:
    """Set the source currency."""
    code = code.lower()
    if code in CURRENCIES:
        # If setting from same as to, swap them
        if code == state.to_code:
            state.to_code = state.from_code
        state.from_code = code
        state.last_result = None
        state.touch()
    return state


def set_to_code(state: ConvertState, code: str) -> ConvertState:
    """Set the target currency."""
    code = code.lower()
    if code in CURRENCIES:
        # If setting to same as from, swap them
        if code == state.from_code:
            state.from_code = state.to_code
        state.to_code = code
        state.last_result = None
        state.touch()
    return state


def swap_currencies(state: ConvertState) -> ConvertState:
    """Swap from and to currencies."""
    state.from_code, state.to_code = state.to_code, state.from_code
    state.last_result = None
    state.touch()
    return state


def set_usdt_network(state: ConvertState, network: str) -> ConvertState:
    """Set USDT network."""
    network = network.lower()
    if network in USDT_NETWORKS:
        state.usdt_network = network
        state.last_result = None
        state.touch()
    return state


def set_amd_unit(state: ConvertState, unit: str) -> ConvertState:
    """Set AMD unit (cash/card)."""
    unit = unit.lower()
    if unit in AMD_UNITS:
        state.amd_unit = unit
        state.last_result = None
        state.touch()
    return state


def set_rub_method(state: ConvertState, method: str) -> ConvertState:
    """Set RUB payment method."""
    method = method.lower()
    if method in RUB_METHODS:
        state.rub_method = method
        state.last_result = None
        state.touch()
    return state


def set_result(state: ConvertState, result: str, rate: str) -> ConvertState:
    """Store conversion result."""
    state.last_result = result
    state.last_rate = rate
    state.touch()
    return state


def get_xml_codes(state: ConvertState) -> Tuple[str, str, Optional[str]]:
    """
    Get XML-compatible codes from state.

    Returns (from_code, to_code, method).
    """
    from_code = state.from_code.upper()
    to_code = state.to_code.upper()
    method = None

    # Map USDT to specific network
    if from_code == "USDT":
        network_map = {
            "trc20": "USDTTRC20",
            "bep20": "USDTBEP20",
            "erc20": "USDTERC20",
            "ton": "USDTTON",
            "sol": "USDTSOL",
        }
        from_code = network_map.get(state.usdt_network, "USDTTRC20")

    if to_code == "USDT":
        network_map = {
            "trc20": "USDTTRC20",
            "bep20": "USDTBEP20",
            "erc20": "USDTERC20",
            "ton": "USDTTON",
            "sol": "USDTSOL",
        }
        to_code = network_map.get(state.usdt_network, "USDTTRC20")

    # Map AMD to specific unit
    if from_code == "AMD":
        from_code = "CASHAMD" if state.amd_unit == "cash" else "CARDAMD"
    if to_code == "AMD":
        to_code = "CASHAMD" if state.amd_unit == "cash" else "CARDAMD"

    # Map USD to CASHUSD
    if from_code == "USD":
        from_code = "CASHUSD"
    if to_code == "USD":
        to_code = "CASHUSD"

    # Handle RUB method
    if to_code == "RUB" or from_code == "RUB":
        method = state.rub_method

    return from_code, to_code, method


def get_display_from(state: ConvertState) -> Tuple[str, str]:
    """Get display name and detail for source currency."""
    code = state.from_code.upper()
    detail = ""

    if code == "USDT":
        detail = state.usdt_network.upper()
    elif code == "AMD":
        detail = state.amd_unit.title()
    elif code == "RUB":
        detail = state.rub_method.title()

    return code, detail


def get_display_to(state: ConvertState) -> Tuple[str, str]:
    """Get display name and detail for target currency."""
    code = state.to_code.upper()
    detail = ""

    if code == "USDT":
        detail = state.usdt_network.upper()
    elif code == "AMD":
        detail = state.amd_unit.title()
    elif code == "RUB":
        detail = state.rub_method.title()

    return code, detail


def involves_usdt(state: ConvertState) -> bool:
    """Check if conversion involves USDT."""
    return state.from_code == "usdt" or state.to_code == "usdt"


def involves_amd(state: ConvertState) -> bool:
    """Check if conversion involves AMD."""
    return state.from_code == "amd" or state.to_code == "amd"


def involves_rub(state: ConvertState) -> bool:
    """Check if conversion involves RUB."""
    return state.from_code == "rub" or state.to_code == "rub"


# Global state storage with TTL cleanup
_user_states: Dict[int, ConvertState] = {}


def get_user_state(user_id: int) -> ConvertState:
    """Get or create user state."""
    state = _user_states.get(user_id)
    if state is None or state.is_expired():
        state = create_state()
        _user_states[user_id] = state
    return state


def save_user_state(user_id: int, state: ConvertState) -> None:
    """Save user state."""
    _user_states[user_id] = state


def clear_user_state(user_id: int) -> None:
    """Clear user state."""
    _user_states.pop(user_id, None)


def has_active_state(user_id: int) -> bool:
    """Check if user has an active (non-expired) convert panel state."""
    state = _user_states.get(user_id)
    return state is not None and not state.is_expired()


def cleanup_expired_states() -> int:
    """Remove expired states. Returns count of removed states."""
    expired = [uid for uid, state in _user_states.items() if state.is_expired()]
    for uid in expired:
        del _user_states[uid]
    return len(expired)


# =============================================================================
# Availability Engine
# =============================================================================

# Configuration
AUTO_FIX_UNAVAILABLE = True  # Auto-fix to nearest valid option


@dataclass
class AvailabilityResult:
    """Result of availability check."""

    available: bool
    from_xml: str  # Resolved XML code
    to_xml: str  # Resolved XML code
    method: Optional[str]
    reason: Optional[str] = None  # Why not available
    suggestions: list = field(default_factory=list)  # Suggested fixes
    adjusted: bool = False  # Was state auto-adjusted?
    adjustment_msg: Optional[str] = None  # What was adjusted


def _build_xml_code(currency: str, state: ConvertState) -> str:
    """Build XML code for a currency based on state settings."""
    currency = currency.lower()

    if currency == "usdt":
        network_map = {
            "trc20": "USDTTRC20",
            "bep20": "USDTBEP20",
            "erc20": "USDTERC20",
            "ton": "USDTTON",
            "sol": "USDTSOL",
        }
        return network_map.get(state.usdt_network, "USDTTRC20")

    if currency == "amd":
        return "CASHAMD" if state.amd_unit == "cash" else "CARDAMD"

    if currency == "usd":
        return "CASHUSD"

    if currency == "rub":
        method_map = {
            "sberbank": "SBERRUB",
            "tinkoff": "TCSBRUB",
            "alfa": "ACRUB",
            "vtb": "VTBRUB",
        }
        return method_map.get(state.rub_method, "SBERRUB")

    return currency.upper()


def check_availability(
    state: ConvertState,
    available_pairs: set,  # Set of (from_xml, to_xml) tuples
) -> AvailabilityResult:
    """
    Check if current state configuration is available.

    Args:
        state: Current conversion state
        available_pairs: Set of (from_xml, to_xml) tuples from XML

    Returns:
        AvailabilityResult with status and suggestions
    """
    from_xml = _build_xml_code(state.from_code, state)
    to_xml = _build_xml_code(state.to_code, state)
    method = state.rub_method if involves_rub(state) else None

    # Check if pair exists
    pair = (from_xml, to_xml)
    if pair in available_pairs:
        return AvailabilityResult(
            available=True,
            from_xml=from_xml,
            to_xml=to_xml,
            method=method,
        )

    # Not available - find suggestions
    suggestions = []
    reason = f"{from_xml} → {to_xml} not in exchange feed"

    # Try alternative units/networks
    if state.to_code == "amd":
        # Try other AMD unit
        alt_unit = "cash" if state.amd_unit == "card" else "card"
        alt_to = "CASHAMD" if alt_unit == "cash" else "CARDAMD"
        if (from_xml, alt_to) in available_pairs:
            suggestions.append(("amd_unit", alt_unit, f"AMD {alt_unit.title()}"))
            reason = f"AMD {state.amd_unit.title()} not available"

    if state.from_code == "amd":
        alt_unit = "cash" if state.amd_unit == "card" else "card"
        alt_from = "CASHAMD" if alt_unit == "cash" else "CARDAMD"
        if (alt_from, to_xml) in available_pairs:
            suggestions.append(("amd_unit", alt_unit, f"AMD {alt_unit.title()}"))
            reason = f"AMD {state.amd_unit.title()} not available"

    if state.from_code == "usdt":
        # Try other USDT networks
        for net in USDT_NETWORKS:
            if net == state.usdt_network:
                continue
            alt_from = f"USDT{net.upper()}"
            if (alt_from, to_xml) in available_pairs:
                suggestions.append(("network", net, f"USDT {net.upper()}"))
                if not reason.startswith("USDT"):
                    reason = f"USDT {state.usdt_network.upper()} not available"

    if state.to_code == "usdt":
        for net in USDT_NETWORKS:
            if net == state.usdt_network:
                continue
            alt_to = f"USDT{net.upper()}"
            if (from_xml, alt_to) in available_pairs:
                suggestions.append(("network", net, f"USDT {net.upper()}"))
                if not reason.startswith("USDT"):
                    reason = f"USDT {state.usdt_network.upper()} not available"

    if state.to_code == "rub":
        # Try other RUB methods
        for meth in RUB_METHODS:
            if meth == state.rub_method:
                continue
            method_map = {"sberbank": "SBERRUB", "tinkoff": "TCSBRUB", "alfa": "ACRUB", "vtb": "VTBRUB"}
            alt_to = method_map.get(meth, "SBERRUB")
            if (from_xml, alt_to) in available_pairs:
                suggestions.append(("rub_method", meth, f"RUB {meth.title()}"))
                reason = f"RUB {state.rub_method.title()} not available"

    if state.from_code == "rub":
        for meth in RUB_METHODS:
            if meth == state.rub_method:
                continue
            method_map = {"sberbank": "SBERRUB", "tinkoff": "TCSBRUB", "alfa": "ACRUB", "vtb": "VTBRUB"}
            alt_from = method_map.get(meth, "SBERRUB")
            if (alt_from, to_xml) in available_pairs:
                suggestions.append(("rub_method", meth, f"RUB {meth.title()}"))
                reason = f"RUB {state.rub_method.title()} not available"

    return AvailabilityResult(
        available=False,
        from_xml=from_xml,
        to_xml=to_xml,
        method=method,
        reason=reason,
        suggestions=suggestions[:3],  # Limit to top 3
    )


def auto_fix_state(
    state: ConvertState,
    available_pairs: set,
) -> Tuple[ConvertState, AvailabilityResult]:
    """
    Automatically fix state to nearest valid configuration.

    Returns (fixed_state, availability_result with adjusted=True if changed).
    """
    result = check_availability(state, available_pairs)

    if result.available or not AUTO_FIX_UNAVAILABLE:
        return state, result

    # Apply first suggestion
    if result.suggestions:
        action, value, display = result.suggestions[0]

        if action == "amd_unit":
            old_val = state.amd_unit.title()
            state = set_amd_unit(state, value)
            result.adjusted = True
            result.adjustment_msg = f"AMD {old_val} → AMD {value.title()} (not available)"

        elif action == "network":
            old_val = state.usdt_network.upper()
            state = set_usdt_network(state, value)
            result.adjusted = True
            result.adjustment_msg = f"USDT {old_val} → USDT {value.upper()} (not available)"

        elif action == "rub_method":
            old_val = state.rub_method.title()
            state = set_rub_method(state, value)
            result.adjusted = True
            result.adjustment_msg = f"RUB {old_val} → RUB {value.title()} (not available)"

        # Re-check after fix
        new_result = check_availability(state, available_pairs)
        new_result.adjusted = result.adjusted
        new_result.adjustment_msg = result.adjustment_msg
        return state, new_result

    return state, result


def get_allowed_options(
    state: ConvertState,
    available_pairs: set,
) -> Dict[str, set]:
    """
    Get allowed options for each selector given current state.

    Returns dict with keys: networks, amd_units, rub_methods
    Each value is a set of allowed values.
    """
    allowed = {
        "networks": set(),
        "amd_units": set(),
        "rub_methods": set(),
    }

    # Check USDT networks
    if state.from_code == "usdt" or state.to_code == "usdt":
        for net in USDT_NETWORKS:
            # Build test codes
            test_state = ConvertState(
                from_code=state.from_code,
                to_code=state.to_code,
                usdt_network=net,
                amd_unit=state.amd_unit,
                rub_method=state.rub_method,
            )
            from_xml = _build_xml_code(state.from_code, test_state)
            to_xml = _build_xml_code(state.to_code, test_state)
            if (from_xml, to_xml) in available_pairs:
                allowed["networks"].add(net)

    # Check AMD units
    if state.from_code == "amd" or state.to_code == "amd":
        for unit in AMD_UNITS:
            test_state = ConvertState(
                from_code=state.from_code,
                to_code=state.to_code,
                usdt_network=state.usdt_network,
                amd_unit=unit,
                rub_method=state.rub_method,
            )
            from_xml = _build_xml_code(state.from_code, test_state)
            to_xml = _build_xml_code(state.to_code, test_state)
            if (from_xml, to_xml) in available_pairs:
                allowed["amd_units"].add(unit)

    # Check RUB methods
    if state.from_code == "rub" or state.to_code == "rub":
        for method in RUB_METHODS:
            test_state = ConvertState(
                from_code=state.from_code,
                to_code=state.to_code,
                usdt_network=state.usdt_network,
                amd_unit=state.amd_unit,
                rub_method=method,
            )
            from_xml = _build_xml_code(state.from_code, test_state)
            to_xml = _build_xml_code(state.to_code, test_state)
            if (from_xml, to_xml) in available_pairs:
                allowed["rub_methods"].add(method)

    return allowed
