#!/usr/bin/env python3
"""CLI entry point for the DropAgent weekly category report."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Optional

from dotenv import load_dotenv

from agent.comparator import PriceComparator
from agent.scanner import EbayScanner
from agent.trends import GoogleTrendsScanner
from agent.weekly_report import WeeklyCategoryReporter
from digest import build_sources, build_sources_for_user, infer_business_model


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DropAgent Weekly Category Report — category trends plus profitable products"
    )
    parser.add_argument(
        "--category",
        action="append",
        default=[],
        help="Configured category to include. Repeat for multiple categories.",
    )
    parser.add_argument(
        "--source",
        action="append",
        choices=["amazon", "walmart", "aliexpress", "cj"],
        default=[],
        help="Restrict sources to use. Repeat for multiple sources.",
    )
    parser.add_argument(
        "--top-products",
        type=int,
        default=5,
        help="Max products to show per category (default: 5).",
    )
    parser.add_argument(
        "--trend-limit",
        type=int,
        default=5,
        help="Max trend keywords to use per category (default: 5).",
    )
    parser.add_argument(
        "--query-limit",
        type=int,
        default=10,
        help="Max source results to scan per keyword (default: 10).",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Optional custom report title.",
    )
    return parser.parse_args(argv)


async def run_weekly_report(args: argparse.Namespace, env: Optional[dict] = None) -> str:
    env = env or os.environ
    if not args.category:
        raise ValueError("At least one --category is required")
    if not env.get("EBAY_APP_ID", "").strip():
        raise ValueError("EBAY_APP_ID is required to compare source prices against eBay")

    telegram_chat_id = getattr(args, "telegram_chat_id", None)
    if telegram_chat_id:
        sources = build_sources_for_user(args.source, env, telegram_chat_id=telegram_chat_id)
    else:
        sources = build_sources(args.source, env)
    selected_source_names = args.source or [getattr(source, "name", str(source)) for source in sources]
    business_model = infer_business_model(selected_source_names)
    comparator = PriceComparator(
        sources=sources,
        ebay_scanner=EbayScanner(app_id=env.get("EBAY_APP_ID")),
        business_model=business_model,
    )
    reporter = WeeklyCategoryReporter(
        comparator=comparator,
        google_scanner=GoogleTrendsScanner(),
        reddit_scanner=None,
        top_products=args.top_products,
        trend_limit=args.trend_limit,
        query_limit=args.query_limit,
    )

    try:
        report = await reporter.generate_report(
            categories=args.category,
            title=args.title,
        )
        return report.summary()
    finally:
        await comparator.close()


def main(argv: Optional[list[str]] = None) -> int:
    load_dotenv()
    args = parse_args(argv)
    try:
        output = asyncio.run(run_weekly_report(args))
        print(output)
        return 0
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
