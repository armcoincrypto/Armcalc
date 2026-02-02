"""Calculator handlers for direct messages and keyboard."""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from armcalc.services.safe_calc import get_calculator
from armcalc.services.history_store import get_history_store
from armcalc.keyboards.calc_keyboard import (
    get_calc_keyboard,
    CalcKeyboardCallback,
)
from armcalc.utils.logging import get_logger

logger = get_logger("calc")
router = Router(name="calc")

# Store current expression per user for keyboard mode
_user_expressions: dict[int, str] = {}


@router.message(Command("keyboard", "calc", "k"))
async def cmd_keyboard(message: Message) -> None:
    """Show calculator keyboard."""
    user_id = message.from_user.id if message.from_user else 0
    _user_expressions[user_id] = ""
    logger.info(f"/keyboard from user {user_id}")

    await message.answer(
        "🧮 <b>Calculator</b>\n\n"
        "Expression: <code>_</code>\n\n"
        "Tap buttons to build expression:",
        reply_markup=get_calc_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(CalcKeyboardCallback.filter())
async def handle_calc_callback(
    callback: CallbackQuery,
    callback_data: CalcKeyboardCallback,
) -> None:
    """Handle calculator keyboard callbacks."""
    user_id = callback.from_user.id if callback.from_user else 0
    action = callback_data.action
    value = callback_data.value

    logger.debug(f"Calc callback: user={user_id}, action={action}, value={value}")

    # Get current expression
    expr = _user_expressions.get(user_id, "")

    if action == "close":
        await callback.message.delete()
        _user_expressions.pop(user_id, None)
        await callback.answer("Closed")
        return

    if action == "clear":
        expr = ""
        await callback.answer("Cleared")

    elif action == "back":
        expr = expr[:-1] if expr else ""
        await callback.answer("⌫")

    elif action in ("digit", "op", "func"):
        expr += value
        await callback.answer()

    elif action == "eval":
        if expr:
            calc = get_calculator()
            result = calc.calculate(expr)

            if result.success:
                # Save to history
                history = get_history_store()
                history.add_entry(user_id, expr, result.formatted, "calc")
                logger.info(f"Calc keyboard: '{expr}' = {result.formatted}")

                await callback.message.edit_text(
                    f"🧮 <b>Calculator</b>\n\n"
                    f"<code>{expr}</code> = <b>{result.formatted}</b>\n\n"
                    f"Expression: <code>_</code>",
                    reply_markup=get_calc_keyboard(),
                    parse_mode="HTML",
                )
                expr = ""
            else:
                await callback.answer(f"Error: {result.error}", show_alert=True)
        else:
            await callback.answer("Enter an expression first")
        _user_expressions[user_id] = expr
        return

    # Update expression display
    _user_expressions[user_id] = expr
    display_expr = expr if expr else "_"

    try:
        await callback.message.edit_text(
            f"🧮 <b>Calculator</b>\n\n"
            f"Expression: <code>{display_expr}</code>\n\n"
            f"Tap buttons to build expression:",
            reply_markup=get_calc_keyboard(),
            parse_mode="HTML",
        )
    except Exception:
        pass  # Message unchanged


@router.message(Command("history"))
async def cmd_history(message: Message) -> None:
    """Show calculation history."""
    user_id = message.from_user.id if message.from_user else 0
    logger.info(f"/history from user {user_id}")

    history = get_history_store()
    entries = history.get_history(user_id)

    if not entries:
        await message.answer("No history yet. Start calculating!")
        return

    lines = ["📊 <b>Your Last Calculations:</b>\n"]
    for i, entry in enumerate(entries, 1):
        lines.append(f"{i}. <code>{entry.expression}</code> = {entry.result}")
        lines.append(f"   <i>{entry.formatted_time}</i>\n")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("clear_history"))
async def cmd_clear_history(message: Message) -> None:
    """Clear calculation history."""
    user_id = message.from_user.id if message.from_user else 0
    history = get_history_store()

    if history.clear_history(user_id):
        await message.answer("History cleared!")
    else:
        await message.answer("Failed to clear history.")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_math_expression(message: Message) -> None:
    """
    Handle direct math expressions.

    This is the main calculator handler for DM messages.
    """
    if not message.text:
        return

    text = message.text.strip()
    user_id = message.from_user.id if message.from_user else 0

    # Skip if it looks like a command or is too long
    if text.startswith("/") or len(text) > 500:
        return

    # Skip if it doesn't look like a math expression
    # Must contain at least one digit or math constant
    if not any(c.isdigit() for c in text) and "pi" not in text.lower() and "e" not in text.lower():
        return

    calc = get_calculator()
    result = calc.calculate(text)

    logger.info(f"Calc: '{text}' -> {result}")

    if result.success:
        # Save to history
        history = get_history_store()
        history.add_entry(user_id, text, result.formatted, "calc")

        # Armenian-friendly response
        await message.answer(f"Artyunq: {result.formatted}")
    else:
        # Only show error if it looks like they were trying to calculate
        # Check if expression contains math operators
        math_chars = set("+-*/^%().")
        if any(c in math_chars for c in text):
            await message.answer(f"Skhal: {result.error}")
