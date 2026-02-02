"""
Convert panel inline keyboard.

Provides the interactive UI for currency conversion.
"""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from armcalc.services.convert_state import (
    ConvertState,
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


def get_convert_panel_keyboard(state: ConvertState) -> InlineKeyboardMarkup:
    """
    Build the convert panel keyboard based on current state.

    Dynamic rows based on which currencies are involved.
    """
    rows = []

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
        for net in USDT_NETWORKS:
            is_selected = state.usdt_network == net
            text = f"{'•' if is_selected else ''}{net.upper()}"
            network_buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=ConvertPanelCallback(action="network", value=net).pack()
            ))
        rows.append(network_buttons)

    # Row 5: AMD Units (only if AMD involved)
    if involves_amd(state):
        unit_buttons = []
        for unit in AMD_UNITS:
            is_selected = state.amd_unit == unit
            text = f"{'•' if is_selected else ''}{unit.title()}"
            unit_buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=ConvertPanelCallback(action="amd_unit", value=unit).pack()
            ))
        rows.append(unit_buttons)

    # Row 6: RUB Methods (only if RUB involved)
    if involves_rub(state):
        method_buttons = []
        for method in RUB_METHODS:
            is_selected = state.rub_method == method
            text = f"{'•' if is_selected else ''}{method.title()}"
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

    # Row 8: Close
    rows.append([
        InlineKeyboardButton(
            text="❌ Close",
            callback_data=ConvertPanelCallback(action="close").pack()
        ),
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def render_panel_text(state: ConvertState) -> str:
    """
    Render the panel message text.

    Shows current selection and result if available.
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

    # Show result if available
    if state.last_result:
        lines.append(f"<b>Result: {state.last_result}</b>")
        if state.last_rate:
            lines.append(f"<i>Rate: {state.last_rate}</i>")
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
