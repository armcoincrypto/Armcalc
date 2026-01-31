"""Calculator inline keyboard."""

from enum import Enum
from typing import Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData


class CalcKeyboardCallback(CallbackData, prefix="calc"):
    """Callback data for calculator keyboard."""

    action: str
    value: str = ""


def get_calc_keyboard() -> InlineKeyboardMarkup:
    """
    Create calculator keyboard.

    Layout:
    [ 7 ] [ 8 ] [ 9 ] [ / ]
    [ 4 ] [ 5 ] [ 6 ] [ * ]
    [ 1 ] [ 2 ] [ 3 ] [ - ]
    [ 0 ] [ . ] [ = ] [ + ]
    [ ( ] [ ) ] [ ^ ] [ % ]
    [ sqrt ] [ sin ] [ cos ] [ C ]
    """
    keyboard = [
        # Row 1: 7 8 9 /
        [
            InlineKeyboardButton(
                text="7", callback_data=CalcKeyboardCallback(action="digit", value="7").pack()
            ),
            InlineKeyboardButton(
                text="8", callback_data=CalcKeyboardCallback(action="digit", value="8").pack()
            ),
            InlineKeyboardButton(
                text="9", callback_data=CalcKeyboardCallback(action="digit", value="9").pack()
            ),
            InlineKeyboardButton(
                text="/", callback_data=CalcKeyboardCallback(action="op", value="/").pack()
            ),
        ],
        # Row 2: 4 5 6 *
        [
            InlineKeyboardButton(
                text="4", callback_data=CalcKeyboardCallback(action="digit", value="4").pack()
            ),
            InlineKeyboardButton(
                text="5", callback_data=CalcKeyboardCallback(action="digit", value="5").pack()
            ),
            InlineKeyboardButton(
                text="6", callback_data=CalcKeyboardCallback(action="digit", value="6").pack()
            ),
            InlineKeyboardButton(
                text="*", callback_data=CalcKeyboardCallback(action="op", value="*").pack()
            ),
        ],
        # Row 3: 1 2 3 -
        [
            InlineKeyboardButton(
                text="1", callback_data=CalcKeyboardCallback(action="digit", value="1").pack()
            ),
            InlineKeyboardButton(
                text="2", callback_data=CalcKeyboardCallback(action="digit", value="2").pack()
            ),
            InlineKeyboardButton(
                text="3", callback_data=CalcKeyboardCallback(action="digit", value="3").pack()
            ),
            InlineKeyboardButton(
                text="-", callback_data=CalcKeyboardCallback(action="op", value="-").pack()
            ),
        ],
        # Row 4: 0 . = +
        [
            InlineKeyboardButton(
                text="0", callback_data=CalcKeyboardCallback(action="digit", value="0").pack()
            ),
            InlineKeyboardButton(
                text=".", callback_data=CalcKeyboardCallback(action="digit", value=".").pack()
            ),
            InlineKeyboardButton(
                text="=", callback_data=CalcKeyboardCallback(action="eval", value="=").pack()
            ),
            InlineKeyboardButton(
                text="+", callback_data=CalcKeyboardCallback(action="op", value="+").pack()
            ),
        ],
        # Row 5: ( ) ^ %
        [
            InlineKeyboardButton(
                text="(", callback_data=CalcKeyboardCallback(action="op", value="(").pack()
            ),
            InlineKeyboardButton(
                text=")", callback_data=CalcKeyboardCallback(action="op", value=")").pack()
            ),
            InlineKeyboardButton(
                text="^", callback_data=CalcKeyboardCallback(action="op", value="^").pack()
            ),
            InlineKeyboardButton(
                text="%", callback_data=CalcKeyboardCallback(action="op", value="%").pack()
            ),
        ],
        # Row 6: sqrt sin cos C
        [
            InlineKeyboardButton(
                text="sqrt", callback_data=CalcKeyboardCallback(action="func", value="sqrt(").pack()
            ),
            InlineKeyboardButton(
                text="sin", callback_data=CalcKeyboardCallback(action="func", value="sin(").pack()
            ),
            InlineKeyboardButton(
                text="cos", callback_data=CalcKeyboardCallback(action="func", value="cos(").pack()
            ),
            InlineKeyboardButton(
                text="C", callback_data=CalcKeyboardCallback(action="clear", value="").pack()
            ),
        ],
        # Row 7: Backspace and close
        [
            InlineKeyboardButton(
                text="<< Back", callback_data=CalcKeyboardCallback(action="back", value="").pack()
            ),
            InlineKeyboardButton(
                text="Close", callback_data=CalcKeyboardCallback(action="close", value="").pack()
            ),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_simple_keyboard() -> InlineKeyboardMarkup:
    """Get a simpler keyboard for quick operations."""
    keyboard = [
        [
            InlineKeyboardButton(
                text="sqrt", callback_data=CalcKeyboardCallback(action="func", value="sqrt(").pack()
            ),
            InlineKeyboardButton(
                text="%", callback_data=CalcKeyboardCallback(action="op", value="%").pack()
            ),
            InlineKeyboardButton(
                text="^", callback_data=CalcKeyboardCallback(action="op", value="^").pack()
            ),
            InlineKeyboardButton(
                text="( )", callback_data=CalcKeyboardCallback(action="op", value="()").pack()
            ),
        ],
        [
            InlineKeyboardButton(
                text="C", callback_data=CalcKeyboardCallback(action="clear", value="").pack()
            ),
            InlineKeyboardButton(
                text="Close", callback_data=CalcKeyboardCallback(action="close", value="").pack()
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
