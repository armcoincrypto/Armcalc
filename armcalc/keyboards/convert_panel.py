"""
Convert panel inline keyboard.

Clean UI with specific exchange pairs.
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
    """Build convert panel with specific pairs."""
    rows = []

    # ═══════════════════════════════════
    # AMOUNT SECTION
    # ═══════════════════════════════════
    rows.append([
        InlineKeyboardButton(
            text=f"💰 Amount: {state.amount:,.0f}",
            callback_data=ConvertPanelCallback(action="show_amount").pack()
        ),
        InlineKeyboardButton(
            text="✏️",
            callback_data=ConvertPanelCallback(action="amount").pack()
        ),
    ])

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

    # ═══════════════════════════════════
    # USDT → CASH
    # ═══════════════════════════════════
    rows.append([
        InlineKeyboardButton(
            text="━━━ USDT → Cash ━━━",
            callback_data=ConvertPanelCallback(action="noop").pack()
        ),
    ])

    rows.append([
        InlineKeyboardButton(
            text="🇦🇲 USD Yerevan",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_to_usd_evn").pack()
        ),
        InlineKeyboardButton(
            text="🇦🇲 AMD Yerevan",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_to_amd_evn").pack()
        ),
    ])

    rows.append([
        InlineKeyboardButton(
            text="🇺🇸 USD Los Angeles",
            callback_data=ConvertPanelCallback(action="pair", value="usdt_to_usd_la").pack()
        ),
    ])

    # ═══════════════════════════════════
    # USDT → CARD
    # ═══════════════════════════════════
    rows.append([
        InlineKeyboardButton(
            text="━━━ USDT → Card ━━━",
            callback_data=ConvertPanelCallback(action="noop").pack()
        ),
    ])

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
    # CASH → USDT
    # ═══════════════════════════════════
    rows.append([
        InlineKeyboardButton(
            text="━━━ Cash → USDT ━━━",
            callback_data=ConvertPanelCallback(action="noop").pack()
        ),
    ])

    rows.append([
        InlineKeyboardButton(
            text="🇦🇲 AMD Yerevan",
            callback_data=ConvertPanelCallback(action="pair", value="amd_evn_to_usdt").pack()
        ),
        InlineKeyboardButton(
            text="🇦🇲 USD Yerevan",
            callback_data=ConvertPanelCallback(action="pair", value="usd_evn_to_usdt").pack()
        ),
    ])

    rows.append([
        InlineKeyboardButton(
            text="🇺🇸 USD Los Angeles",
            callback_data=ConvertPanelCallback(action="pair", value="usd_la_to_usdt").pack()
        ),
    ])

    # ═══════════════════════════════════
    # CARD → USDT
    # ═══════════════════════════════════
    rows.append([
        InlineKeyboardButton(
            text="━━━ Card → USDT ━━━",
            callback_data=ConvertPanelCallback(action="noop").pack()
        ),
    ])

    rows.append([
        InlineKeyboardButton(
            text="🇷🇺 RUB",
            callback_data=ConvertPanelCallback(action="pair", value="rub_card_to_usdt").pack()
        ),
    ])

    # Close
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
    """Render panel text."""
    lines = ["💱 <b>Currency Exchange</b>"]

    if state.last_result:
        lines.append("")
        lines.append(f"<b>{state.last_result}</b>")
        if state.last_rate:
            lines.append(f"<i>{state.last_rate}</i>")

    return "\n".join(lines)
