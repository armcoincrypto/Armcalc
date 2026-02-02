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


def cleanup_expired_states() -> int:
    """Remove expired states. Returns count of removed states."""
    expired = [uid for uid, state in _user_states.items() if state.is_expired()]
    for uid in expired:
        del _user_states[uid]
    return len(expired)
