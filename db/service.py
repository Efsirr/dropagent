"""Higher-level database operations for users, settings, and tracked queries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from db.models import TrackedQuery, User, UserSettings


_UNSET = object()
SUPPORTED_SOURCES = {"amazon", "walmart"}
SUPPORTED_DIGEST_INTERVALS = {1, 2, 3, 7}


@dataclass
class TrackedQueryRecord:
    """Serializable tracked-query data for bot and dashboard use."""

    query: str
    category: Optional[str] = None
    max_buy_price: Optional[float] = None
    min_profit_threshold: Optional[float] = None


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
    enabled_sources: list[str] = field(default_factory=list)
    tracked_queries: list[TrackedQueryRecord] = field(default_factory=list)


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
        enabled_sources=_normalize_sources(settings.enabled_sources),
        tracked_queries=tracked_queries,
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
    min_profit_threshold: Optional[float] = None,
    max_buy_price=_UNSET,
    enabled_sources: Optional[list[str]] = None,
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
    if min_profit_threshold is not None:
        settings.min_profit_threshold = min_profit_threshold
    if max_buy_price is not _UNSET:
        settings.max_buy_price = max_buy_price
    if enabled_sources is not None:
        settings.enabled_sources = _serialize_sources(enabled_sources)
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
