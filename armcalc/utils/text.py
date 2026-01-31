"""Text formatting utilities."""

import re
from typing import Union


def escape_md(text: str) -> str:
    """Escape markdown special characters for Telegram MarkdownV2."""
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", str(text))


def format_number(
    value: Union[int, float],
    decimals: int = 2,
    thousands_sep: str = ",",
    force_decimals: bool = False,
) -> str:
    """Format a number with thousands separator and decimals."""
    if isinstance(value, int) and not force_decimals:
        return f"{value:,}".replace(",", thousands_sep)

    if isinstance(value, float):
        # Check if it's a whole number
        if value == int(value) and not force_decimals:
            return f"{int(value):,}".replace(",", thousands_sep)

        formatted = f"{value:,.{decimals}f}"
        return formatted.replace(",", thousands_sep)

    return str(value)


def format_currency(
    amount: float,
    currency: str,
    decimals: int = 2,
) -> str:
    """Format amount with currency symbol."""
    symbols = {
        "USD": "$",
        "EUR": "\\u20ac",
        "RUB": "\\u20bd",
        "AMD": "\\u058f",
        "GBP": "\\u00a3",
    }
    symbol = symbols.get(currency.upper(), currency.upper() + " ")
    formatted = format_number(amount, decimals=decimals)
    return f"{symbol}{formatted}"


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
