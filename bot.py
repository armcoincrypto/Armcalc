#!/usr/bin/env python3
import os
import re
import uuid
import time
import logging

from telegram import (
    Update,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    InlineQueryHandler,
    ContextTypes,
    filters,
)
from telegram.error import Conflict
from asteval import Interpreter
from dotenv import load_dotenv
load_dotenv()

# ———————————————
# Logging
# ———————————————
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ———————————————
# Token & Eval setup
# ———————————————
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_TOKEN is not set in .env")
    exit(1)

aeval = Interpreter()

# ———————————————
# Helper: convert “10%” → “(prev * 10 / 100)”
# ———————————————
def convert_percent(expr: str) -> str:
    tokens = re.findall(r"\d+\.?\d*%|[\d.]+|[+/*()-]", expr)
    output, eval_stack = [], []
    for token in tokens:
        if token.endswith("%"):
            num = float(token[:-1])
            try:
                prev = aeval("".join(eval_stack))
                expr_pct = f"({prev} * {num} / 100)"
                output.append(expr_pct)
                eval_stack = [expr_pct]
            except:
                frac = f"({num} / 100)"
                output.append(frac)
                eval_stack = [frac]
        else:
            output.append(token)
            if token not in "+-*/()":
                eval_stack.append(token)
    return "".join(output)

# ———————————————
# /start handler
# ———————————————
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name or "there"
    logger.info(f"/start from {user}")
    await update.message.reply_text(f"Ողջույն {user}! 🤖")
    await update.message.reply_text(
        "Use me inline by typing @YourBotUsername <expression>"
    )

# ———————————————
# Text handler
# ———————————————
async def handle_math_expression(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    text = update.message.text.strip()
    expr = convert_percent(text)
    logger.info(f"Evaluating: {expr}")
    try:
        result = aeval(expr)
        await update.message.reply_text(f"Արդյունք: {result}")
    except ZeroDivisionError:
        await update.message.reply_text("Սխալ՝ բաժանում զրոյից։")
    except:
        await update.message.reply_text("⚠️ Սխալ արտահայտություն։")

# ———————————————
# Inline query handler
# ———————————————
async def inline_query_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.inline_query.query.strip()
    expr = convert_percent(query)
    logger.info(f"Inline query: {expr}")
    results = []
    if re.fullmatch(r"[0-9+\-*/(). %]+", expr):
        try:
            res = aeval(expr)
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=f"{expr} = {res}",
                    input_message_content=InputTextMessageContent(
                        f"✅ {expr} = {res}"
                    ),
                )
            )
        except:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="⚠️ Սխալ արտահայտություն",
                    input_message_content=InputTextMessageContent("❌ Սխալ"),
                )
            )
    elif query:
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="⚠️ Անվավեր նշաններ",
                input_message_content=InputTextMessageContent(
                    "❌ Մուտքագրեք ճիշտ արտահայտություն։"
                ),
            )
        )
    await update.inline_query.answer(results, cache_time=0)

# ———————————————
# Main
# ———————————————
if __name__ == "__main__":
    # Build application
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_math_expression)
    )
    app.add_handler(InlineQueryHandler(inline_query_handler))

    logger.info("🤖 Bot configured, entering polling loop…")

    # Polling loop with Conflict retry & drop_pending_updates
    while True:
        try:
            app.run_polling(
                drop_pending_updates=True,
                timeout=30,
            )
            break
        except Conflict:
            logger.warning("⚠️ Conflict detected—sleeping 5s then retrying…")
            time.sleep(5)

