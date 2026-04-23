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

from agent.adapters.keepa import KeepaAdapter, get_keepa_adapter_for_user
from agent.analyzer import BusinessModel
from agent.comparator import PriceComparator
from agent.integrations import (
    deserialize_integration_credentials,
    integration_credentials_from_env,
)
from agent.scanner import EbayScanner
from agent.scheduler import MorningDigestScheduler, ScanRequest, load_scan_requests_from_env
from agent.sources.aliexpress import AliExpressSource
from agent.sources.amazon import AmazonSource
from agent.sources.base import BaseSource
from agent.sources.cj import CJDropshippingSource
from agent.sources.walmart import WalmartSource
from agent.secrets import open_secret
from db.service import get_user_integration_encrypted_secret
from db.session import get_database_url, get_session


CHINA_SOURCE_NAMES = {"aliexpress", "cj"}


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
        choices=["amazon", "walmart", "aliexpress", "cj"],
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
    return integration_credentials_from_env("amazon", env) is not None


def _has_walmart_credentials(env: dict) -> bool:
    return integration_credentials_from_env("walmart", env) is not None


def _has_aliexpress_credentials(env: dict) -> bool:
    return integration_credentials_from_env("aliexpress", env) is not None


def _has_cj_credentials(env: dict) -> bool:
    return integration_credentials_from_env("cj", env) is not None


def infer_business_model(source_names: list[str]) -> BusinessModel:
    """Infer business model from selected sources."""
    if any(source in CHINA_SOURCE_NAMES for source in source_names):
        return BusinessModel.CHINA_DROPSHIPPING
    return BusinessModel.US_ARBITRAGE


def build_keepa_adapter(
    source_names: list[str],
    env: Optional[dict] = None,
):
    """Build an optional Keepa adapter for Amazon enrichment."""
    env = env or os.environ
    if "amazon" not in source_names:
        return None
    api_key = env.get("KEEPA_API_KEY", "").strip()
    if not api_key:
        return None
    return KeepaAdapter(api_key=api_key)


def _load_user_integration_credentials(
    integration_id: str,
    telegram_chat_id: str,
    env: Optional[dict] = None,
) -> Optional[dict[str, str]]:
    """Load and decrypt saved user credentials for one integration."""
    env = env or os.environ
    app_secret = env.get("APP_SECRET_KEY", "").strip()
    if len(app_secret) < 16:
        return None

    session = get_session(get_database_url(env))
    try:
        encrypted_secret = get_user_integration_encrypted_secret(
            session=session,
            telegram_chat_id=telegram_chat_id,
            integration_id=integration_id,
        )
    finally:
        session.close()

    if not encrypted_secret:
        return None

    try:
        secret_payload = open_secret(encrypted_secret, app_secret=app_secret)
    except Exception:
        return None

    return deserialize_integration_credentials(integration_id, secret_payload)


def _integration_credentials_for_user_or_env(
    integration_id: str,
    env: Optional[dict] = None,
    telegram_chat_id: Optional[str] = None,
) -> Optional[dict[str, str]]:
    """Prefer a user's saved credentials, then fall back to instance env."""
    if telegram_chat_id:
        user_credentials = _load_user_integration_credentials(
            integration_id=integration_id,
            telegram_chat_id=telegram_chat_id,
            env=env,
        )
        if user_credentials:
            return user_credentials
    return integration_credentials_from_env(integration_id, env)


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
        if "aliexpress" in selected:
            if not _has_aliexpress_credentials(env):
                raise ValueError(
                    "AliExpress source requested but ALIEXPRESS_APP_KEY and "
                    "ALIEXPRESS_APP_SECRET are not fully configured"
                )
            sources.append(AliExpressSource())
        if "cj" in selected:
            if not _has_cj_credentials(env):
                raise ValueError("CJ source requested but CJ_API_KEY is not configured")
            sources.append(CJDropshippingSource())
        return sources

    if _has_amazon_credentials(env):
        sources.append(AmazonSource())
    if _has_walmart_credentials(env):
        sources.append(WalmartSource())
    if _has_aliexpress_credentials(env):
        sources.append(AliExpressSource())
    if _has_cj_credentials(env):
        sources.append(CJDropshippingSource())

    if not sources:
        raise ValueError(
            "No marketplace sources configured. Set Amazon, Walmart, AliExpress, or CJ credentials in .env"
        )

    return sources


def build_sources_for_user(
    source_names: list[str],
    env: Optional[dict] = None,
    telegram_chat_id: Optional[str] = None,
) -> list[BaseSource]:
    """Build source clients using per-user credentials with env fallback."""
    env = env or os.environ
    selected = source_names or []
    sources: list[BaseSource] = []

    def resolve_required(source_id: str) -> dict[str, str]:
        credentials = _integration_credentials_for_user_or_env(
            source_id,
            env=env,
            telegram_chat_id=telegram_chat_id,
        )
        if credentials is None:
            if source_id == "amazon":
                raise ValueError(
                    "Amazon source requested but credentials are not configured for this user or instance"
                )
            if source_id == "walmart":
                raise ValueError(
                    "Walmart source requested but credentials are not configured for this user or instance"
                )
            if source_id == "aliexpress":
                raise ValueError(
                    "AliExpress source requested but credentials are not configured for this user or instance"
                )
            if source_id == "cj":
                raise ValueError(
                    "CJ source requested but credentials are not configured for this user or instance"
                )
        return credentials

    if selected:
        if "amazon" in selected:
            credentials = resolve_required("amazon")
            sources.append(
                AmazonSource(
                    access_key=credentials.get("access_key"),
                    secret_key=credentials.get("secret_key"),
                    partner_tag=credentials.get("partner_tag"),
                )
            )
        if "walmart" in selected:
            credentials = resolve_required("walmart")
            sources.append(WalmartSource(api_key=credentials.get("api_key")))
        if "aliexpress" in selected:
            credentials = resolve_required("aliexpress")
            sources.append(
                AliExpressSource(
                    app_key=credentials.get("app_key"),
                    app_secret=credentials.get("app_secret"),
                    tracking_id=credentials.get("tracking_id"),
                )
            )
        if "cj" in selected:
            credentials = resolve_required("cj")
            sources.append(CJDropshippingSource(api_key=credentials.get("api_key")))
        return sources

    amazon_credentials = _integration_credentials_for_user_or_env("amazon", env=env, telegram_chat_id=telegram_chat_id)
    walmart_credentials = _integration_credentials_for_user_or_env("walmart", env=env, telegram_chat_id=telegram_chat_id)
    aliexpress_credentials = _integration_credentials_for_user_or_env("aliexpress", env=env, telegram_chat_id=telegram_chat_id)
    cj_credentials = _integration_credentials_for_user_or_env("cj", env=env, telegram_chat_id=telegram_chat_id)

    if amazon_credentials:
        sources.append(
            AmazonSource(
                access_key=amazon_credentials.get("access_key"),
                secret_key=amazon_credentials.get("secret_key"),
                partner_tag=amazon_credentials.get("partner_tag"),
            )
        )
    if walmart_credentials:
        sources.append(WalmartSource(api_key=walmart_credentials.get("api_key")))
    if aliexpress_credentials:
        sources.append(
            AliExpressSource(
                app_key=aliexpress_credentials.get("app_key"),
                app_secret=aliexpress_credentials.get("app_secret"),
                tracking_id=aliexpress_credentials.get("tracking_id"),
            )
        )
    if cj_credentials:
        sources.append(CJDropshippingSource(api_key=cj_credentials.get("api_key")))

    if not sources:
        raise ValueError(
            "No marketplace sources configured for this user or instance. Connect Amazon, Walmart, AliExpress, or CJ first."
        )

    return sources


def build_keepa_adapter_for_user(
    source_names: list[str],
    env: Optional[dict] = None,
    telegram_chat_id: Optional[str] = None,
):
    """Build an optional Keepa adapter from user-owned creds with env fallback."""
    env = env or os.environ
    if "amazon" not in source_names:
        return None

    if telegram_chat_id:
        session = get_session(get_database_url(env))
        try:
            adapter = get_keepa_adapter_for_user(
                telegram_chat_id=telegram_chat_id,
                session=session,
                app_secret=env.get("APP_SECRET_KEY", ""),
            )
        finally:
            session.close()
        if adapter is not None:
            return adapter

    return build_keepa_adapter(source_names, env)


async def run_digest(
    args: argparse.Namespace,
    env: Optional[dict] = None,
    keepa_adapter=None,
) -> str:
    """Generate the morning digest and return formatted output."""
    env = env or os.environ

    if not env.get("EBAY_APP_ID", "").strip():
        raise ValueError("EBAY_APP_ID is required to compare source prices against eBay")

    requests = build_scan_requests(args, env)
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
        min_profit=args.min_profit,
        keepa_adapter=keepa_adapter
        or build_keepa_adapter_for_user(
            selected_source_names,
            env,
            telegram_chat_id=telegram_chat_id,
        ),
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
