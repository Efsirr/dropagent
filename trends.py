#!/usr/bin/env python3
"""
CLI entry point for the DropAgent Google Trends scanner.

Usage:
    python trends.py --category electronics
    python trends.py --category electronics --category gaming --merge
"""

import argparse
import sys

from agent.trends import GoogleTrendsScanner, merge_trend_results


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="DropAgent Google Trends scanner — find rising keywords by category"
    )
    parser.add_argument(
        "--category",
        action="append",
        default=[],
        help="Configured category to scan. Repeat for multiple categories.",
    )
    parser.add_argument(
        "--geo",
        default="US",
        help="Google Trends geo code (default: US).",
    )
    parser.add_argument(
        "--timeframe",
        default="now 7-d",
        help="Google Trends timeframe (default: now 7-d).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Max trends per category (default: 10).",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge multiple category scans into one combined ranking.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if not args.category:
        print("Error: at least one --category is required", file=sys.stderr)
        return 1

    scanner = GoogleTrendsScanner()
    try:
        results = scanner.scan_categories(
            categories=args.category,
            geo=args.geo,
            timeframe=args.timeframe,
            limit=args.limit,
        )
        if args.merge:
            print(merge_trend_results(results, limit=args.limit).summary())
        else:
            for index, result in enumerate(results):
                if index:
                    print()
                print(result.summary())
        return 0
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
