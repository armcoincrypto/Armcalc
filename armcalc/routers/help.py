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
• `/convert 1000 amd eur`
• `/convert 50 eur rub`
Supported: USD, EUR, AMD, RUB, GBP, TRY, GEL, AED, etc.
Note: USDT = USD (stablecoin parity)

📐 **Unit Conversion**
• `/unit 10 km miles`
• `/unit 100 kg lbs`
• `/unit 25 c f` (Celsius to Fahrenheit)

Categories: distance (km, m, miles, ft), weight (kg, lbs, oz), temperature (c, f, k), volume (l, gal), speed (kmh, mph)

━━━━━━━━━━━━━━━━━━━━

💵 **Financial Tools**

• `/tip 5000 15` - Calculate 15% tip on 5000
• `/split 15000 4` - Split 15000 among 4 people
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
