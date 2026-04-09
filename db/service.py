"""Higher-level database operations for users, settings, and tracked queries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from agent.competitor import CompetitorReport, CompetitorTracker
from db.models import CompetitorObservation, PriceHistoryEntry, TrackedCompetitor, TrackedQuery, User, UserSettings, WatchlistItem


_UNSET = object()
SUPPORTED_SOURCES = {"amazon", "walmart", "aliexpress", "cj"}
SUPPORTED_DIGEST_INTERVALS = {1, 2, 3, 7}


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
    tracked_queries: list[TrackedQueryRecord] = field(default_factory=list)
    watchlist_items: list[WatchlistItemRecord] = field(default_factory=list)
    tracked_competitors: list[CompetitorRecord] = field(default_factory=list)


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
        tracked_queries=tracked_queries,
        watchlist_items=watchlist_items,
        tracked_competitors=tracked_competitors,
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
    return report
