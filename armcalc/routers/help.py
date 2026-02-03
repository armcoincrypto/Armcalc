"""Help command handler."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from armcalc.utils.logging import get_logger

logger = get_logger("help")
router = Router(name="help")

HELP_TEXT = """
<b>📚 ARMCALC — FULL GUIDE</b>

━━━━━━━━━━━━━━━━━━━━━━━━
<b>🧮 CALCULATOR</b>
━━━━━━━━━━━━━━━━━━━━━━━━
Just type any math expression:

<b>Basic:</b>
• <code>2+2</code> → 4
• <code>100*5</code> → 500
• <code>50/4</code> → 12.5
• <code>2^10</code> → 1024

<b>Percent:</b>
• <code>100+10%</code> → 110
• <code>200-15%</code> → 170
• <code>500*20%</code> → 100

<b>Functions:</b>
• <code>sqrt(144)</code> → 12
• <code>pow(2,8)</code> → 256
• <code>sin(90)</code> → 1
• <code>cos(0)</code> → 1
• <code>log(100)</code> → 2
• <code>abs(-5)</code> → 5

<b>Constants:</b>
• <code>pi</code> → 3.14159...
• <code>e</code> → 2.71828...

━━━━━━━━━━━━━━━━━━━━━━━━
<b>💱 CURRENCY EXCHANGE</b>
━━━━━━━━━━━━━━━━━━━━━━━━

<b>/convert</b> — Interactive panel
Best for quick conversions with buttons

<b>/convert [amount] [from] [to]</b>
Text-based conversion:
• <code>/convert 100 usdt amd</code>
• <code>/convert 50000 amd usdt</code>
• <code>/convert 100 usdt rub</code>
• <code>/convert 100 usdt sberbank rub</code>

<b>Supported currencies:</b>
• USDT (TRC20, BEP20, ERC20)
• AMD (Cash, Card)
• USD (Cash)
• RUB (Sberbank, Tinkoff, Alfa, VTB)
• KZT, GEL, AED (Card)

<b>Defaults:</b>
USDT=TRC20, AMD=Cash, RUB=Sberbank

━━━━━━━━━━━━━━━━━━━━━━━━
<b>📊 RATES &amp; PAIRS</b>
━━━━━━━━━━━━━━━━━━━━━━━━
<b>/rates</b> — All current rates
<b>/pairs</b> — Overview of options
<b>/pairs usdt</b> — USDT networks
<b>/pairs amd</b> — AMD options
<b>/pairs rub</b> — RUB methods

━━━━━━━━━━━━━━━━━━━━━━━━
<b>💰 CRYPTO PRICES</b>
━━━━━━━━━━━━━━━━━━━━━━━━
<b>/price btc</b> — Bitcoin
<b>/price eth</b> — Ethereum
<b>/price sol</b> — Solana
<b>/price ton</b> — Toncoin
<b>/price xrp</b> — Ripple

━━━━━━━━━━━━━━━━━━━━━━━━
<b>📋 OTHER COMMANDS</b>
━━━━━━━━━━━━━━━━━━━━━━━━
<b>/start</b> — Welcome message
<b>/help</b> — This guide
<b>/keyboard</b> — Calculator buttons
<b>/history</b> — Your recent history
<b>/debug</b> — Bot status

━━━━━━━━━━━━━━━━━━━━━━━━
<b>💡 TIPS</b>
━━━━━━━━━━━━━━━━━━━━━━━━
• Use /convert panel for fastest exchange
• Type numbers to change amount in panel
• All rates from exswaping.com (Yerevan)
"""


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    logger.info(f"/help from user {message.from_user.id if message.from_user else 'unknown'}")
    await message.answer(HELP_TEXT, parse_mode="HTML")
