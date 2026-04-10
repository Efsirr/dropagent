"""Dashboard-ready service functions built on top of DropAgent core logic."""

from __future__ import annotations

from typing import Optional

from agent.ad_discovery import build_ad_discovery_report
from agent.adapters.keepa import get_keepa_adapter_for_user
from agent.adapters.pipiads import get_pipiads_adapter_for_user
from agent.adapters.storeleads import get_storeleads_adapter_for_user
from agent.capabilities import build_capability_statuses, build_next_step
from agent.integrations import (
    BASELINE_REQUIREMENTS,
    INTEGRATION_SPECS,
    env_vars_configured,
    get_integration_spec,
)
from agent.secrets import SecretBoxError, mask_secret, seal_secret
from agent.store_discovery import build_store_discovery_report
from agent.trends import GoogleTrendsScanner
from agent.analyzer import BusinessModel, calculate_margin
from agent.competitor import CompetitorTracker
from agent.scanner import EbayScanner
from db.service import (
    AlertEventRecord,
    CompetitorRecord,
    DiscoveryRunRecord,
    PriceHistoryRecord,
    SavedStoreLeadRecord,
    TrackedQueryRecord,
    UserProfile,
    WatchlistItemRecord,
    add_alert_event,
    add_discovery_run,
    get_previous_discovery_run,
    add_saved_store_lead,
    add_tracked_competitor,
    add_watchlist_item,
    add_watchlist_price_point,
    add_tracked_query,
    get_or_create_user_profile,
    list_tracked_competitors,
    list_user_integration_credentials,
    list_watchlist_history,
    list_watchlist_items,
    list_saved_store_leads,
    list_alert_events,
    list_discovery_runs,
    list_tracked_queries,
    delete_user_integration_secret,
    remove_saved_store_lead,
    remove_tracked_competitor,
    remove_watchlist_item,
    remove_tracked_query,
    save_user_integration_secret,
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
        "alert_preferences": profile.alert_preferences,
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
        "saved_store_leads": [_store_lead_to_dict(item) for item in profile.saved_store_leads],
        "discovery_runs": [_discovery_run_to_dict(item) for item in profile.discovery_runs],
        "alert_events": [_alert_event_to_dict(item) for item in profile.alert_events],
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


def _store_lead_to_dict(item: SavedStoreLeadRecord) -> dict:
    return {
        "store_lead_id": item.store_lead_id,
        "domain": item.domain,
        "merchant_name": item.merchant_name,
        "niche_query": item.niche_query,
        "source_integration": item.source_integration,
        "estimated_visits": item.estimated_visits,
        "estimated_sales_monthly_usd": item.estimated_sales_monthly_usd,
        "avg_price_usd": item.avg_price_usd,
        "notes": item.notes,
    }


def _discovery_run_to_dict(item: DiscoveryRunRecord) -> dict:
    return {
        "discovery_run_id": item.discovery_run_id,
        "query": item.query,
        "country": item.country,
        "result_limit": item.result_limit,
        "store_count": item.store_count,
        "ad_count": item.ad_count,
        "trend_count": item.trend_count,
        "summary": item.summary,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def _alert_event_to_dict(item: AlertEventRecord) -> dict:
    return {
        "alert_event_id": item.alert_event_id,
        "alert_type": item.alert_type,
        "title": item.title,
        "message": item.message,
        "severity": item.severity,
        "related_query": item.related_query,
        "metadata": item.metadata,
        "is_read": item.is_read,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def _integration_credential_to_dict(item) -> dict:
    spec = get_integration_spec(item.integration_id)
    return {
        "credential_id": item.credential_id,
        "integration_id": item.integration_id,
        "label": spec.label if spec else item.integration_id,
        "configured": True,
        "secret_hint": item.secret_hint,
        "status": item.status,
        "last_checked_at": item.last_checked_at.isoformat() if item.last_checked_at else None,
    }


def _app_secret(env: Optional[dict]) -> str:
    env = env or {}
    return env.get("APP_SECRET_KEY", "")


def _require_app_secret(env: Optional[dict]) -> str:
    secret = _app_secret(env)
    if len(secret) < 16:
        raise ValueError("APP_SECRET_KEY must be set to save user service keys")
    return secret


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
    alert_preferences: Optional[list[str]] = None,
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
            alert_preferences=alert_preferences,
            onboarding_completed=onboarding_completed,
        )
        return _profile_to_dict(profile, env=env)
    finally:
        session.close()


def list_user_integrations_payload(
    telegram_chat_id: str,
    env: Optional[dict] = None,
) -> dict:
    """Return safe saved-service status for a user."""
    session = get_session(get_database_url(env))
    try:
        credentials = list_user_integration_credentials(session, telegram_chat_id=telegram_chat_id)
        return {"integrations": [_integration_credential_to_dict(item) for item in credentials]}
    finally:
        session.close()


def connect_user_integration_payload(
    telegram_chat_id: str,
    integration_id: str,
    api_key: str,
    env: Optional[dict] = None,
) -> dict:
    """Encrypt and save a user-owned integration API key."""
    spec = get_integration_spec(integration_id)
    if spec is None:
        raise ValueError("unsupported integration")
    app_secret = _require_app_secret(env)
    try:
        encrypted_secret = seal_secret(api_key.strip(), app_secret=app_secret)
    except SecretBoxError as error:
        raise ValueError(str(error)) from error

    session = get_session(get_database_url(env))
    try:
        credential = save_user_integration_secret(
            session,
            telegram_chat_id=telegram_chat_id,
            integration_id=integration_id,
            encrypted_secret=encrypted_secret,
            secret_hint=mask_secret(api_key),
        )
        return _integration_credential_to_dict(credential)
    finally:
        session.close()


def disconnect_user_integration_payload(
    telegram_chat_id: str,
    integration_id: str,
    env: Optional[dict] = None,
) -> dict:
    """Remove a user's saved API key for one integration."""
    session = get_session(get_database_url(env))
    try:
        credentials = delete_user_integration_secret(
            session,
            telegram_chat_id=telegram_chat_id,
            integration_id=integration_id,
        )
        return {"integrations": [_integration_credential_to_dict(item) for item in credentials]}
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


def list_saved_store_leads_payload(
    telegram_chat_id: str,
    env: Optional[dict] = None,
) -> dict:
    """Return saved store leads for a user."""
    session = get_session(get_database_url(env))
    try:
        items = list_saved_store_leads(session, telegram_chat_id=telegram_chat_id)
        return {"saved_store_leads": [_store_lead_to_dict(item) for item in items]}
    finally:
        session.close()


def add_saved_store_lead_payload(
    telegram_chat_id: str,
    domain: str,
    env: Optional[dict] = None,
    merchant_name: Optional[str] = None,
    niche_query: Optional[str] = None,
    source_integration: str = "storeleads",
    estimated_visits: Optional[int] = None,
    estimated_sales_monthly_usd: Optional[float] = None,
    avg_price_usd: Optional[float] = None,
    notes: Optional[str] = None,
) -> dict:
    """Add a saved store lead and return the saved payload."""
    session = get_session(get_database_url(env))
    try:
        item = add_saved_store_lead(
            session,
            telegram_chat_id=telegram_chat_id,
            domain=domain,
            merchant_name=merchant_name,
            niche_query=niche_query,
            source_integration=source_integration,
            estimated_visits=estimated_visits,
            estimated_sales_monthly_usd=estimated_sales_monthly_usd,
            avg_price_usd=avg_price_usd,
            notes=notes,
        )
        return _store_lead_to_dict(item)
    finally:
        session.close()


def remove_saved_store_lead_payload(
    telegram_chat_id: str,
    store_lead_id: int,
    env: Optional[dict] = None,
) -> dict:
    """Remove a saved store lead and return the remaining list."""
    session = get_session(get_database_url(env))
    try:
        items = remove_saved_store_lead(
            session,
            telegram_chat_id=telegram_chat_id,
            store_lead_id=store_lead_id,
        )
        return {"saved_store_leads": [_store_lead_to_dict(item) for item in items]}
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


async def discover_competitor_stores_payload(
    telegram_chat_id: str,
    query: str,
    env: dict,
    country: Optional[str] = None,
    platform: str = "shopify",
    limit: int = 5,
) -> dict:
    """Use StoreLeads to discover competitor stores for a niche/category query."""
    if not query.strip():
        raise ValueError("query is required")

    session = get_session(get_database_url(env))
    adapter = None
    try:
        adapter = get_storeleads_adapter_for_user(
            telegram_chat_id=telegram_chat_id,
            session=session,
            app_secret=_app_secret(env),
        )
        if adapter is None:
            raise ValueError("Connect StoreLeads first to discover competitor stores")

        stores = await adapter.search_domains(
            platform=platform,
            country=country,
            categories=query.strip(),
            page_size=max(1, min(limit, 20)),
        )
        report = build_store_discovery_report(
            query=query.strip(),
            stores=stores[:limit],
            platform=platform,
            country=country,
        )
        return report.to_dict() | {"summary": report.summary()}
    finally:
        session.close()
        if adapter is not None:
            await adapter.close()


async def discover_trending_ads_payload(
    telegram_chat_id: str,
    query: str,
    env: dict,
    country: Optional[str] = None,
    limit: int = 5,
) -> dict:
    """Use PiPiADS to discover trending TikTok ads for a niche/product."""
    if not query.strip():
        raise ValueError("query is required")

    session = get_session(get_database_url(env))
    adapter = None
    try:
        adapter = get_pipiads_adapter_for_user(
            telegram_chat_id=telegram_chat_id,
            session=session,
            app_secret=_app_secret(env),
        )
        if adapter is None:
            raise ValueError("Connect PiPiADS first to discover trending ads")

        result = await adapter.search_ads(
            keyword=query.strip(),
            country=country,
            page_size=max(1, min(limit, 20)),
        )
        report = build_ad_discovery_report(
            query=query.strip(),
            ads=result.ads[:limit],
            country=country,
        )
        return report.to_dict() | {"summary": report.summary()}
    finally:
        session.close()
        if adapter is not None:
            await adapter.close()


async def generate_discovery_hub_payload(
    telegram_chat_id: str,
    query: str,
    env: dict,
    country: Optional[str] = None,
    limit: int = 5,
) -> dict:
    """Run the simple unified discovery flow for dashboard users."""
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("query is required")

    store_report = None
    ad_report = None
    trend_report = None
    errors: dict = {}

    try:
        store_payload = await discover_competitor_stores_payload(
            telegram_chat_id=telegram_chat_id,
            query=normalized_query,
            env=env,
            country=country,
            limit=limit,
        )
        store_report = store_payload
    except ValueError as exc:
        errors["stores"] = str(exc)

    try:
        ad_payload = await discover_trending_ads_payload(
            telegram_chat_id=telegram_chat_id,
            query=normalized_query,
            env=env,
            country=country,
            limit=limit,
        )
        ad_report = ad_payload
    except ValueError as exc:
        errors["ads"] = str(exc)

    try:
        google_scanner = GoogleTrendsScanner()
        google_result = google_scanner.scan_category(
            category=normalized_query,
            keywords=[normalized_query],
            geo=country or "US",
            limit=limit,
        )
        trend_report = google_result
    except Exception as exc:
        errors["trends"] = str(exc)

    payload = {
        "query": normalized_query,
        "store_report": store_report,
        "ad_report": ad_report,
        "trend_report": trend_report.to_dict() if trend_report else None,
        "errors": errors,
    }

    session = get_session(get_database_url(env))
    alert_event = None
    recent_alerts = []
    try:
        previous_run = get_previous_discovery_run(
            session,
            telegram_chat_id=telegram_chat_id,
            query=normalized_query,
        )
        trend_count = len((payload["trend_report"] or {}).get("keywords", []))
        summary_bits = []
        if store_report:
            summary_bits.append(f"{store_report.get('count', 0)} stores")
        if ad_report:
            summary_bits.append(f"{ad_report.get('count', 0)} ads")
        if payload["trend_report"] is not None:
            summary_bits.append(f"{trend_count} trends")
        current_run = add_discovery_run(
            session,
            telegram_chat_id=telegram_chat_id,
            query=normalized_query,
            country=country,
            result_limit=limit,
            store_count=store_report.get("count", 0) if store_report else 0,
            ad_count=ad_report.get("count", 0) if ad_report else 0,
            trend_count=trend_count,
            summary=" · ".join(summary_bits) if summary_bits else None,
        )
        recent_runs = list_discovery_runs(
            session,
            telegram_chat_id=telegram_chat_id,
            limit=8,
        )
        tracked_profile = get_or_create_user_profile(
            session,
            telegram_chat_id=telegram_chat_id,
        )
        normalized_tracked = {item.query.strip().lower() for item in tracked_profile.tracked_queries}
        if previous_run and normalized_query.lower() in normalized_tracked:
            improvements = []
            if current_run.store_count > previous_run.store_count:
                improvements.append(f"stores {previous_run.store_count}->{current_run.store_count}")
            if current_run.ad_count > previous_run.ad_count:
                improvements.append(f"ads {previous_run.ad_count}->{current_run.ad_count}")
            if current_run.trend_count > previous_run.trend_count:
                improvements.append(f"trends {previous_run.trend_count}->{current_run.trend_count}")
            if improvements:
                alert_event = add_alert_event(
                    session,
                    telegram_chat_id=telegram_chat_id,
                    alert_type="discovery_signal_strength",
                    title=f"{normalized_query} is heating up",
                    message=f"Discovery signals improved for {normalized_query}: " + ", ".join(improvements),
                    severity="info",
                    related_query=normalized_query,
                    metadata={
                        "previous": {
                            "store_count": previous_run.store_count,
                            "ad_count": previous_run.ad_count,
                            "trend_count": previous_run.trend_count,
                        },
                        "current": {
                            "store_count": current_run.store_count,
                            "ad_count": current_run.ad_count,
                            "trend_count": current_run.trend_count,
                        },
                    },
                )
        recent_alerts = list_alert_events(
            session,
            telegram_chat_id=telegram_chat_id,
            limit=8,
        )
    finally:
        session.close()

    payload["recent_runs"] = [_discovery_run_to_dict(item) for item in recent_runs]
    payload["recent_alerts"] = [_alert_event_to_dict(item) for item in recent_alerts]
    payload["generated_alert"] = _alert_event_to_dict(alert_event) if alert_event else None
    return payload


async def generate_digest_payload(
    queries: list[str],
    env: dict,
    sources: Optional[list[str]] = None,
    top: int = 10,
    min_profit: float = 5.0,
    max_buy_price: Optional[float] = None,
    limit: int = 20,
    title: Optional[str] = None,
    keepa_adapter=None,
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
    summary = await run_digest(args, env, keepa_adapter=keepa_adapter)
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
    keepa_adapter = None

    if "amazon" in profile["enabled_sources"]:
        session = get_session(get_database_url(env))
        try:
            keepa_adapter = get_keepa_adapter_for_user(
                telegram_chat_id=telegram_chat_id,
                session=session,
                app_secret=_app_secret(env),
            )
        finally:
            session.close()

    return await generate_digest_payload(
        queries=queries,
        env=env,
        sources=profile["enabled_sources"],
        top=top,
        min_profit=profile["min_profit_threshold"],
        max_buy_price=profile["max_buy_price"],
        limit=limit,
        title=title,
        keepa_adapter=keepa_adapter,
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
