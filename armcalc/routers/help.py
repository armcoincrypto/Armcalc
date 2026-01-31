"""Help command handler."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from armcalc.utils.logging import get_logger

logger = get_logger("help")
router = Router(name="help")

HELP_TEXT = """
🧮 **Armcalc - Calculator Bot**

**Basic Math**
Just type any expression:
• `2 + 2` → 4
• `10 * 5` → 50
• `100 / 4` → 25
• `2 ^ 8` → 256 (power)

**Percent Operations**
• `100 + 10%` → 110 (add 10% of 100)
• `200 - 5%` → 190 (subtract 5% of 200)
• `50 * 10%` → 5 (50 times 0.1)
• `10%` → 0.1

**Scientific Functions**
• `sqrt(16)` → 4
• `sin(90)` → 1 (degrees!)
• `cos(0)` → 1
• `tan(45)` → 1
• `log(100)` → 2 (base 10)
• `ln(e)` → 1 (natural log)
• `abs(-5)` → 5
• `round(3.7)` → 4
• `pow(2, 10)` → 1024

**Constants**
• `pi` → 3.14159...
• `e` → 2.71828...

**Inline Mode**
Type `@YourBotName 2+2` in any chat!

━━━━━━━━━━━━━━━━━━━━

💰 **Crypto Prices**
• `/price btc` - Bitcoin price
• `/price eth` - Ethereum price
• `/price sol` - Solana price
Supported: btc, eth, sol, bnb, xrp, ada, doge, ltc, link, etc.

💱 **Currency Conversion**
• `/convert 100 usd amd`
• `/convert 100 usdt amd` ← exchanger rates!
• `/convert 100 amd usdt`
• `/convert 100 usdt sberbank rub`
• `/convert 100 usdt tinkoff rub`

**RUB methods:** sberbank, tinkoff, alfa, vtb
Some pairs (AMD↔USDT, USD↔USDT, RUB) use exchanger XML rates.

📊 **Exchange Rates**
• `/rates` - all available directions
• `/rates usdt` - USDT targets
• `/rates sberbank` - Sberbank rates

━━━━━━━━━━━━━━━━━━━━

💵 **Financial Tools**

• `/loan 1000000 12 24` - Monthly payment for 1M loan at 12% for 24 months
• `/days 2024-01-01 2024-12-31` - Days between dates

━━━━━━━━━━━━━━━━━━━━

📊 **Other Commands**
• `/history` - Your last 10 calculations
• `/keyboard` - Show calculator keyboard
• `/debug` - Bot status info
• `/help` - This help message

━━━━━━━━━━━━━━━━━━━━
Made with ❤️ for Armcoin
"""


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    logger.info(f"/help from user {message.from_user.id if message.from_user else 'unknown'}")
    await message.answer(HELP_TEXT, parse_mode="Markdown")
