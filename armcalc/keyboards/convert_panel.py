"""
Convert panel inline keyboard.

Beautiful clean UI for currency conversion with predefined pairs.
"""

from typing import Dict, Optional, Set

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from armcalc.services.convert_state import ConvertState, AvailabilityResult


class ConvertPanelCallback(CallbackData, prefix="cvt"):
    """Callback data for convert panel."""

    action: str
    value: str = ""


def get_convert_panel_keyboard(
    state: ConvertState,
    allowed: Optional[Dict[str, Set[str]]] = None,
) -> InlineKeyboardMarkup:
    """
    Build beautiful convert panel keyboard with Sell/Buy USDT sections.
    """
    rows = []

    # Header row: Amount display + Edit
    rows.append([
        InlineKeyboardButton(
            text=f"💵 {state.amount:,.0f}",
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

    # ═══════════════════════════════════
    # SELL USDT Section (USDT → ...)
    # ═══════════════════════════════════
    rows.append([
        InlineKeyboardButton(
            text="📤 Sell USDT →",
            callback_data=ConvertPanelCallback(action="noop").pack()
        ),
    ])

    # Cash row
    rows.append([
        InlineKeyboardButton(
            text="💵 Cash",
            callback_data=ConvertPanelCallback(action="noop").pack()
        ),
    ])

    # USD Cash Yerevan, AMD Cash Yerevan
    rows.append([
        InlineKeyboardButton(
            text="🇦🇲 USD Yerevan",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_to_usd_cash").pack()
        ),
        InlineKeyboardButton(
            text="🇦🇲 AMD Yerevan",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_to_amd_cash").pack()
        ),
    ])

    # USD Cash LA
    rows.append([
        InlineKeyboardButton(
            text="🇺🇸 USD Los Angeles",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_to_usd_la").pack()
        ),
    ])

    # Card row
    rows.append([
        InlineKeyboardButton(
            text="💳 Card",
            callback_data=ConvertPanelCallback(action="noop").pack()
        ),
    ])

    # AMD Card, RUB Card
    rows.append([
        InlineKeyboardButton(
            text="🇦🇲 AMD",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_to_amd_card").pack()
        ),
        InlineKeyboardButton(
            text="🇷🇺 RUB",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_to_rub_card").pack()
        ),
    ])

    # KZT, GEL, AED
    rows.append([
        InlineKeyboardButton(
            text="🇰🇿 KZT",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_to_kzt_card").pack()
        ),
        InlineKeyboardButton(
            text="🇬🇪 GEL",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_to_gel_card").pack()
        ),
        InlineKeyboardButton(
            text="🇦🇪 AED",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_to_aed_card").pack()
        ),
    ])

    # ═══════════════════════════════════
    # BUY USDT Section (... → USDT)
    # ═══════════════════════════════════
    rows.append([
        InlineKeyboardButton(
            text="📥 Buy USDT ←",
            callback_data=ConvertPanelCallback(action="noop").pack()
        ),
    ])

    # Cash to USDT
    rows.append([
        InlineKeyboardButton(
            text="🇦🇲 USD →",
            callback_data=ConvertPanelCallback(action="pair", value="usd_cash_to_usdt").pack()
        ),
        InlineKeyboardButton(
            text="🇦🇲 AMD →",
            callback_data=ConvertPanelCallback(action="pair", value="amd_cash_to_usdt").pack()
        ),
    ])

    # RUB to USDT
    rows.append([
        InlineKeyboardButton(
            text="🇷🇺 RUB →",
            callback_data=ConvertPanelCallback(action="pair", value="rub_to_usdt").pack()
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
    """Render clean panel message text."""
    amount_str = f"{state.amount:,.0f}"

    lines = [
        "💱 <b>Currency Exchange</b>",
        "",
        f"Amount: <b>{amount_str}</b>",
    ]

    # Show result if available
    if state.last_result:
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━")
        lines.append(f"<b>{state.last_result}</b>")
        if state.last_rate:
            lines.append(f"<i>{state.last_rate}</i>")
    else:
        lines.append("")
        lines.append("<i>Select conversion below</i>")

    return "\n".join(lines)


def render_amount_prompt() -> str:
    """Render the amount input prompt."""
    return (
        "✏️ <b>Enter Amount</b>\n\n"
        "Send a number (e.g., <code>100</code> or <code>5000</code>)\n\n"
        "<i>Or tap quick amount buttons</i>"
    )
