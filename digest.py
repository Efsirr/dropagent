#!/usr/bin/env python3
"""
CLI entry point for generating the DropAgent daily digest.

Usage:
    python digest.py --query "airpods pro" --query "gaming mouse"
    python digest.py --source walmart --query "lego star wars"
    python digest.py
"""

import argparse
import asyncio
import os
import sys
from typing import Optional

from dotenv import load_dotenv

from agent.comparator import PriceComparator
from agent.scanner import EbayScanner
from agent.scheduler import MorningDigestScheduler, ScanRequest, load_scan_requests_from_env
from agent.sources.amazon import AmazonSource
from agent.sources.base import BaseSource
from agent.sources.walmart import WalmartSource


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments for the daily digest command."""
    parser = argparse.ArgumentParser(
        description="DropAgent Daily Digest — scan marketplaces and rank opportunities"
    )
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        help="Product query to include in the digest. Repeat for multiple queries.",
    )
    parser.add_argument(
        "--source",
        action="append",
        choices=["amazon", "walmart"],
        default=[],
        help="Restrict sources to use. Repeat for multiple sources. Default: auto-detect from env.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Maximum number of opportunities to include (default: 10).",
    )
    parser.add_argument(
        "--min-profit",
        type=float,
        default=5.0,
        help="Minimum net profit required to include an opportunity (default: 5.0).",
    )
    parser.add_argument(
        "--max-buy-price",
        type=float,
        default=None,
        help="Maximum source buy price to consider for all queries.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum products to scan per source and query (default: 20).",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Optional custom report title.",
    )
    return parser.parse_args(argv)


def build_scan_requests(args: argparse.Namespace, env: Optional[dict] = None) -> list[ScanRequest]:
    """Build scan requests from CLI args or DIGEST_QUERIES environment config."""
    env = env or os.environ
    queries = [query.strip() for query in args.query if query.strip()]

    if queries:
        return [
            ScanRequest(
                query=query,
                max_buy_price=args.max_buy_price,
                limit=args.limit,
            )
            for query in queries
        ]

    requests = load_scan_requests_from_env(env)
    if not requests:
        raise ValueError(
            "No digest queries provided. Use --query or set DIGEST_QUERIES in .env"
        )

    for request in requests:
        request.max_buy_price = args.max_buy_price
        request.limit = args.limit
    return requests


def _has_amazon_credentials(env: dict) -> bool:
    return all(
        env.get(key, "").strip()
        for key in ("AMAZON_ACCESS_KEY", "AMAZON_SECRET_KEY", "AMAZON_PARTNER_TAG")
    )


def _has_walmart_credentials(env: dict) -> bool:
    return bool(env.get("WALMART_API_KEY", "").strip())


def build_sources(
    source_names: list[str],
    env: Optional[dict] = None,
) -> list[BaseSource]:
    """Build source clients based on CLI selection or available credentials."""
    env = env or os.environ
    selected = source_names or []
    sources: list[BaseSource] = []

    if selected:
        if "amazon" in selected:
            if not _has_amazon_credentials(env):
                raise ValueError(
                    "Amazon source requested but AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, "
                    "and AMAZON_PARTNER_TAG are not fully configured"
                )
            sources.append(AmazonSource())

        if "walmart" in selected:
            if not _has_walmart_credentials(env):
                raise ValueError(
                    "Walmart source requested but WALMART_API_KEY is not configured"
                )
            sources.append(WalmartSource())
        return sources

    if _has_amazon_credentials(env):
        sources.append(AmazonSource())
    if _has_walmart_credentials(env):
        sources.append(WalmartSource())

    if not sources:
        raise ValueError(
            "No marketplace sources configured. Set Amazon or Walmart credentials in .env"
        )

    return sources


async def run_digest(args: argparse.Namespace, env: Optional[dict] = None) -> str:
    """Generate the morning digest and return formatted output."""
    env = env or os.environ

    if not env.get("EBAY_APP_ID", "").strip():
        raise ValueError("EBAY_APP_ID is required to compare source prices against eBay")

    requests = build_scan_requests(args, env)
    sources = build_sources(args.source, env)
    comparator = PriceComparator(
        sources=sources,
        ebay_scanner=EbayScanner(app_id=env.get("EBAY_APP_ID")),
        min_profit=args.min_profit,
    )
    scheduler = MorningDigestScheduler(
        comparator=comparator,
        top_n=args.top,
        min_profit=args.min_profit,
    )

    try:
        digest = await scheduler.generate_digest(
            requests=requests,
            title=args.title,
        )
        return digest.summary()
    finally:
        await comparator.close()


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point."""
    load_dotenv()
    args = parse_args(argv)

    try:
        output = asyncio.run(run_digest(args))
        print(output)
        return 0
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
