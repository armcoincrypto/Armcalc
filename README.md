# Armcalc

A powerful Telegram calculator bot with crypto prices, currency conversion, and more.

## Features

- **Basic Calculator**: `2+2`, `10*5`, `100/4`, `2^8`
- **Percent Operations**: `100+10%` = 110, `200-5%` = 190
- **Scientific Functions**: `sqrt(16)`, `sin(90)`, `cos(0)`, `log(100)`, `ln(e)`
- **Constants**: `pi`, `e`
- **Inline Mode**: Type `@YourBot 2+2` in any chat
- **Crypto Prices**: `/price btc`, `/price eth`
- **Currency Conversion**: `/convert 100 usd amd`
- **Unit Conversion**: `/unit 10 km miles`, `/unit 25 c f`
- **Financial Tools**: `/tip`, `/loan`, `/split`, `/days`
- **History**: `/history` shows your last calculations
- **Calculator Keyboard**: `/keyboard` for button-based input

## Installation

```bash
# Clone the repository
git clone git@github.com:armcoincrypto/Armcalc.git
cd Armcalc

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and add your BOT_TOKEN
```

## Running

```bash
# Activate venv if not already
source venv/bin/activate

# Run the bot
python -m armcalc.main
```

## Testing

```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_safe_calc.py -v

# Syntax check
python -m py_compile armcalc/main.py armcalc/bot.py
```

## Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram Bot Token (required) | - |
| `DRY_RUN` | Mock API calls for testing | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `PRICE_CACHE_TTL_SEC` | Crypto price cache TTL | `60` |
| `FX_CACHE_TTL_SEC` | FX rate cache TTL | `900` |
| `HISTORY_DB_PATH` | SQLite database path | `./data/history.sqlite3` |

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Full help text |
| `/keyboard` | Calculator keyboard |
| `/price <symbol>` | Crypto price (btc, eth, sol, etc.) |
| `/convert <amount> <from> <to>` | Currency conversion |
| `/unit <amount> <from> <to>` | Unit conversion |
| `/tip <amount> <percent>` | Calculate tip |
| `/split <amount> <people>` | Split bill |
| `/loan <amount> <rate> <months>` | Loan calculator |
| `/days <date1> <date2>` | Days between dates |
| `/history` | Your calculation history |
| `/debug` | Bot status info |

## Project Structure

```
armcalc/
├── __init__.py
├── main.py           # Entry point
├── bot.py            # Bot setup
├── config.py         # Configuration
├── routers/          # Command handlers
│   ├── start.py
│   ├── help.py
│   ├── calc.py
│   ├── inline.py
│   ├── tools_finance.py
│   ├── tools_convert.py
│   └── debug.py
├── services/         # Business logic
│   ├── safe_calc.py
│   ├── price_service.py
│   ├── fx_service.py
│   ├── unit_service.py
│   └── history_store.py
├── keyboards/        # Inline keyboards
│   └── calc_keyboard.py
└── utils/           # Utilities
    ├── logging.py
    └── text.py
tests/
├── conftest.py
├── test_safe_calc.py
└── test_unit_service.py
```

## License

MIT

## Made with love for Armcoin
