"""Command-line interface for the Binance Futures testnet trading bot.

Example::

    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT \
        --quantity 0.01 --price 65000
    python cli.py --symbol BTCUSDT --side BUY --type STOP_LIMIT \
        --quantity 0.01 --price 66000 --stop-price 65500
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from bot.client import APIError, BinanceClientError, BinanceFuturesClient, NetworkError
from bot.logging_config import LOG_FILE, setup_logging
from bot.orders import OrderService
from bot.validators import OrderInput, ValidationError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Place orders on Binance USDT-M Futures Testnet.",
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument(
        "--side", required=True, choices=["BUY", "SELL"], type=str.upper
    )
    parser.add_argument(
        "--type",
        dest="order_type",
        required=True,
        choices=["MARKET", "LIMIT", "STOP_LIMIT"],
        type=lambda v: v.upper().replace("-", "_"),
        help="Order type. STOP_LIMIT is the bonus order type.",
    )
    parser.add_argument("--quantity", required=True, help="Base asset quantity")
    parser.add_argument("--price", help="Limit price (required for LIMIT/STOP_LIMIT)")
    parser.add_argument(
        "--stop-price", dest="stop_price", help="Trigger price (STOP_LIMIT only)"
    )
    parser.add_argument(
        "--time-in-force",
        dest="time_in_force",
        default="GTC",
        choices=["GTC", "IOC", "FOK", "GTX"],
        help="Time in force for LIMIT / STOP_LIMIT orders (default: GTC)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate input and print the request summary without calling the API",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable DEBUG console logging"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    # Load ``.env`` from the project root so the user can keep keys outside the repo.
    load_dotenv(Path(__file__).resolve().parent / ".env")

    parser = build_parser()
    args = parser.parse_args(argv)

    logger = setup_logging(logging.DEBUG if args.verbose else logging.INFO)

    try:
        order = OrderInput.build(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
            time_in_force=args.time_in_force,
        )
    except ValidationError as exc:
        logger.error("Invalid input: %s", exc)
        _print_failure(f"Invalid input: {exc}")
        return 2

    _print_request_summary(order)

    if args.dry_run:
        logger.info("Dry run - skipping API call.")
        print("\nDry run: no order sent.")
        return 0

    try:
        client = BinanceFuturesClient(
            api_key=os.getenv("BINANCE_API_KEY", ""),
            api_secret=os.getenv("BINANCE_API_SECRET", ""),
            testnet=True,
        )
        client.ping()
        service = OrderService(client)
        result = service.place(order)
    except APIError as exc:
        logger.error("Exchange rejected the order: %s", exc)
        _print_failure(f"Exchange error: {exc}")
        return 1
    except NetworkError as exc:
        logger.error("Network failure: %s", exc)
        _print_failure(f"Network error: {exc}")
        return 1
    except BinanceClientError as exc:
        logger.error("Client error: %s", exc)
        _print_failure(str(exc))
        return 1
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130

    _print_success(result)
    print(f"\nLog file: {LOG_FILE}")
    return 0


# --- pretty output helpers -----------------------------------------------


def _print_request_summary(order: OrderInput) -> None:
    lines = [
        "===== Order Request =====",
        f"symbol       : {order.symbol}",
        f"side         : {order.side}",
        f"type         : {order.order_type}",
        f"quantity     : {order.quantity}",
    ]
    if order.price is not None:
        lines.append(f"price        : {order.price}")
    if order.stop_price is not None:
        lines.append(f"stopPrice    : {order.stop_price}")
    if order.order_type in {"LIMIT", "STOP_LIMIT"}:
        lines.append(f"timeInForce  : {order.time_in_force}")
    print("\n".join(lines))


def _print_success(result) -> None:
    print("\n===== Order Response =====")
    print(result.format())
    print("\n[OK] Order submitted successfully.")


def _print_failure(message: str) -> None:
    print("\n===== Order Response =====", file=sys.stderr)
    print(f"[FAIL] {message}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
