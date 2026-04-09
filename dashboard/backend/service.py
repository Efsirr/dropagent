"""Dashboard-ready service functions built on top of DropAgent core logic."""

from __future__ import annotations

from typing import Optional

from agent.analyzer import BusinessModel, calculate_margin
from db.service import (
    TrackedQueryRecord,
    UserProfile,
    add_tracked_query,
    get_or_create_user_profile,
    list_tracked_queries,
    remove_tracked_query,
    update_digest_schedule,
    update_user_settings,
)
from db.session import get_database_url, get_session
from digest import parse_args, run_digest


def _profile_to_dict(profile: UserProfile) -> dict:
    return {
        "user_id": profile.user_id,
        "telegram_chat_id": profile.telegram_chat_id,
        "username": profile.username,
        "preferred_language": profile.preferred_language,
        "business_model": profile.business_model,
        "min_profit_threshold": profile.min_profit_threshold,
        "max_buy_price": profile.max_buy_price,
        "digest_enabled": profile.digest_enabled,
        "digest_interval_days": profile.digest_interval_days,
        "next_digest_at": (
            profile.next_digest_at.isoformat() if profile.next_digest_at else None
        ),
        "enabled_sources": profile.enabled_sources,
        "tracked_queries": [
            {
                "query": tracked.query,
                "category": tracked.category,
                "max_buy_price": tracked.max_buy_price,
                "min_profit_threshold": tracked.min_profit_threshold,
            }
            for tracked in profile.tracked_queries
        ],
    }


def calculate_margin_payload(
    buy_price: float,
    sell_price: float,
    shipping_cost: Optional[float] = None,
    packaging_cost: Optional[float] = None,
    model: str = "us",
    platform: str = "ebay",
) -> dict:
    """Return margin calculation data for dashboard/API consumers."""
    business_model = (
        BusinessModel.CHINA_DROPSHIPPING
        if model == "china"
        else BusinessModel.US_ARBITRAGE
    )
    result = calculate_margin(
        buy_price=buy_price,
        sell_price=sell_price,
        shipping_cost=shipping_cost,
        packaging_cost=packaging_cost,
        business_model=business_model,
        platform=platform,
    )
    payload = result.to_dict()
    payload["summary"] = result.summary()
    return payload


def get_user_profile_payload(
    telegram_chat_id: str,
    env: Optional[dict] = None,
    username: Optional[str] = None,
    preferred_language: Optional[str] = None,
) -> dict:
    """Return the persisted user profile for dashboard/API consumers."""
    session = get_session(get_database_url(env))
    try:
        profile = get_or_create_user_profile(
            session,
            telegram_chat_id=telegram_chat_id,
            username=username,
            preferred_language=preferred_language,
        )
        return _profile_to_dict(profile)
    finally:
        session.close()


def update_user_settings_payload(
    telegram_chat_id: str,
    env: Optional[dict] = None,
    preferred_language: Optional[str] = None,
    min_profit_threshold: Optional[float] = None,
    max_buy_price=None,
    enabled_sources: Optional[list[str]] = None,
) -> dict:
    """Update persisted settings and return the refreshed user profile."""
    session = get_session(get_database_url(env))
    try:
        profile = update_user_settings(
            session,
            telegram_chat_id=telegram_chat_id,
            preferred_language=preferred_language,
            min_profit_threshold=min_profit_threshold,
            max_buy_price=max_buy_price,
            enabled_sources=enabled_sources,
        )
        return _profile_to_dict(profile)
    finally:
        session.close()


def update_digest_schedule_payload(
    telegram_chat_id: str,
    interval_days: Optional[int],
    enabled: bool = True,
    env: Optional[dict] = None,
) -> dict:
    """Update auto-digest schedule and return refreshed user profile."""
    session = get_session(get_database_url(env))
    try:
        profile = update_digest_schedule(
            session,
            telegram_chat_id=telegram_chat_id,
            interval_days=interval_days,
            enabled=enabled,
        )
        return _profile_to_dict(profile)
    finally:
        session.close()


def list_tracked_queries_payload(
    telegram_chat_id: str,
    env: Optional[dict] = None,
) -> dict:
    """Return all enabled tracked queries for a user."""
    session = get_session(get_database_url(env))
    try:
        tracked = list_tracked_queries(session, telegram_chat_id=telegram_chat_id)
        return {
            "tracked_queries": [
                {
                    "query": item.query,
                    "category": item.category,
                    "max_buy_price": item.max_buy_price,
                    "min_profit_threshold": item.min_profit_threshold,
                }
                for item in tracked
            ]
        }
    finally:
        session.close()


def add_tracked_query_payload(
    telegram_chat_id: str,
    query: str,
    env: Optional[dict] = None,
    category: Optional[str] = None,
    max_buy_price: Optional[float] = None,
    min_profit_threshold: Optional[float] = None,
) -> dict:
    """Add or update a tracked query and return the refreshed user profile."""
    session = get_session(get_database_url(env))
    try:
        profile = add_tracked_query(
            session,
            telegram_chat_id=telegram_chat_id,
            query=query,
            category=category,
            max_buy_price=max_buy_price,
            min_profit_threshold=min_profit_threshold,
        )
        return _profile_to_dict(profile)
    finally:
        session.close()


def remove_tracked_query_payload(
    telegram_chat_id: str,
    query: str,
    env: Optional[dict] = None,
    category: Optional[str] = None,
) -> dict:
    """Remove a tracked query and return the refreshed user profile."""
    session = get_session(get_database_url(env))
    try:
        profile = remove_tracked_query(
            session,
            telegram_chat_id=telegram_chat_id,
            query=query,
            category=category,
        )
        return _profile_to_dict(profile)
    finally:
        session.close()


async def generate_digest_payload(
    queries: list[str],
    env: dict,
    sources: Optional[list[str]] = None,
    top: int = 10,
    min_profit: float = 5.0,
    max_buy_price: Optional[float] = None,
    limit: int = 20,
    title: Optional[str] = None,
) -> dict:
    """Return digest data for dashboard/API consumers."""
    cli_args = []
    for query in queries:
        cli_args.extend(["--query", query])

    for source in sources or []:
        cli_args.extend(["--source", source])

    cli_args.extend(
        ["--top", str(top), "--min-profit", str(min_profit), "--limit", str(limit)]
    )

    if max_buy_price is not None:
        cli_args.extend(["--max-buy-price", str(max_buy_price)])

    if title:
        cli_args.extend(["--title", title])

    args = parse_args(cli_args)
    summary = await run_digest(args, env)
    return {
        "queries": queries,
        "sources": sources or [],
        "summary": summary,
    }


async def generate_saved_digest_payload(
    telegram_chat_id: str,
    env: dict,
    top: int = 10,
    limit: int = 20,
    title: Optional[str] = None,
) -> dict:
    """Generate a digest preview using the user's saved settings and tracked queries."""
    profile = get_user_profile_payload(telegram_chat_id=telegram_chat_id, env=env)
    queries = [item["query"] for item in profile["tracked_queries"]]

    return await generate_digest_payload(
        queries=queries,
        env=env,
        sources=profile["enabled_sources"],
        top=top,
        min_profit=profile["min_profit_threshold"],
        max_buy_price=profile["max_buy_price"],
        limit=limit,
        title=title,
    )
