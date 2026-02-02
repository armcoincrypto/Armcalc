"""
Convert panel inline keyboard.

Beautiful clean UI for currency conversion with predefined pairs.
"""

from typing import Dict, Optional, Set

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from armcalc.services.convert_state import (
    ConvertState,
    AvailabilityResult,
)


class ConvertPanelCallback(CallbackData, prefix="cvt"):
    """Callback data for convert panel."""

    action: str
    value: str = ""


# Predefined conversion pairs with display names
CONVERSION_PAIRS = [
    # (id, from_code, to_code, display_name, emoji)
    ("usdt_usd_cash_yerevan", "usdt", "usd_cash_yerevan", "USD Cash Yerevan", "🇦🇲"),
    ("usdt_amd_cash_yerevan", "usdt", "amd_cash", "AMD Cash Yerevan", "🇦🇲"),
    ("usdt_usd_cash_la", "usdt", "usd_cash_la", "USD Cash LA", "🇺🇸"),
    ("usdt_amd_card", "usdt", "amd_card", "AMD Card", "💳"),
    ("usdt_rub_card", "usdt", "rub_card", "RUB Card", "🇷🇺"),
    ("usdt_kzt_card", "usdt", "kzt_card", "KZT Card", "🇰🇿"),
    ("usdt_gel_card", "usdt", "gel_card", "GEL Card", "🇬🇪"),
    ("usdt_aed_card", "usdt", "aed_card", "AED Card", "🇦🇪"),
]


def get_convert_panel_keyboard(
    state: ConvertState,
    allowed: Optional[Dict[str, Set[str]]] = None,
) -> InlineKeyboardMarkup:
    """
    Build beautiful convert panel keyboard.

    Args:
        state: Current conversion state
        allowed: Dict with allowed options (unused in new design)
    """
    rows = []

    # Header row: Amount display + Edit
    rows.append([
        InlineKeyboardButton(
            text=f"💵 {state.amount:,.0f} USDT",
            callback_data=ConvertPanelCallback(action="show_amount").pack()
        ),
        InlineKeyboardButton(
            text="✏️",
            callback_data=ConvertPanelCallback(action="amount").pack()
        ),
    ])

    # Quick amount buttons
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
            text="1K",
            callback_data=ConvertPanelCallback(action="quick_amount", value="1000").pack()
        ),
        InlineKeyboardButton(
            text="5K",
            callback_data=ConvertPanelCallback(action="quick_amount", value="5000").pack()
        ),
        InlineKeyboardButton(
            text="10K",
            callback_data=ConvertPanelCallback(action="quick_amount", value="10000").pack()
        ),
    ])

    # Separator
    rows.append([
        InlineKeyboardButton(
            text="━━━━ USDT → ━━━━",
            callback_data=ConvertPanelCallback(action="noop").pack()
        ),
    ])

    # Cash section header
    rows.append([
        InlineKeyboardButton(
            text="💵 Cash",
            callback_data=ConvertPanelCallback(action="noop").pack()
        ),
    ])

    # Cash options: 2 per row
    # Row 1: USD Cash Yerevan, AMD Cash Yerevan
    rows.append([
        InlineKeyboardButton(
            text="🇦🇲 USD Yerevan",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_usd_cash_yerevan").pack()
        ),
        InlineKeyboardButton(
            text="🇦🇲 AMD Yerevan",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_amd_cash_yerevan").pack()
        ),
    ])

    # Row 2: USD Cash LA
    rows.append([
        InlineKeyboardButton(
            text="🇺🇸 USD Los Angeles",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_usd_cash_la").pack()
        ),
    ])

    # Card section header
    rows.append([
        InlineKeyboardButton(
            text="💳 Card",
            callback_data=ConvertPanelCallback(action="noop").pack()
        ),
    ])

    # Card options: 2 per row
    # Row 1: AMD Card, RUB Card
    rows.append([
        InlineKeyboardButton(
            text="🇦🇲 AMD",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_amd_card").pack()
        ),
        InlineKeyboardButton(
            text="🇷🇺 RUB",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_rub_card").pack()
        ),
    ])

    # Row 2: KZT Card, GEL Card
    rows.append([
        InlineKeyboardButton(
            text="🇰🇿 KZT",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_kzt_card").pack()
        ),
        InlineKeyboardButton(
            text="🇬🇪 GEL",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_gel_card").pack()
        ),
    ])

    # Row 3: AED Card
    rows.append([
        InlineKeyboardButton(
            text="🇦🇪 AED",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_aed_card").pack()
        ),
    ])

    # Close button
    rows.append([
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
    Render clean panel message text.

    Args:
        state: Current conversion state
        availability: Availability check result (optional)
    """
    # Format amount with thousands separator
    amount_str = f"{state.amount:,.0f}"

    lines = [
        "💱 <b>Exchange USDT</b>",
        "",
        f"Amount: <b>{amount_str} USDT</b>",
        "",
        "<i>Select destination below:</i>",
    ]

    # Show result if available
    if state.last_result:
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━")
        lines.append(f"<b>Result: {state.last_result}</b>")
        if state.last_rate:
            lines.append(f"<i>{state.last_rate}</i>")

    return "\n".join(lines)


def render_result_panel(
    amount: str,
    from_display: str,
    to_display: str,
    result: str,
    rate: str,
) -> str:
    """Render conversion result panel."""
    return (
        f"💱 <b>Conversion Result</b>\n"
        f"\n"
        f"{amount} {from_display}\n"
        f"      ↓\n"
        f"<b>{result}</b>\n"
        f"\n"
        f"<i>Rate: {rate}</i>"
    )


def render_amount_prompt() -> str:
    """Render the amount input prompt."""
    return (
        "✏️ <b>Enter Amount</b>\n\n"
        "Send a number (e.g., <code>100</code> or <code>5000</code>)\n\n"
        "<i>Or tap quick amount buttons</i>"
    )
