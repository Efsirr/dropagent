"""Higher-level database operations for users, settings, and tracked queries."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from agent.competitor import CompetitorReport, CompetitorTracker
from db.models import (
    AlertEvent,
    CompetitorObservation,
    DiscoveryRun,
    PriceHistoryEntry,
    SavedStoreLead,
    TrackedCompetitor,
    TrackedQuery,
    User,
    UserIntegrationCredential,
    UserSettings,
    WatchlistItem,
)


_UNSET = object()
SUPPORTED_SOURCES = {"amazon", "walmart", "aliexpress", "cj"}
SUPPORTED_DIGEST_INTERVALS = {1, 2, 3, 7}
SUPPORTED_ALERT_PREFERENCES = {"discovery", "watchlist", "competitor"}
DEFAULT_ALERT_PREFERENCES = ["discovery", "watchlist", "competitor"]
ALERT_TYPE_TO_PREFERENCE = {
    "discovery_signal_strength": "discovery",
    "watchlist_price_improved": "watchlist",
    "competitor_activity": "competitor",
}


@dataclass
class TrackedQueryRecord:
    """Serializable tracked-query data for bot and dashboard use."""

    query: str
    category: Optional[str] = None
    max_buy_price: Optional[float] = None
    min_profit_threshold: Optional[float] = None


@dataclass
class PriceHistoryRecord:
    """Serializable price-history entry for a watchlist item."""

    buy_price: Optional[float]
    sell_price: Optional[float]
    recorded_at: datetime


@dataclass
class WatchlistItemRecord:
    """Serializable watchlist item data for bot and dashboard use."""

    item_id: int
    product_name: str
    source: str
    product_url: Optional[str] = None
    target_buy_price: Optional[float] = None
    target_sell_price: Optional[float] = None
    current_buy_price: Optional[float] = None
    current_sell_price: Optional[float] = None
    notes: Optional[str] = None
    price_history: list[PriceHistoryRecord] = field(default_factory=list)


@dataclass
class CompetitorRecord:
    """Serializable tracked-competitor data."""

    competitor_id: int
    seller_username: str
    label: Optional[str] = None
    last_scan_at: Optional[datetime] = None
    known_item_count: int = 0


@dataclass
class SavedStoreLeadRecord:
    """Serializable saved store-lead data for dashboard workflows."""

    store_lead_id: int
    domain: str
    merchant_name: Optional[str] = None
    niche_query: Optional[str] = None
    source_integration: str = "storeleads"
    estimated_visits: Optional[int] = None
    estimated_sales_monthly_usd: Optional[float] = None
    avg_price_usd: Optional[float] = None
    notes: Optional[str] = None


@dataclass
class DiscoveryRunRecord:
    """Serializable discovery history entry for dashboard use."""

    discovery_run_id: int
    query: str
    country: Optional[str] = None
    result_limit: int = 5
    store_count: int = 0
    ad_count: int = 0
    trend_count: int = 0
    summary: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class AlertEventRecord:
    """Serializable user alert event."""

    alert_event_id: int
    alert_type: str
    title: str
    message: str
    severity: str = "info"
    related_query: Optional[str] = None
    metadata: Optional[dict] = None
    is_read: bool = False
    created_at: Optional[datetime] = None


@dataclass
class UserIntegrationCredentialRecord:
    """Safe integration credential metadata. Never includes the raw or encrypted key."""

    credential_id: int
    integration_id: str
    secret_hint: str
    status: str
    last_checked_at: Optional[datetime] = None


@dataclass
class UserProfile:
    """Combined user state for bot interactions."""

    user_id: int
    telegram_chat_id: str
    username: Optional[str]
    preferred_language: str
    business_model: str
    min_profit_threshold: float
    max_buy_price: Optional[float]
    digest_enabled: bool
    digest_interval_days: int
    next_digest_at: Optional[datetime]
    onboarding_completed: bool = False
    enabled_sources: list[str] = field(default_factory=list)
    selected_integrations: list[str] = field(default_factory=list)
    connected_integrations: list[str] = field(default_factory=list)
    alert_preferences: list[str] = field(default_factory=list)
    tracked_queries: list[TrackedQueryRecord] = field(default_factory=list)
    watchlist_items: list[WatchlistItemRecord] = field(default_factory=list)
    tracked_competitors: list[CompetitorRecord] = field(default_factory=list)
    saved_store_leads: list[SavedStoreLeadRecord] = field(default_factory=list)
    discovery_runs: list[DiscoveryRunRecord] = field(default_factory=list)
    alert_events: list[AlertEventRecord] = field(default_factory=list)


def compute_next_digest_at(
    interval_days: int,
    alert_hour_utc: int,
    now: Optional[datetime] = None,
    base_time: Optional[datetime] = None,
) -> datetime:
    """Compute the next digest time based on interval and UTC hour."""
    now = now or datetime.now(timezone.utc)
    anchor = base_time or now
    candidate = anchor.astimezone(timezone.utc).replace(
        hour=alert_hour_utc,
        minute=0,
        second=0,
        microsecond=0,
    )
    if candidate <= now:
        candidate += timedelta(days=interval_days)
    return candidate


def _schedule_label(interval_days: int, enabled: bool) -> str:
    if not enabled:
        return "off"
    if interval_days == 7:
        return "weekly"
    return f"every {interval_days} day(s)"


def _normalize_sources(enabled_sources: Optional[str]) -> list[str]:
    if not enabled_sources:
        return []
    return [source.strip() for source in enabled_sources.split(",") if source.strip()]


def _serialize_sources(enabled_sources: list[str]) -> str:
    return ",".join(enabled_sources)


def _normalize_integration_ids(value: Optional[str]) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _serialize_integration_ids(values: list[str]) -> str:
    return ",".join(values)


def _normalize_alert_preferences(value: Optional[str]) -> list[str]:
    if not value:
        return DEFAULT_ALERT_PREFERENCES.copy()
    normalized = []
    for item in value.split(","):
        item = item.strip()
        if item in SUPPORTED_ALERT_PREFERENCES and item not in normalized:
            normalized.append(item)
    return normalized or DEFAULT_ALERT_PREFERENCES.copy()


def _serialize_alert_preferences(values: list[str]) -> str:
    normalized = [item for item in values if item in SUPPORTED_ALERT_PREFERENCES]
    deduped = list(dict.fromkeys(normalized))
    return ",".join(deduped or DEFAULT_ALERT_PREFERENCES)


def _normalize_datetime(value: Optional[datetime]) -> Optional[datetime]:
    """Normalize DB datetimes to UTC-aware values."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _user_query():
    return (
        select(User)
        .options(
            selectinload(User.settings),
            selectinload(User.tracked_queries),
            selectinload(User.watchlist_items).selectinload(WatchlistItem.price_history),
            selectinload(User.tracked_competitors).selectinload(TrackedCompetitor.observations),
            selectinload(User.saved_store_leads),
            selectinload(User.discovery_runs),
            selectinload(User.alert_events),
            selectinload(User.integration_credentials),
        )
    )


def get_or_create_user(
    session: Session,
    telegram_chat_id: str,
    username: Optional[str] = None,
    preferred_language: Optional[str] = None,
) -> User:
    """Load a user by Telegram chat ID or create a new one with default settings."""
    user = session.scalar(
        _user_query().where(User.telegram_chat_id == str(telegram_chat_id))
    )

    if user is None:
        user = User(
            telegram_chat_id=str(telegram_chat_id),
            username=username,
        )
        user.settings = UserSettings(
            preferred_language=preferred_language or "en",
            next_digest_at=compute_next_digest_at(interval_days=1, alert_hour_utc=8),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return session.scalar(
            _user_query().where(User.id == user.id)
        )

    if username and user.username != username:
        user.username = username
    if preferred_language and user.settings and not user.settings.preferred_language:
        user.settings.preferred_language = preferred_language
    session.commit()
    return session.scalar(
        _user_query().where(User.id == user.id)
    )


def build_user_profile(user: User) -> UserProfile:
    """Convert ORM user object into transport-friendly profile data."""
    settings = user.settings or UserSettings()
    tracked_queries = [
        TrackedQueryRecord(
            query=tracked.query,
            category=tracked.category,
            max_buy_price=tracked.max_buy_price,
            min_profit_threshold=tracked.min_profit_threshold,
        )
        for tracked in user.tracked_queries
        if tracked.is_enabled
    ]
    watchlist_items = [
        WatchlistItemRecord(
            item_id=item.id,
            product_name=item.product_name,
            source=item.source,
            product_url=item.product_url,
            target_buy_price=item.target_buy_price,
            target_sell_price=item.target_sell_price,
            current_buy_price=item.current_buy_price,
            current_sell_price=item.current_sell_price,
            notes=item.notes,
            price_history=[
                PriceHistoryRecord(
                    buy_price=entry.buy_price,
                    sell_price=entry.sell_price,
                    recorded_at=_normalize_datetime(entry.recorded_at) or entry.recorded_at,
                )
                for entry in item.price_history
            ],
        )
        for item in user.watchlist_items
        if item.is_enabled
    ]
    tracked_competitors = [
        CompetitorRecord(
            competitor_id=item.id,
            seller_username=item.seller_username,
            label=item.label,
            last_scan_at=_normalize_datetime(item.last_scan_at),
            known_item_count=len(item.observations),
        )
        for item in user.tracked_competitors
        if item.is_enabled
    ]
    saved_store_leads = [
        SavedStoreLeadRecord(
            store_lead_id=item.id,
            domain=item.domain,
            merchant_name=item.merchant_name,
            niche_query=item.niche_query,
            source_integration=item.source_integration,
            estimated_visits=item.estimated_visits,
            estimated_sales_monthly_usd=item.estimated_sales_monthly_usd,
            avg_price_usd=item.avg_price_usd,
            notes=item.notes,
        )
        for item in user.saved_store_leads
        if item.is_enabled
    ]
    discovery_runs = [
        DiscoveryRunRecord(
            discovery_run_id=item.id,
            query=item.query,
            country=item.country,
            result_limit=item.result_limit,
            store_count=item.store_count,
            ad_count=item.ad_count,
            trend_count=item.trend_count,
            summary=item.summary,
            created_at=_normalize_datetime(item.created_at),
        )
        for item in sorted(
            user.discovery_runs,
            key=lambda record: record.created_at or datetime.min,
            reverse=True,
        )[:8]
    ]
    alert_events = [
        AlertEventRecord(
            alert_event_id=item.id,
            alert_type=item.alert_type,
            title=item.title,
            message=item.message,
            severity=item.severity,
            related_query=item.related_query,
            metadata=json.loads(item.metadata_json) if item.metadata_json else None,
            is_read=item.is_read,
            created_at=_normalize_datetime(item.created_at),
        )
        for item in sorted(
            user.alert_events,
            key=lambda record: record.created_at or datetime.min,
            reverse=True,
        )[:8]
    ]
    return UserProfile(
        user_id=user.id,
        telegram_chat_id=user.telegram_chat_id or "",
        username=user.username,
        preferred_language=settings.preferred_language,
        business_model=settings.business_model,
        min_profit_threshold=settings.min_profit_threshold,
        max_buy_price=settings.max_buy_price,
        digest_enabled=settings.digest_enabled,
        digest_interval_days=settings.digest_interval_days,
        next_digest_at=_normalize_datetime(settings.next_digest_at),
        onboarding_completed=settings.onboarding_completed,
        enabled_sources=_normalize_sources(settings.enabled_sources),
        selected_integrations=_normalize_integration_ids(settings.selected_integrations),
        connected_integrations=[
            credential.integration_id
            for credential in user.integration_credentials
        ],
        alert_preferences=_normalize_alert_preferences(settings.alert_preferences),
        tracked_queries=tracked_queries,
        watchlist_items=watchlist_items,
        tracked_competitors=tracked_competitors,
        saved_store_leads=saved_store_leads,
        discovery_runs=discovery_runs,
        alert_events=alert_events,
    )


def get_or_create_user_profile(
    session: Session,
    telegram_chat_id: str,
    username: Optional[str] = None,
    preferred_language: Optional[str] = None,
) -> UserProfile:
    """Get a user profile for the current Telegram user, creating it if needed."""
    user = get_or_create_user(
        session=session,
        telegram_chat_id=telegram_chat_id,
        username=username,
        preferred_language=preferred_language,
    )
    return build_user_profile(user)


def update_user_settings(
    session: Session,
    telegram_chat_id: str,
    preferred_language: Optional[str] = None,
    business_model: Optional[str] = None,
    min_profit_threshold: Optional[float] = None,
    max_buy_price=_UNSET,
    enabled_sources: Optional[list[str]] = None,
    selected_integrations: Optional[list[str]] = None,
    alert_preferences: Optional[list[str]] = None,
    onboarding_completed: Optional[bool] = None,
    digest_enabled: Optional[bool] = None,
    digest_interval_days: Optional[int] = None,
    next_digest_at=_UNSET,
    now: Optional[datetime] = None,
) -> UserProfile:
    """Update persisted user settings and return the refreshed profile."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    settings = user.settings
    if settings is None:
        settings = UserSettings(user_id=user.id)
        user.settings = settings

    if preferred_language is not None:
        settings.preferred_language = preferred_language
    if business_model is not None:
        settings.business_model = business_model
    if min_profit_threshold is not None:
        settings.min_profit_threshold = min_profit_threshold
    if max_buy_price is not _UNSET:
        settings.max_buy_price = max_buy_price
    if enabled_sources is not None:
        settings.enabled_sources = _serialize_sources(enabled_sources)
    if selected_integrations is not None:
        settings.selected_integrations = _serialize_integration_ids(selected_integrations)
    if alert_preferences is not None:
        settings.alert_preferences = _serialize_alert_preferences(alert_preferences)
    if onboarding_completed is not None:
        settings.onboarding_completed = onboarding_completed
    if digest_enabled is not None:
        settings.digest_enabled = digest_enabled
    if digest_interval_days is not None:
        settings.digest_interval_days = digest_interval_days
    if next_digest_at is not _UNSET:
        settings.next_digest_at = next_digest_at

    if digest_enabled is True and next_digest_at is _UNSET:
        settings.next_digest_at = compute_next_digest_at(
            interval_days=settings.digest_interval_days,
            alert_hour_utc=settings.alert_hour_utc,
            now=now,
        )
    if digest_enabled is False:
        settings.next_digest_at = None

    session.add(user)
    session.commit()
    refreshed = session.scalar(_user_query().where(User.id == user.id))
    return build_user_profile(refreshed)


def update_digest_schedule(
    session: Session,
    telegram_chat_id: str,
    interval_days: Optional[int],
    enabled: bool = True,
    now: Optional[datetime] = None,
) -> UserProfile:
    """Persist a digest schedule selection for a user."""
    if enabled:
        if interval_days not in SUPPORTED_DIGEST_INTERVALS:
            raise ValueError("Unsupported digest interval")
        next_digest_at = _UNSET
    else:
        interval_days = interval_days or 1
        next_digest_at = None

    return update_user_settings(
        session,
        telegram_chat_id=telegram_chat_id,
        digest_enabled=enabled,
        digest_interval_days=interval_days,
        next_digest_at=next_digest_at,
        now=now,
    )


def _credential_record(credential: UserIntegrationCredential) -> UserIntegrationCredentialRecord:
    return UserIntegrationCredentialRecord(
        credential_id=credential.id,
        integration_id=credential.integration_id,
        secret_hint=credential.secret_hint,
        status=credential.status,
        last_checked_at=_normalize_datetime(credential.last_checked_at),
    )


def save_user_integration_secret(
    session: Session,
    telegram_chat_id: str,
    integration_id: str,
    encrypted_secret: str,
    secret_hint: str,
    status: str = "connected",
    checked_at: Optional[datetime] = None,
) -> UserIntegrationCredentialRecord:
    """Create or update encrypted credential metadata for a user's service."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    credential = session.scalar(
        select(UserIntegrationCredential).where(
            UserIntegrationCredential.user_id == user.id,
            UserIntegrationCredential.integration_id == integration_id,
        )
    )
    if credential is None:
        credential = UserIntegrationCredential(
            user_id=user.id,
            integration_id=integration_id,
            encrypted_secret=encrypted_secret,
            secret_hint=secret_hint,
            status=status,
            last_checked_at=checked_at,
        )
        session.add(credential)
    else:
        credential.encrypted_secret = encrypted_secret
        credential.secret_hint = secret_hint
        credential.status = status
        if checked_at is not None:
            credential.last_checked_at = checked_at

    session.commit()
    session.refresh(credential)
    return _credential_record(credential)


def list_user_integration_credentials(
    session: Session,
    telegram_chat_id: str,
) -> list[UserIntegrationCredentialRecord]:
    """List safe metadata for all connected services owned by the user."""
    user = session.scalar(
        _user_query().where(User.telegram_chat_id == str(telegram_chat_id))
    )
    if user is None:
        return []
    credentials = session.scalars(
        select(UserIntegrationCredential)
        .where(UserIntegrationCredential.user_id == user.id)
        .order_by(UserIntegrationCredential.integration_id)
    ).all()
    return [_credential_record(credential) for credential in credentials]


def get_user_integration_encrypted_secret(
    session: Session,
    telegram_chat_id: str,
    integration_id: str,
) -> Optional[str]:
    """Return the encrypted secret for internal connector use only."""
    user = session.scalar(
        select(User).where(User.telegram_chat_id == str(telegram_chat_id))
    )
    if user is None:
        return None
    credential = session.scalar(
        select(UserIntegrationCredential).where(
            UserIntegrationCredential.user_id == user.id,
            UserIntegrationCredential.integration_id == integration_id,
        )
    )
    return credential.encrypted_secret if credential else None


def delete_user_integration_secret(
    session: Session,
    telegram_chat_id: str,
    integration_id: str,
) -> list[UserIntegrationCredentialRecord]:
    """Disconnect a user's service secret and return remaining safe metadata."""
    user = session.scalar(
        select(User).where(User.telegram_chat_id == str(telegram_chat_id))
    )
    if user is None:
        return []
    credential = session.scalar(
        select(UserIntegrationCredential).where(
            UserIntegrationCredential.user_id == user.id,
            UserIntegrationCredential.integration_id == integration_id,
        )
    )
    if credential is not None:
        session.delete(credential)
        session.commit()
    return list_user_integration_credentials(session, telegram_chat_id)


def mark_user_integration_checked(
    session: Session,
    telegram_chat_id: str,
    integration_id: str,
    status: str,
    checked_at: Optional[datetime] = None,
) -> Optional[UserIntegrationCredentialRecord]:
    """Update a saved service status after a health/check call."""
    user = session.scalar(
        select(User).where(User.telegram_chat_id == str(telegram_chat_id))
    )
    if user is None:
        return None
    credential = session.scalar(
        select(UserIntegrationCredential).where(
            UserIntegrationCredential.user_id == user.id,
            UserIntegrationCredential.integration_id == integration_id,
        )
    )
    if credential is None:
        return None
    credential.status = status
    credential.last_checked_at = checked_at or datetime.now(timezone.utc)
    session.commit()
    session.refresh(credential)
    return _credential_record(credential)


def add_tracked_query(
    session: Session,
    telegram_chat_id: str,
    query: str,
    category: Optional[str] = None,
    max_buy_price: Optional[float] = None,
    min_profit_threshold: Optional[float] = None,
) -> UserProfile:
    """Create or update a tracked query for a Telegram user."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    existing = session.scalar(
        select(TrackedQuery).where(
            TrackedQuery.user_id == user.id,
            TrackedQuery.query == query,
            TrackedQuery.category == category,
        )
    )

    if existing is None:
        existing = TrackedQuery(
            user_id=user.id,
            query=query,
            category=category,
        )
        session.add(existing)

    existing.is_enabled = True
    existing.max_buy_price = max_buy_price
    existing.min_profit_threshold = min_profit_threshold
    session.commit()

    refreshed = session.scalar(_user_query().where(User.id == user.id))
    return build_user_profile(refreshed)


def list_tracked_queries(
    session: Session,
    telegram_chat_id: str,
    enabled_only: bool = True,
) -> list[TrackedQueryRecord]:
    """List tracked queries for a Telegram user."""
    user = session.scalar(
        _user_query().where(User.telegram_chat_id == str(telegram_chat_id))
    )
    if user is None:
        return []

    records = []
    for tracked in user.tracked_queries:
        if enabled_only and not tracked.is_enabled:
            continue
        records.append(
            TrackedQueryRecord(
                query=tracked.query,
                category=tracked.category,
                max_buy_price=tracked.max_buy_price,
                min_profit_threshold=tracked.min_profit_threshold,
            )
        )
    return records


def remove_tracked_query(
    session: Session,
    telegram_chat_id: str,
    query: str,
    category: Optional[str] = None,
) -> UserProfile:
    """Disable a tracked query for a Telegram user."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    existing = session.scalar(
        select(TrackedQuery).where(
            TrackedQuery.user_id == user.id,
            TrackedQuery.query == query,
            TrackedQuery.category == category,
            TrackedQuery.is_enabled.is_(True),
        )
    )
    if existing is None:
        raise ValueError("Tracked query not found")

    existing.is_enabled = False
    session.commit()

    refreshed = session.scalar(_user_query().where(User.id == user.id))
    return build_user_profile(refreshed)


def list_due_digest_profiles(
    session: Session,
    now: Optional[datetime] = None,
) -> list[UserProfile]:
    """Return users whose scheduled digest is due now."""
    now = now or datetime.now(timezone.utc)
    users = session.scalars(
        _user_query()
        .join(User.settings)
        .where(UserSettings.digest_enabled.is_(True))
        .where(UserSettings.next_digest_at.is_not(None))
        .where(UserSettings.next_digest_at <= now)
    ).all()
    return [build_user_profile(user) for user in users]


def mark_digest_sent(
    session: Session,
    telegram_chat_id: str,
    sent_at: Optional[datetime] = None,
) -> UserProfile:
    """Advance the next digest time after a successful send."""
    sent_at = sent_at or datetime.now(timezone.utc)
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    settings = user.settings
    if settings is None:
        raise ValueError("User settings not found")

    settings.next_digest_at = compute_next_digest_at(
        interval_days=settings.digest_interval_days,
        alert_hour_utc=settings.alert_hour_utc,
        now=sent_at,
        base_time=sent_at,
    )
    session.commit()
    refreshed = session.scalar(_user_query().where(User.id == user.id))
    return build_user_profile(refreshed)


def _watchlist_query():
    return (
        select(WatchlistItem)
        .options(selectinload(WatchlistItem.price_history))
        .order_by(WatchlistItem.created_at.desc(), WatchlistItem.id.desc())
    )


def _serialize_watchlist_item(item: WatchlistItem) -> WatchlistItemRecord:
    return WatchlistItemRecord(
        item_id=item.id,
        product_name=item.product_name,
        source=item.source,
        product_url=item.product_url,
        target_buy_price=item.target_buy_price,
        target_sell_price=item.target_sell_price,
        current_buy_price=item.current_buy_price,
        current_sell_price=item.current_sell_price,
        notes=item.notes,
        price_history=[
            PriceHistoryRecord(
                buy_price=entry.buy_price,
                sell_price=entry.sell_price,
                recorded_at=_normalize_datetime(entry.recorded_at) or entry.recorded_at,
            )
            for entry in item.price_history
        ],
    )


def add_watchlist_item(
    session: Session,
    telegram_chat_id: str,
    product_name: str,
    source: str,
    product_url: Optional[str] = None,
    target_buy_price: Optional[float] = None,
    target_sell_price: Optional[float] = None,
    current_buy_price: Optional[float] = None,
    current_sell_price: Optional[float] = None,
    notes: Optional[str] = None,
    record_history: bool = True,
    recorded_at: Optional[datetime] = None,
) -> WatchlistItemRecord:
    """Create a new watchlist item and optionally save an initial price point."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    watchlist_item = WatchlistItem(
        user_id=user.id,
        product_name=product_name,
        source=source.lower(),
        product_url=product_url,
        target_buy_price=target_buy_price,
        target_sell_price=target_sell_price,
        current_buy_price=current_buy_price,
        current_sell_price=current_sell_price,
        notes=notes,
        is_enabled=True,
    )
    session.add(watchlist_item)
    session.flush()

    if record_history and (current_buy_price is not None or current_sell_price is not None):
        session.add(
            PriceHistoryEntry(
                watchlist_item_id=watchlist_item.id,
                buy_price=current_buy_price,
                sell_price=current_sell_price,
                recorded_at=recorded_at or datetime.now(timezone.utc),
            )
        )

    session.commit()
    saved = session.scalar(_watchlist_query().where(WatchlistItem.id == watchlist_item.id))
    return _serialize_watchlist_item(saved)


def list_watchlist_items(
    session: Session,
    telegram_chat_id: str,
) -> list[WatchlistItemRecord]:
    """List enabled watchlist items for a Telegram user."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    items = session.scalars(
        _watchlist_query().where(
            WatchlistItem.user_id == user.id,
            WatchlistItem.is_enabled.is_(True),
        )
    ).all()
    return [_serialize_watchlist_item(item) for item in items]


def add_watchlist_price_point(
    session: Session,
    telegram_chat_id: str,
    item_id: int,
    buy_price: Optional[float] = None,
    sell_price: Optional[float] = None,
    recorded_at: Optional[datetime] = None,
) -> WatchlistItemRecord:
    """Append a new price-history point and refresh current watchlist prices."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    item = session.scalar(
        _watchlist_query().where(
            WatchlistItem.id == item_id,
            WatchlistItem.user_id == user.id,
            WatchlistItem.is_enabled.is_(True),
        )
    )
    if item is None:
        raise ValueError("Watchlist item not found")

    if buy_price is None and sell_price is None:
        raise ValueError("At least one price value is required")

    previous_buy_price = item.current_buy_price
    previous_sell_price = item.current_sell_price
    previous_spread = (
        previous_sell_price - previous_buy_price
        if previous_buy_price is not None and previous_sell_price is not None
        else None
    )

    if buy_price is not None:
        item.current_buy_price = buy_price
    if sell_price is not None:
        item.current_sell_price = sell_price

    session.add(
        PriceHistoryEntry(
            watchlist_item_id=item.id,
            buy_price=buy_price,
            sell_price=sell_price,
            recorded_at=recorded_at or datetime.now(timezone.utc),
        )
    )
    session.commit()
    saved = session.scalar(_watchlist_query().where(WatchlistItem.id == item.id))
    current_spread = (
        saved.current_sell_price - saved.current_buy_price
        if saved.current_buy_price is not None and saved.current_sell_price is not None
        else None
    )
    improvements = []
    if previous_buy_price is not None and buy_price is not None and buy_price < previous_buy_price:
        improvements.append(f"buy price dropped from ${previous_buy_price:.2f} to ${buy_price:.2f}")
    if previous_sell_price is not None and sell_price is not None and sell_price > previous_sell_price:
        improvements.append(f"sell price rose from ${previous_sell_price:.2f} to ${sell_price:.2f}")
    if previous_spread is not None and current_spread is not None and current_spread > previous_spread:
        improvements.append(f"spread improved from ${previous_spread:.2f} to ${current_spread:.2f}")

    if improvements:
        add_alert_event(
            session,
            telegram_chat_id=telegram_chat_id,
            alert_type="watchlist_price_improved",
            title=f"{saved.product_name} improved",
            message="; ".join(improvements),
            severity="info",
            related_query=saved.product_name,
            metadata={
                "item_id": saved.id,
                "source": saved.source,
                "previous_buy_price": previous_buy_price,
                "previous_sell_price": previous_sell_price,
                "previous_spread": previous_spread,
                "current_buy_price": saved.current_buy_price,
                "current_sell_price": saved.current_sell_price,
                "current_spread": current_spread,
            },
        )
    return _serialize_watchlist_item(saved)


def remove_watchlist_item(
    session: Session,
    telegram_chat_id: str,
    item_id: int,
) -> list[WatchlistItemRecord]:
    """Disable a watchlist item for the current user."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    item = session.scalar(
        select(WatchlistItem).where(
            WatchlistItem.id == item_id,
            WatchlistItem.user_id == user.id,
            WatchlistItem.is_enabled.is_(True),
        )
    )
    if item is None:
        raise ValueError("Watchlist item not found")

    item.is_enabled = False
    session.commit()
    return list_watchlist_items(session, telegram_chat_id=telegram_chat_id)


def list_watchlist_history(
    session: Session,
    telegram_chat_id: str,
    item_id: int,
) -> list[PriceHistoryRecord]:
    """List price history for a specific watchlist item."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    item = session.scalar(
        _watchlist_query().where(
            WatchlistItem.id == item_id,
            WatchlistItem.user_id == user.id,
            WatchlistItem.is_enabled.is_(True),
        )
    )
    if item is None:
        raise ValueError("Watchlist item not found")
    return _serialize_watchlist_item(item).price_history


def _competitor_query():
    return (
        select(TrackedCompetitor)
        .options(selectinload(TrackedCompetitor.observations))
        .order_by(TrackedCompetitor.created_at.desc(), TrackedCompetitor.id.desc())
    )


def _serialize_competitor(item: TrackedCompetitor) -> CompetitorRecord:
    return CompetitorRecord(
        competitor_id=item.id,
        seller_username=item.seller_username,
        label=item.label,
        last_scan_at=_normalize_datetime(item.last_scan_at),
        known_item_count=len(item.observations),
    )


def add_tracked_competitor(
    session: Session,
    telegram_chat_id: str,
    seller_username: str,
    label: Optional[str] = None,
) -> CompetitorRecord:
    """Save or re-enable a tracked competitor seller."""
    seller_username = seller_username.strip()
    if not seller_username:
        raise ValueError("seller_username is required")

    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    item = session.scalar(
        select(TrackedCompetitor).where(
            TrackedCompetitor.user_id == user.id,
            TrackedCompetitor.seller_username == seller_username,
        )
    )
    if item is None:
        item = TrackedCompetitor(
            user_id=user.id,
            seller_username=seller_username,
            label=label,
            is_enabled=True,
        )
        session.add(item)
    else:
        item.is_enabled = True
        if label is not None:
            item.label = label

    session.commit()
    saved = session.scalar(_competitor_query().where(TrackedCompetitor.id == item.id))
    return _serialize_competitor(saved)


def _store_lead_query():
    return (
        select(SavedStoreLead)
        .order_by(SavedStoreLead.created_at.desc(), SavedStoreLead.id.desc())
    )


def _serialize_store_lead(item: SavedStoreLead) -> SavedStoreLeadRecord:
    return SavedStoreLeadRecord(
        store_lead_id=item.id,
        domain=item.domain,
        merchant_name=item.merchant_name,
        niche_query=item.niche_query,
        source_integration=item.source_integration,
        estimated_visits=item.estimated_visits,
        estimated_sales_monthly_usd=item.estimated_sales_monthly_usd,
        avg_price_usd=item.avg_price_usd,
        notes=item.notes,
    )


def add_saved_store_lead(
    session: Session,
    telegram_chat_id: str,
    domain: str,
    merchant_name: Optional[str] = None,
    niche_query: Optional[str] = None,
    source_integration: str = "storeleads",
    estimated_visits: Optional[int] = None,
    estimated_sales_monthly_usd: Optional[float] = None,
    avg_price_usd: Optional[float] = None,
    notes: Optional[str] = None,
) -> SavedStoreLeadRecord:
    """Create or re-enable a saved store lead for a user."""
    normalized_domain = domain.strip().lower()
    if not normalized_domain:
        raise ValueError("domain is required")

    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    item = session.scalar(
        select(SavedStoreLead).where(
            SavedStoreLead.user_id == user.id,
            SavedStoreLead.domain == normalized_domain,
        )
    )
    if item is None:
        item = SavedStoreLead(
            user_id=user.id,
            domain=normalized_domain,
            merchant_name=merchant_name,
            niche_query=niche_query,
            source_integration=source_integration,
            estimated_visits=estimated_visits,
            estimated_sales_monthly_usd=estimated_sales_monthly_usd,
            avg_price_usd=avg_price_usd,
            notes=notes,
            is_enabled=True,
        )
        session.add(item)
    else:
        item.is_enabled = True
        item.merchant_name = merchant_name or item.merchant_name
        item.niche_query = niche_query or item.niche_query
        item.source_integration = source_integration or item.source_integration
        item.estimated_visits = estimated_visits
        item.estimated_sales_monthly_usd = estimated_sales_monthly_usd
        item.avg_price_usd = avg_price_usd
        item.notes = notes if notes is not None else item.notes

    session.commit()
    saved = session.scalar(_store_lead_query().where(SavedStoreLead.id == item.id))
    return _serialize_store_lead(saved)


def list_saved_store_leads(
    session: Session,
    telegram_chat_id: str,
) -> list[SavedStoreLeadRecord]:
    """List active saved store leads for a user."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    items = session.scalars(
        _store_lead_query().where(
            SavedStoreLead.user_id == user.id,
            SavedStoreLead.is_enabled.is_(True),
        )
    ).all()
    return [_serialize_store_lead(item) for item in items]


def remove_saved_store_lead(
    session: Session,
    telegram_chat_id: str,
    store_lead_id: int,
) -> list[SavedStoreLeadRecord]:
    """Disable a saved store lead for the current user."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    item = session.scalar(
        select(SavedStoreLead).where(
            SavedStoreLead.id == store_lead_id,
            SavedStoreLead.user_id == user.id,
            SavedStoreLead.is_enabled.is_(True),
        )
    )
    if item is None:
        raise ValueError("Saved store lead not found")

    item.is_enabled = False
    session.commit()
    return list_saved_store_leads(session, telegram_chat_id=telegram_chat_id)


def _discovery_run_query():
    return (
        select(DiscoveryRun)
        .order_by(DiscoveryRun.created_at.desc(), DiscoveryRun.id.desc())
    )


def _serialize_discovery_run(item: DiscoveryRun) -> DiscoveryRunRecord:
    return DiscoveryRunRecord(
        discovery_run_id=item.id,
        query=item.query,
        country=item.country,
        result_limit=item.result_limit,
        store_count=item.store_count,
        ad_count=item.ad_count,
        trend_count=item.trend_count,
        summary=item.summary,
        created_at=_normalize_datetime(item.created_at),
    )


def add_discovery_run(
    session: Session,
    telegram_chat_id: str,
    query: str,
    country: Optional[str] = None,
    result_limit: int = 5,
    store_count: int = 0,
    ad_count: int = 0,
    trend_count: int = 0,
    summary: Optional[str] = None,
) -> DiscoveryRunRecord:
    """Persist a discovery run for recent search history."""
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("query is required")

    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    item = DiscoveryRun(
        user_id=user.id,
        query=normalized_query,
        country=country,
        result_limit=max(1, result_limit),
        store_count=max(0, store_count),
        ad_count=max(0, ad_count),
        trend_count=max(0, trend_count),
        summary=summary,
    )
    session.add(item)
    session.commit()
    saved = session.scalar(_discovery_run_query().where(DiscoveryRun.id == item.id))
    return _serialize_discovery_run(saved)


def list_discovery_runs(
    session: Session,
    telegram_chat_id: str,
    limit: int = 8,
) -> list[DiscoveryRunRecord]:
    """List recent discovery runs for a user."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    items = session.scalars(
        _discovery_run_query().where(
            DiscoveryRun.user_id == user.id,
        ).limit(max(1, limit))
    ).all()
    return [_serialize_discovery_run(item) for item in items]


def get_previous_discovery_run(
    session: Session,
    telegram_chat_id: str,
    query: str,
) -> Optional[DiscoveryRunRecord]:
    """Return the latest prior discovery run for the same query, if any."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    item = session.scalar(
        _discovery_run_query().where(
            DiscoveryRun.user_id == user.id,
            DiscoveryRun.query == query.strip(),
        )
    )
    return _serialize_discovery_run(item) if item else None


def add_alert_event(
    session: Session,
    telegram_chat_id: str,
    alert_type: str,
    title: str,
    message: str,
    severity: str = "info",
    related_query: Optional[str] = None,
    metadata: Optional[dict] = None,
 ) -> Optional[AlertEventRecord]:
    """Persist a user-facing alert event."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    enabled_preferences = _normalize_alert_preferences(
        user.settings.alert_preferences if user.settings is not None else None
    )
    required_preference = ALERT_TYPE_TO_PREFERENCE.get(alert_type)
    if required_preference and required_preference not in enabled_preferences:
        return None
    item = AlertEvent(
        user_id=user.id,
        alert_type=alert_type,
        title=title,
        message=message,
        severity=severity,
        related_query=related_query,
        metadata_json=json.dumps(metadata, ensure_ascii=False) if metadata is not None else None,
        is_read=False,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return AlertEventRecord(
        alert_event_id=item.id,
        alert_type=item.alert_type,
        title=item.title,
        message=item.message,
        severity=item.severity,
        related_query=item.related_query,
        metadata=metadata,
        is_read=item.is_read,
        created_at=_normalize_datetime(item.created_at),
    )


def list_alert_events(
    session: Session,
    telegram_chat_id: str,
    limit: int = 8,
) -> list[AlertEventRecord]:
    """List recent alert events for a user."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    items = session.scalars(
        select(AlertEvent)
        .where(AlertEvent.user_id == user.id)
        .order_by(AlertEvent.created_at.desc(), AlertEvent.id.desc())
        .limit(max(1, limit))
    ).all()
    return [
        AlertEventRecord(
            alert_event_id=item.id,
            alert_type=item.alert_type,
            title=item.title,
            message=item.message,
            severity=item.severity,
            related_query=item.related_query,
            metadata=json.loads(item.metadata_json) if item.metadata_json else None,
            is_read=item.is_read,
            created_at=_normalize_datetime(item.created_at),
        )
        for item in items
    ]


def list_tracked_competitors(
    session: Session,
    telegram_chat_id: str,
) -> list[CompetitorRecord]:
    """List active tracked competitors for a user."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    items = session.scalars(
        _competitor_query().where(
            TrackedCompetitor.user_id == user.id,
            TrackedCompetitor.is_enabled.is_(True),
        )
    ).all()
    return [_serialize_competitor(item) for item in items]


def remove_tracked_competitor(
    session: Session,
    telegram_chat_id: str,
    competitor_id: int,
) -> list[CompetitorRecord]:
    """Disable a tracked competitor."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    item = session.scalar(
        select(TrackedCompetitor).where(
            TrackedCompetitor.id == competitor_id,
            TrackedCompetitor.user_id == user.id,
            TrackedCompetitor.is_enabled.is_(True),
        )
    )
    if item is None:
        raise ValueError("Tracked competitor not found")

    item.is_enabled = False
    session.commit()
    return list_tracked_competitors(session, telegram_chat_id=telegram_chat_id)


async def scan_tracked_competitor(
    session: Session,
    telegram_chat_id: str,
    competitor_id: int,
    tracker: CompetitorTracker,
    query: Optional[str] = None,
    limit: int = 25,
    scanned_at: Optional[datetime] = None,
) -> CompetitorReport:
    """Scan a tracked competitor and persist newly observed item IDs."""
    user = get_or_create_user(session, telegram_chat_id=telegram_chat_id)
    item = session.scalar(
        _competitor_query().where(
            TrackedCompetitor.id == competitor_id,
            TrackedCompetitor.user_id == user.id,
            TrackedCompetitor.is_enabled.is_(True),
        )
    )
    if item is None:
        raise ValueError("Tracked competitor not found")

    previous_top_categories = [
        name
        for name, _ in Counter(
            observation.category for observation in item.observations if observation.category
        ).most_common(3)
    ]
    known_item_ids = {observation.item_id for observation in item.observations}
    report = await tracker.scan_seller(
        seller_username=item.seller_username,
        known_item_ids=known_item_ids,
        query=query,
        limit=limit,
    )

    now = scanned_at or datetime.now(timezone.utc)
    existing_by_item_id = {observation.item_id: observation for observation in item.observations}
    for observed in report.items:
        existing = existing_by_item_id.get(observed.item_id)
        if existing is None:
            session.add(
                CompetitorObservation(
                    competitor_id=item.id,
                    item_id=observed.item_id,
                    title=observed.title,
                    category=observed.category,
                    sold_price=observed.sold_price,
                    sold_date=observed.sold_date,
                    first_seen_at=now,
                    last_seen_at=now,
                )
            )
        else:
            existing.title = observed.title
            existing.category = observed.category
            existing.sold_price = observed.sold_price
            existing.sold_date = observed.sold_date
            existing.last_seen_at = now

    item.last_scan_at = now
    session.commit()
    category_shift = report.top_categories != previous_top_categories and bool(report.top_categories)
    if report.new_count > 0 or category_shift:
        changes = []
        if report.new_count > 0:
            changes.append(f"{report.new_count} new item(s)")
        if category_shift:
            previous_label = ", ".join(previous_top_categories) if previous_top_categories else "none yet"
            current_label = ", ".join(report.top_categories)
            changes.append(f"top categories changed from {previous_label} to {current_label}")
        add_alert_event(
            session,
            telegram_chat_id=telegram_chat_id,
            alert_type="competitor_activity",
            title=f"{item.seller_username} changed",
            message="; ".join(changes),
            severity="info",
            related_query=item.seller_username,
            metadata={
                "competitor_id": item.id,
                "seller_username": item.seller_username,
                "new_count": report.new_count,
                "previous_top_categories": previous_top_categories,
                "current_top_categories": report.top_categories,
            },
        )
    return report
