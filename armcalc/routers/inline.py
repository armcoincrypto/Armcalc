"""Inline query handler."""

import uuid
from aiogram import Router
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from armcalc.services.safe_calc import get_calculator
from armcalc.utils.logging import get_logger

logger = get_logger("inline")
router = Router(name="inline")


@router.inline_query()
async def handle_inline_query(inline_query: InlineQuery) -> None:
    """
    Handle inline queries.

    User types: @BotName 2+2
    Bot shows: 2+2 = 4
    """
    query = inline_query.query.strip()
    results = []

    if not query:
        # Show help when empty query
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="Type a math expression",
                description="Example: 2+2, 100+10%, sqrt(16), sin(90)",
                input_message_content=InputTextMessageContent(
                    message_text="Use @ArmcalcBot <expression> to calculate!"
                ),
            )
        )
    else:
        calc = get_calculator()
        result = calc.calculate(query)

        logger.debug(f"Inline query: '{query}' -> {result}")

        if result.success:
            # Success result
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=f"{query} = {result.formatted}",
                    description="Tap to send result",
                    input_message_content=InputTextMessageContent(
                        message_text=f"🧮 {query} = {result.formatted}"
                    ),
                )
            )
            # Also offer just the number
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=f"Just the result: {result.formatted}",
                    description="Send only the number",
                    input_message_content=InputTextMessageContent(
                        message_text=result.formatted
                    ),
                )
            )
        else:
            # Error result
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=f"Error: {result.error}",
                    description=f"Expression: {query}",
                    input_message_content=InputTextMessageContent(
                        message_text=f"❌ Could not calculate: {query}"
                    ),
                )
            )

    await inline_query.answer(results, cache_time=0, is_personal=True)
