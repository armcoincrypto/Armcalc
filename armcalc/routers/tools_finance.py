"""Financial tools: loan, days."""

from datetime import datetime
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from armcalc.services.history_store import get_history_store
from armcalc.utils.logging import get_logger

logger = get_logger("tools_finance")
router = Router(name="tools_finance")


def parse_float(value: str) -> float | None:
    """Parse a float from string, handling commas."""
    try:
        return float(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def parse_int(value: str) -> int | None:
    """Parse an integer from string."""
    try:
        return int(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


@router.message(Command("loan"))
async def cmd_loan(message: Message) -> None:
    """
    Calculate loan monthly payment.

    Usage: /loan <amount> <annual_rate_percent> <months>
    Example: /loan 1000000 12 24

    Uses annuity formula:
    M = P * [r(1+r)^n] / [(1+r)^n - 1]
    where:
    - M = monthly payment
    - P = principal (loan amount)
    - r = monthly interest rate
    - n = number of months
    """
    if not message.text:
        return

    parts = message.text.split()

    if len(parts) != 4:
        await message.answer(
            "Usage: `/loan <amount> <annual_rate%> <months>`\n"
            "Example: `/loan 1000000 12 24`\n\n"
            "Calculates monthly payment for a loan.",
            parse_mode="Markdown",
        )
        return

    principal = parse_float(parts[1])
    annual_rate = parse_float(parts[2])
    months = parse_int(parts[3])

    if principal is None or annual_rate is None or months is None:
        await message.answer("Invalid numbers.", parse_mode="Markdown")
        return

    if principal <= 0 or months <= 0:
        await message.answer("Amount and months must be positive.")
        return

    if annual_rate < 0:
        await message.answer("Interest rate cannot be negative.")
        return

    # Calculate monthly payment
    if annual_rate == 0:
        # No interest case
        monthly_payment = principal / months
        total_paid = principal
        total_interest = 0
    else:
        monthly_rate = annual_rate / 100 / 12
        # Annuity formula
        monthly_payment = principal * (
            monthly_rate * (1 + monthly_rate) ** months
        ) / ((1 + monthly_rate) ** months - 1)
        total_paid = monthly_payment * months
        total_interest = total_paid - principal

    result_text = (
        f"🏦 **Loan Calculator**\n\n"
        f"Principal: {principal:,.0f}\n"
        f"Annual Rate: {annual_rate}%\n"
        f"Term: {months} months\n\n"
        f"**Monthly Payment: {monthly_payment:,.2f}**\n"
        f"Total Paid: {total_paid:,.2f}\n"
        f"Total Interest: {total_interest:,.2f}"
    )

    # Save to history
    user_id = message.from_user.id if message.from_user else 0
    history = get_history_store()
    history.add_entry(
        user_id,
        f"loan {principal:,.0f} @ {annual_rate}% x {months}mo",
        f"{monthly_payment:,.2f}/mo",
        "loan",
    )

    await message.answer(result_text, parse_mode="Markdown")


@router.message(Command("days"))
async def cmd_days(message: Message) -> None:
    """
    Calculate days between two dates.

    Usage: /days <date1> <date2>
    Example: /days 2024-01-01 2024-12-31

    Date format: YYYY-MM-DD
    """
    if not message.text:
        return

    parts = message.text.split()

    if len(parts) != 3:
        await message.answer(
            "Usage: `/days <date1> <date2>`\n"
            "Example: `/days 2024-01-01 2024-12-31`\n\n"
            "Date format: YYYY-MM-DD",
            parse_mode="Markdown",
        )
        return

    date_formats = ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%m/%d/%Y"]

    date1 = None
    date2 = None

    for fmt in date_formats:
        try:
            date1 = datetime.strptime(parts[1], fmt)
            break
        except ValueError:
            continue

    for fmt in date_formats:
        try:
            date2 = datetime.strptime(parts[2], fmt)
            break
        except ValueError:
            continue

    if date1 is None or date2 is None:
        await message.answer(
            "Invalid date format.\n"
            "Use: YYYY-MM-DD (e.g., 2024-01-15)",
            parse_mode="Markdown",
        )
        return

    delta = date2 - date1
    days = abs(delta.days)
    weeks = days // 7
    remaining_days = days % 7

    result_text = (
        f"📅 **Days Calculator**\n\n"
        f"From: {date1.strftime('%Y-%m-%d')}\n"
        f"To: {date2.strftime('%Y-%m-%d')}\n\n"
        f"**{days} days**"
    )

    if weeks > 0:
        result_text += f"\n({weeks} weeks"
        if remaining_days > 0:
            result_text += f" and {remaining_days} days"
        result_text += ")"

    # Save to history
    user_id = message.from_user.id if message.from_user else 0
    history = get_history_store()
    history.add_entry(
        user_id,
        f"days {parts[1]} to {parts[2]}",
        f"{days} days",
        "days",
    )

    await message.answer(result_text, parse_mode="Markdown")
