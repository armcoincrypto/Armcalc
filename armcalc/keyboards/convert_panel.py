"""
Convert panel inline keyboard.

Provides the interactive UI for currency conversion with availability checking.
"""

from typing import Dict, Optional, Set

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from armcalc.services.convert_state import (
    ConvertState,
    AvailabilityResult,
    involves_usdt,
    involves_amd,
    involves_rub,
    get_display_from,
    get_display_to,
    USDT_NETWORKS,
    AMD_UNITS,
    RUB_METHODS,
)


class ConvertPanelCallback(CallbackData, prefix="cvt"):
    """Callback data for convert panel."""

    action: str
    value: str = ""


def get_convert_panel_keyboard(
    state: ConvertState,
    allowed: Optional[Dict[str, Set[str]]] = None,
) -> InlineKeyboardMarkup:
    """
    Build the convert panel keyboard based on current state.

    Args:
        state: Current conversion state
        allowed: Dict with allowed options for networks/amd_units/rub_methods
                If None, all options are shown as available.
    """
    rows = []

    # Default to all allowed if not specified
    if allowed is None:
        allowed = {
            "networks": set(USDT_NETWORKS),
            "amd_units": set(AMD_UNITS),
            "rub_methods": set(RUB_METHODS),
        }

    # Row 1: Actions
    rows.append([
        InlineKeyboardButton(
            text="✏️ Amount",
            callback_data=ConvertPanelCallback(action="amount").pack()
        ),
        InlineKeyboardButton(
            text="🔁 Swap",
            callback_data=ConvertPanelCallback(action="swap").pack()
        ),
        InlineKeyboardButton(
            text="✅ Convert",
            callback_data=ConvertPanelCallback(action="convert").pack()
        ),
    ])

    # Row 2: From selector
    from_buttons = []
    for curr in ["usdt", "amd", "usd", "rub"]:
        is_selected = state.from_code == curr
        text = f"{'•' if is_selected else ''}{curr.upper()}"
        from_buttons.append(InlineKeyboardButton(
            text=text,
            callback_data=ConvertPanelCallback(action="from", value=curr).pack()
        ))
    rows.append(from_buttons)

    # Row 3: To selector
    to_buttons = []
    for curr in ["amd", "usdt", "usd", "rub"]:
        is_selected = state.to_code == curr
        text = f"→{'•' if is_selected else ''}{curr.upper()}"
        to_buttons.append(InlineKeyboardButton(
            text=text,
            callback_data=ConvertPanelCallback(action="to", value=curr).pack()
        ))
    rows.append(to_buttons)

    # Row 4: USDT Networks (only if USDT involved)
    if involves_usdt(state):
        network_buttons = []
        allowed_nets = allowed.get("networks", set())
        for net in USDT_NETWORKS:
            is_selected = state.usdt_network == net
            is_allowed = net in allowed_nets or not allowed_nets

            if is_allowed:
                text = f"{'•' if is_selected else ''}{net.upper()}"
            else:
                text = f"🚫{net.upper()}" if is_selected else f"—{net.upper()}"

            network_buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=ConvertPanelCallback(action="network", value=net).pack()
            ))
        rows.append(network_buttons)

    # Row 5: AMD Units (only if AMD involved)
    if involves_amd(state):
        unit_buttons = []
        allowed_units = allowed.get("amd_units", set())
        for unit in AMD_UNITS:
            is_selected = state.amd_unit == unit
            is_allowed = unit in allowed_units or not allowed_units

            if is_allowed:
                text = f"{'•' if is_selected else ''}{unit.title()}"
            else:
                text = f"🚫{unit.title()}" if is_selected else f"—{unit.title()}"

            unit_buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=ConvertPanelCallback(action="amd_unit", value=unit).pack()
            ))
        rows.append(unit_buttons)

    # Row 6: RUB Methods (only if RUB involved)
    if involves_rub(state):
        method_buttons = []
        allowed_methods = allowed.get("rub_methods", set())
        for method in RUB_METHODS:
            is_selected = state.rub_method == method
            is_allowed = method in allowed_methods or not allowed_methods

            if is_allowed:
                text = f"{'•' if is_selected else ''}{method.title()}"
            else:
                text = f"🚫{method.title()}" if is_selected else f"—{method.title()}"

            method_buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=ConvertPanelCallback(action="rub_method", value=method).pack()
            ))
        rows.append(method_buttons)

    # Row 7: Quick amounts
    rows.append([
        InlineKeyboardButton(
            text="100",
            callback_data=ConvertPanelCallback(action="quick_amount", value="100").pack()
        ),
        InlineKeyboardButton(
            text="500",
            callback_data=ConvertPanelCallback(action="quick_amount", value="500").pack()
        ),
        InlineKeyboardButton(
            text="1000",
            callback_data=ConvertPanelCallback(action="quick_amount", value="1000").pack()
        ),
        InlineKeyboardButton(
            text="5000",
            callback_data=ConvertPanelCallback(action="quick_amount", value="5000").pack()
        ),
    ])

    # Row 8: Options & Close
    rows.append([
        InlineKeyboardButton(
            text="📋 /pairs",
            callback_data=ConvertPanelCallback(action="show_pairs").pack()
        ),
        InlineKeyboardButton(
            text="❌ Close",
            callback_data=ConvertPanelCallback(action="close").pack()
        ),
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def render_panel_text(
    state: ConvertState,
    availability: Optional[AvailabilityResult] = None,
) -> str:
    """
    Render the panel message text with availability status.

    Args:
        state: Current conversion state
        availability: Availability check result (optional)
    """
    from_code, from_detail = get_display_from(state)
    to_code, to_detail = get_display_to(state)

    # Format amount with thousands separator
    amount_str = f"{state.amount:,.2f}".rstrip('0').rstrip('.')

    lines = [
        "💱 <b>Converter</b>",
        "",
        f"Amount: <b>{amount_str}</b>",
        f"From: <b>{from_code}</b>" + (f" (<code>{from_detail}</code>)" if from_detail else ""),
        f"To: <b>{to_code}</b>" + (f" (<code>{to_detail}</code>)" if to_detail else ""),
    ]

    # Show RUB method only when RUB is involved
    if involves_rub(state):
        lines.append(f"Method: <b>{state.rub_method.title()}</b>")

    lines.append("")

    # Show availability status
    if availability:
        if availability.available:
            lines.append("Status: ✅ Available")
        else:
            lines.append(f"Status: ❌ {availability.reason or 'Not available'}")
            # Show suggestions
            if availability.suggestions:
                suggestions_text = " • ".join(s[2] for s in availability.suggestions)
                lines.append(f"<i>Try: {suggestions_text}</i>")

        # Show adjustment message if auto-fixed
        if availability.adjusted and availability.adjustment_msg:
            lines.append(f"<i>Adjusted: {availability.adjustment_msg}</i>")

        lines.append("")

    # Show result if available
    if state.last_result:
        lines.append(f"<b>Result: {state.last_result}</b>")
        if state.last_rate:
            lines.append(f"<i>Rate: {state.last_rate}</i>")
    else:
        if availability and availability.available:
            lines.append("<i>Tap ✅ Convert to calculate</i>")
        elif availability and not availability.available:
            lines.append("<i>Select available options above</i>")
        else:
            lines.append("<i>Tap ✅ Convert to calculate</i>")

    return "\n".join(lines)


def render_amount_prompt() -> str:
    """Render the amount input prompt."""
    return (
        "✏️ <b>Enter Amount</b>\n\n"
        "Send a number (e.g., <code>100</code> or <code>1500.50</code>)\n\n"
        "<i>Or tap a quick amount button above</i>"
    )
