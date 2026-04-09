#!/usr/bin/env python3
"""
CLI entry point for the DropAgent Margin Calculator.

Usage:
    python calc.py <buy_price> <sell_price> [--shipping X] [--packaging X] [--model china] [--platform shopify]

Examples:
    python calc.py 25 49.99
    python calc.py 3.50 24.99 --model china
    python calc.py 89 149.99 --shipping 8 --packaging 2
"""

import argparse
import sys

from agent.analyzer import BusinessModel, calculate_margin


def main():
    parser = argparse.ArgumentParser(
        description="DropAgent Margin Calculator — calculate profit for any product"
    )
    parser.add_argument("buy_price", type=float, help="Product purchase price (USD)")
    parser.add_argument("sell_price", type=float, help="Expected selling price (USD)")
    parser.add_argument(
        "--shipping", type=float, default=None, help="Shipping cost (default: auto)"
    )
    parser.add_argument(
        "--packaging", type=float, default=None, help="Packaging cost (default: $1.50)"
    )
    parser.add_argument(
        "--model",
        choices=["us", "china"],
        default="us",
        help="Business model: us (retail arbitrage) or china (dropshipping)",
    )
    parser.add_argument(
        "--platform",
        choices=["ebay", "shopify"],
        default="ebay",
        help="Selling platform (default: ebay)",
    )

    args = parser.parse_args()

    business_model = (
        BusinessModel.CHINA_DROPSHIPPING
        if args.model == "china"
        else BusinessModel.US_ARBITRAGE
    )

    try:
        result = calculate_margin(
            buy_price=args.buy_price,
            sell_price=args.sell_price,
            shipping_cost=args.shipping,
            packaging_cost=args.packaging,
            business_model=business_model,
            platform=args.platform,
        )
        print(result.summary())
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
