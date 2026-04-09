"""Dashboard-ready service functions built on top of DropAgent core logic."""

from __future__ import annotations

from typing import Optional

from agent.capabilities import build_capability_statuses, build_next_step
from agent.integrations import (
    BASELINE_REQUIREMENTS,
    INTEGRATION_SPECS,
    env_vars_configured,
)
from agent.analyzer import BusinessModel, calculate_margin
from agent.competitor import CompetitorTracker
from agent.scanner import EbayScanner
from db.service import (
    CompetitorRecord,
    PriceHistoryRecord,
    TrackedQueryRecord,
    UserProfile,
    WatchlistItemRecord,
    add_tracked_competitor,
    add_watchlist_item,
    add_watchlist_price_point,
    add_tracked_query,
    get_or_create_user_profile,
    list_tracked_competitors,
    list_watchlist_history,
    list_watchlist_items,
    list_tracked_queries,
    remove_tracked_competitor,
    remove_watchlist_item,
    remove_tracked_query,
    scan_tracked_competitor,
    update_digest_schedule,
    update_user_settings,
)
from db.session import get_database_url, get_session
from digest import parse_args, run_digest
from weekly_report import parse_args as parse_weekly_args, run_weekly_report


def _build_setup_status(profile: UserProfile, env: Optional[dict] = None) -> dict:
    env = env or {}
    baseline = [
        {
            "env_var": requirement.env_var,
            "label": requirement.label,
            "purpose": requirement.purpose,
            "configured": env_vars_configured(env, (requirement.env_var,)),
        }
        for requirement in BASELINE_REQUIREMENTS
    ]
    integrations = [
        {
            "integration_id": spec.integration_id,
            "label": spec.label,
            "priority": spec.priority,
            "status": spec.status,
            "value": spec.value,
            "recommended_for": spec.recommended_for,
            "configured": env_vars_configured(env, spec.env_vars),
            "selected": spec.integration_id in profile.selected_integrations,
        }
        for spec in INTEGRATION_SPECS
    ]
    baseline_ready = all(item["configured"] for item in baseline)
    return {
        "baseline": baseline,
        "baseline_ready": baseline_ready,
        "integrations": integrations,
    }


def _profile_to_dict(profile: UserProfile, env: Optional[dict] = None) -> dict:
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
        "onboarding_completed": profile.onboarding_completed,
        "enabled_sources": profile.enabled_sources,
        "selected_integrations": profile.selected_integrations,
        "setup_status": _build_setup_status(profile, env=env),
        "capabilities": [item.to_dict() for item in build_capability_statuses(profile)],
        "next_step": build_next_step(profile, lang=profile.preferred_language),
        "tracked_queries": [
            {
                "query": tracked.query,
                "category": tracked.category,
                "max_buy_price": tracked.max_buy_price,
                "min_profit_threshold": tracked.min_profit_threshold,
            }
            for tracked in profile.tracked_queries
        ],
        "watchlist_items": [_watchlist_item_to_dict(item) for item in profile.watchlist_items],
        "tracked_competitors": [_competitor_to_dict(item) for item in profile.tracked_competitors],
    }


def _price_history_record_to_dict(record: PriceHistoryRecord) -> dict:
    return {
        "buy_price": record.buy_price,
        "sell_price": record.sell_price,
        "recorded_at": record.recorded_at.isoformat(),
    }


def _watchlist_item_to_dict(item: WatchlistItemRecord) -> dict:
    return {
        "item_id": item.item_id,
        "product_name": item.product_name,
        "source": item.source,
        "product_url": item.product_url,
        "target_buy_price": item.target_buy_price,
        "target_sell_price": item.target_sell_price,
        "current_buy_price": item.current_buy_price,
        "current_sell_price": item.current_sell_price,
        "notes": item.notes,
        "price_history": [
            _price_history_record_to_dict(entry)
            for entry in item.price_history
        ],
    }


def _competitor_to_dict(item: CompetitorRecord) -> dict:
    return {
        "competitor_id": item.competitor_id,
        "seller_username": item.seller_username,
        "label": item.label,
        "last_scan_at": item.last_scan_at.isoformat() if item.last_scan_at else None,
        "known_item_count": item.known_item_count,
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
        return _profile_to_dict(profile, env=env)
    finally:
        session.close()


def update_user_settings_payload(
    telegram_chat_id: str,
    env: Optional[dict] = None,
    preferred_language: Optional[str] = None,
    business_model: Optional[str] = None,
    min_profit_threshold: Optional[float] = None,
    max_buy_price=None,
    enabled_sources: Optional[list[str]] = None,
    selected_integrations: Optional[list[str]] = None,
    onboarding_completed: Optional[bool] = None,
) -> dict:
    """Update persisted settings and return the refreshed user profile."""
    session = get_session(get_database_url(env))
    try:
        profile = update_user_settings(
            session,
            telegram_chat_id=telegram_chat_id,
            preferred_language=preferred_language,
            business_model=business_model,
            min_profit_threshold=min_profit_threshold,
            max_buy_price=max_buy_price,
            enabled_sources=enabled_sources,
            selected_integrations=selected_integrations,
            onboarding_completed=onboarding_completed,
        )
        return _profile_to_dict(profile, env=env)
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
        return _profile_to_dict(profile, env=env)
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
        return _profile_to_dict(profile, env=env)
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
        return _profile_to_dict(profile, env=env)
    finally:
        session.close()


def list_watchlist_items_payload(
    telegram_chat_id: str,
    env: Optional[dict] = None,
) -> dict:
    """Return watchlist items for a user."""
    session = get_session(get_database_url(env))
    try:
        items = list_watchlist_items(session, telegram_chat_id=telegram_chat_id)
        return {"watchlist_items": [_watchlist_item_to_dict(item) for item in items]}
    finally:
        session.close()


def add_watchlist_item_payload(
    telegram_chat_id: str,
    product_name: str,
    source: str,
    env: Optional[dict] = None,
    product_url: Optional[str] = None,
    target_buy_price: Optional[float] = None,
    target_sell_price: Optional[float] = None,
    current_buy_price: Optional[float] = None,
    current_sell_price: Optional[float] = None,
    notes: Optional[str] = None,
) -> dict:
    """Add a watchlist item and return the created payload."""
    session = get_session(get_database_url(env))
    try:
        item = add_watchlist_item(
            session,
            telegram_chat_id=telegram_chat_id,
            product_name=product_name,
            source=source,
            product_url=product_url,
            target_buy_price=target_buy_price,
            target_sell_price=target_sell_price,
            current_buy_price=current_buy_price,
            current_sell_price=current_sell_price,
            notes=notes,
        )
        return _watchlist_item_to_dict(item)
    finally:
        session.close()


def remove_watchlist_item_payload(
    telegram_chat_id: str,
    item_id: int,
    env: Optional[dict] = None,
) -> dict:
    """Remove a watchlist item and return the remaining list."""
    session = get_session(get_database_url(env))
    try:
        items = remove_watchlist_item(
            session,
            telegram_chat_id=telegram_chat_id,
            item_id=item_id,
        )
        return {"watchlist_items": [_watchlist_item_to_dict(item) for item in items]}
    finally:
        session.close()


def list_watchlist_history_payload(
    telegram_chat_id: str,
    item_id: int,
    env: Optional[dict] = None,
) -> dict:
    """Return history points for a watchlist item."""
    session = get_session(get_database_url(env))
    try:
        history = list_watchlist_history(
            session,
            telegram_chat_id=telegram_chat_id,
            item_id=item_id,
        )
        return {"price_history": [_price_history_record_to_dict(entry) for entry in history]}
    finally:
        session.close()


def add_watchlist_price_point_payload(
    telegram_chat_id: str,
    item_id: int,
    env: Optional[dict] = None,
    buy_price: Optional[float] = None,
    sell_price: Optional[float] = None,
) -> dict:
    """Append a price point for a watchlist item and return the refreshed item."""
    session = get_session(get_database_url(env))
    try:
        item = add_watchlist_price_point(
            session,
            telegram_chat_id=telegram_chat_id,
            item_id=item_id,
            buy_price=buy_price,
            sell_price=sell_price,
        )
        return _watchlist_item_to_dict(item)
    finally:
        session.close()


def list_tracked_competitors_payload(
    telegram_chat_id: str,
    env: Optional[dict] = None,
) -> dict:
    """Return tracked competitors for a user."""
    session = get_session(get_database_url(env))
    try:
        items = list_tracked_competitors(session, telegram_chat_id=telegram_chat_id)
        return {"tracked_competitors": [_competitor_to_dict(item) for item in items]}
    finally:
        session.close()


def add_tracked_competitor_payload(
    telegram_chat_id: str,
    seller_username: str,
    env: Optional[dict] = None,
    label: Optional[str] = None,
) -> dict:
    """Add a competitor seller and return the saved payload."""
    session = get_session(get_database_url(env))
    try:
        item = add_tracked_competitor(
            session,
            telegram_chat_id=telegram_chat_id,
            seller_username=seller_username,
            label=label,
        )
        return _competitor_to_dict(item)
    finally:
        session.close()


def remove_tracked_competitor_payload(
    telegram_chat_id: str,
    competitor_id: int,
    env: Optional[dict] = None,
) -> dict:
    """Remove a competitor seller and return the remaining list."""
    session = get_session(get_database_url(env))
    try:
        items = remove_tracked_competitor(
            session,
            telegram_chat_id=telegram_chat_id,
            competitor_id=competitor_id,
        )
        return {"tracked_competitors": [_competitor_to_dict(item) for item in items]}
    finally:
        session.close()


async def scan_tracked_competitor_payload(
    telegram_chat_id: str,
    competitor_id: int,
    env: dict,
    query: Optional[str] = None,
    limit: int = 25,
) -> dict:
    """Scan a tracked competitor seller and return the latest report."""
    if not env.get("EBAY_APP_ID", "").strip():
        raise ValueError("EBAY_APP_ID is required to scan competitor sellers")

    session = get_session(get_database_url(env))
    scanner = EbayScanner(app_id=env.get("EBAY_APP_ID"))
    tracker = CompetitorTracker(scanner)
    try:
        report = await scan_tracked_competitor(
            session,
            telegram_chat_id=telegram_chat_id,
            competitor_id=competitor_id,
            tracker=tracker,
            query=query,
            limit=limit,
        )
        return report.to_dict() | {"summary": report.summary()}
    finally:
        session.close()
        await scanner.close()


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


async def generate_weekly_report_payload(
    categories: list[str],
    env: dict,
    sources: Optional[list[str]] = None,
    top_products: int = 5,
    trend_limit: int = 5,
    query_limit: int = 10,
    title: Optional[str] = None,
) -> dict:
    """Return weekly category report data for dashboard/API consumers."""
    cli_args = []
    for category in categories:
        cli_args.extend(["--category", category])

    for source in sources or []:
        cli_args.extend(["--source", source])

    cli_args.extend(
        [
            "--top-products",
            str(top_products),
            "--trend-limit",
            str(trend_limit),
            "--query-limit",
            str(query_limit),
        ]
    )

    if title:
        cli_args.extend(["--title", title])

    args = parse_weekly_args(cli_args)
    summary = await run_weekly_report(args, env)
    return {
        "categories": categories,
        "sources": sources or [],
        "summary": summary,
    }
