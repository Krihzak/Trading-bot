# Binance Futures Testnet Trading Bot

A small Python CLI that places **MARKET**, **LIMIT**, and **STOP_LIMIT** (bonus)
orders on the [Binance USDT-M Futures Testnet](https://testnet.binancefuture.com).
The code is split into a thin client wrapper, an order service, input
validators, and a CLI layer so each piece can be re-used or unit-tested in
isolation.

## Features

- Place `MARKET`, `LIMIT`, and `STOP_LIMIT` orders for `BUY` / `SELL` sides
- CLI input validation (symbol, side, type, quantity, price, stop price, TIF)
- Automatic quantization of price/quantity to the symbol's tick / step size
- Structured request + response logging to `logs/bot.log` (rotating, 1 MB)
- Friendly console output with order request summary and response details
- Clean exception handling for invalid input, API errors, and network failures
- `--dry-run` mode for safe local validation without hitting the API

## Project layout

```
trading_bot/
  bot/
    __init__.py
    client.py          # Binance Futures client wrapper
    orders.py          # Order placement + filter quantization
    validators.py      # Input validation
    logging_config.py  # File + console logging setup
  cli.py               # CLI entry point (argparse)
  logs/                # Created on first run; sample logs included
  requirements.txt
  .env.example
  README.md
```

## Setup

1. **Create a Binance Futures Testnet account** at
   <https://testnet.binancefuture.com/> and generate an API key + secret.
2. **Clone / unzip** this repository and `cd` into `trading_bot/`.
3. **Create a virtual environment** and install dependencies:

   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate

   pip install -r requirements.txt
   ```

4. **Provide your credentials.** Copy `.env.example` to `.env` and fill in:

   ```env
   BINANCE_API_KEY=your_testnet_key_here
   BINANCE_API_SECRET=your_testnet_secret_here
   ```

   Alternatively export them in your shell:

   ```bash
   export BINANCE_API_KEY=...
   export BINANCE_API_SECRET=...
   ```

## Usage

All commands are run from the `trading_bot/` directory.

### Market order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Limit order

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT \
    --quantity 0.01 --price 65000
```

### Stop-Limit order (bonus)

```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT \
    --quantity 0.01 --price 66000 --stop-price 65500
```

### Dry run (no API call)

Use `--dry-run` to validate inputs and print the request summary without
touching the exchange:

```bash
python cli.py --symbol BTCUSDT --side BUY --type LIMIT \
    --quantity 0.01 --price 65000 --dry-run
```

### Verbose logging

Add `-v` / `--verbose` to enable DEBUG-level console logging.

## Output

Successful runs print the order request summary, the exchange response, and
the path to the log file:

```
===== Order Request =====
symbol       : BTCUSDT
side         : BUY
type         : MARKET
quantity     : 0.01

===== Order Response =====
orderId=123456789
clientOrderId=abc...
status=FILLED
executedQty=0.010
avgPrice=64523.10

[OK] Order submitted successfully.

Log file: .../trading_bot/logs/bot.log
```

## Logging

- All requests, responses, and errors are written to `logs/bot.log`.
- The log file rotates at 1 MB with three backups (`bot.log.1` … `bot.log.3`).
- Sample logs from one MARKET and one LIMIT order are included under
  `logs/sample_market.log` and `logs/sample_limit.log`.

## Exit codes

| Code | Meaning                              |
|------|--------------------------------------|
| 0    | Order placed successfully (or dry run)|
| 1    | API / network / client failure       |
| 2    | Invalid CLI input                    |
| 130  | Interrupted (Ctrl-C)                 |

## Assumptions

- The user has an active Binance **Futures** Testnet account (the spot testnet
  account is *not* the same one).
- USDT-M Futures only — coin-margined contracts are out of scope.
- Default `timeInForce` for LIMIT / STOP_LIMIT orders is `GTC`.
- Order prices and quantities are rounded **down** to the nearest tick / step
  to avoid `-1111 Precision` errors. If the rounded value falls below the
  symbol's minimum, the bot raises a clear validation error rather than
  sending a guaranteed-rejection request.
- The bot does not change leverage, margin type, or position mode — those
  must be configured once via the testnet UI.
- Bonus order type implemented: `STOP_LIMIT` (Binance's `STOP` order with a
  limit price + stop price).

## Troubleshooting

- **`API key and secret are required`** — your `.env` file is missing or the
  variables aren't exported. Run with `--dry-run` to confirm validation works
  without credentials.
- **`-2015 Invalid API-key, IP, or permissions`** — regenerate the key on the
  testnet site and make sure "Enable Futures" is checked.
- **`-1121 Symbol ... not found`** — symbol must exist on the Futures testnet
  (e.g. `BTCUSDT`, `ETHUSDT`). Spot-only symbols won't work.
- **`-2019 Margin is insufficient`** — fund your testnet account from the
  faucet on the testnet site.
