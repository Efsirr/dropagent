"""Telegram-style handlers for user settings and tracked queries."""

from __future__ import annotations

from typing import Optional

from db.service import (
    SUPPORTED_SOURCES,
    UserProfile,
    add_tracked_query,
    list_tracked_queries,
    remove_tracked_query,
    update_digest_schedule,
    update_user_settings,
)
from db.session import get_database_url, get_session
from i18n import SUPPORTED_LANGUAGES, t


def _get_chat_id(user_profile: Optional[UserProfile]) -> Optional[str]:
    if user_profile is None:
        return None
    return user_profile.telegram_chat_id


def handle_settings_command(
    user_profile: Optional[UserProfile],
    lang: Optional[str] = None,
) -> str:
    """Render the current persisted settings for the user."""
    if user_profile is None:
        return f"{t('common.error', lang=lang)}: user profile not available"

    tracked = ", ".join(item.query for item in user_profile.tracked_queries) or "none"
    sources = ", ".join(user_profile.enabled_sources) or "none"
    max_buy = (
        f"${user_profile.max_buy_price:.2f}"
        if user_profile.max_buy_price is not None
        else "not set"
    )
    if not user_profile.digest_enabled:
        schedule = "off"
    elif user_profile.digest_interval_days == 7:
        schedule = "weekly"
    else:
        schedule = f"every {user_profile.digest_interval_days} day(s)"
    return (
        "Saved settings:\n"
        f"Language: {user_profile.preferred_language}\n"
        f"Min profit: ${user_profile.min_profit_threshold:.2f}\n"
        f"Max buy price: {max_buy}\n"
        f"Digest schedule: {schedule}\n"
        f"Sources: {sources}\n"
        f"Tracked queries: {tracked}"
    )


def handle_track_command(
    text: str,
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Save a tracked query for future digests."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: user profile not available"

    query = text[len("/track"):].strip()
    if not query:
        return "Usage: /track <query>\nExample: /track airpods pro"

    session = get_session(get_database_url(env))
    try:
        updated = add_tracked_query(session, telegram_chat_id=chat_id, query=query)
        total = len(updated.tracked_queries)
        return f'Saved tracked query: "{query}"\nTotal tracked queries: {total}'
    finally:
        session.close()


def handle_tracklist_command(
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Show saved tracked queries for the current user."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: user profile not available"

    session = get_session(get_database_url(env))
    try:
        tracked_queries = list_tracked_queries(session, telegram_chat_id=chat_id)
    finally:
        session.close()

    if not tracked_queries:
        return "No tracked queries saved yet.\nUse /track <query> to add one."

    lines = ["Tracked queries:"]
    for index, tracked in enumerate(tracked_queries, start=1):
        details = []
        if tracked.max_buy_price is not None:
            details.append(f"max buy ${tracked.max_buy_price:.2f}")
        if tracked.min_profit_threshold is not None:
            details.append(f"min profit ${tracked.min_profit_threshold:.2f}")

        suffix = f" ({', '.join(details)})" if details else ""
        lines.append(f'{index}. "{tracked.query}"{suffix}')
    return "\n".join(lines)


def handle_untrack_command(
    text: str,
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Remove a tracked query from future digests."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: user profile not available"

    query = text[len("/untrack"):].strip()
    if not query:
        return 'Usage: /untrack <query>\nExample: /untrack airpods pro'

    session = get_session(get_database_url(env))
    try:
        updated = remove_tracked_query(session, telegram_chat_id=chat_id, query=query)
        return f'Removed tracked query: "{query}"\nRemaining tracked queries: {len(updated.tracked_queries)}'
    except ValueError as error:
        return f"{t('common.error', lang=lang)}: {error}"
    finally:
        session.close()


def handle_language_command(
    text: str,
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Update the user's preferred language."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: user profile not available"

    parts = text.strip().split()
    if len(parts) != 2:
        return "Usage: /language <en|ru|zh>"

    preferred_language = parts[1].lower()
    if preferred_language not in SUPPORTED_LANGUAGES:
        return f"{t('common.error', lang=lang)}: unsupported language"

    session = get_session(get_database_url(env))
    try:
        update_user_settings(
            session,
            telegram_chat_id=chat_id,
            preferred_language=preferred_language,
        )
        return t("common.language_set", lang=preferred_language)
    finally:
        session.close()


def handle_minprofit_command(
    text: str,
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Update the user's minimum profit threshold."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: user profile not available"

    parts = text.strip().split()
    if len(parts) != 2:
        return "Usage: /minprofit <amount>"

    try:
        min_profit = float(parts[1])
    except ValueError:
        return f"{t('common.error', lang=lang)}: invalid numeric value"

    session = get_session(get_database_url(env))
    try:
        update_user_settings(
            session,
            telegram_chat_id=chat_id,
            min_profit_threshold=min_profit,
        )
        return f"Minimum profit saved: ${min_profit:.2f}"
    finally:
        session.close()


def handle_maxbuy_command(
    text: str,
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Update or clear the user's max buy price."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: user profile not available"

    parts = text.strip().split()
    if len(parts) != 2:
        return "Usage: /maxbuy <amount|clear>"

    raw_value = parts[1].lower()
    if raw_value == "clear":
        value = None
    else:
        try:
            value = float(raw_value)
        except ValueError:
            return f"{t('common.error', lang=lang)}: invalid numeric value"

    session = get_session(get_database_url(env))
    try:
        update_user_settings(
            session,
            telegram_chat_id=chat_id,
            max_buy_price=value,
        )
        if value is None:
            return "Maximum buy price cleared"
        return f"Maximum buy price saved: ${value:.2f}"
    finally:
        session.close()


def handle_sources_command(
    text: str,
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Update enabled source marketplaces for the user."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: user profile not available"

    raw = text[len("/sources"):].strip()
    if not raw:
        return "Usage: /sources amazon,walmart"

    sources = [source.strip().lower() for source in raw.split(",") if source.strip()]
    if not sources or any(source not in SUPPORTED_SOURCES for source in sources):
        return f"{t('common.error', lang=lang)}: unsupported source list"

    session = get_session(get_database_url(env))
    try:
        update_user_settings(
            session,
            telegram_chat_id=chat_id,
            enabled_sources=sources,
        )
        return f"Enabled sources saved: {', '.join(sources)}"
    finally:
        session.close()


def handle_schedule_command(
    text: str,
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Update automatic digest frequency for the user."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: user profile not available"

    parts = text.strip().split()
    if len(parts) != 2:
        return "Usage: /schedule <1d|2d|3d|weekly|off>"

    raw_value = parts[1].lower()
    mapping = {
        "1": 1,
        "1d": 1,
        "daily": 1,
        "2": 2,
        "2d": 2,
        "3": 3,
        "3d": 3,
        "weekly": 7,
        "week": 7,
        "7d": 7,
    }

    session = get_session(get_database_url(env))
    try:
        if raw_value == "off":
            update_digest_schedule(
                session,
                telegram_chat_id=chat_id,
                interval_days=1,
                enabled=False,
            )
            return "Auto digest schedule turned off"

        interval_days = mapping.get(raw_value)
        if interval_days is None:
            return f"{t('common.error', lang=lang)}: unsupported schedule"

        update_digest_schedule(
            session,
            telegram_chat_id=chat_id,
            interval_days=interval_days,
            enabled=True,
        )

        if interval_days == 7:
            return "Auto digest schedule saved: weekly"
        return f"Auto digest schedule saved: every {interval_days} day(s)"
    finally:
        session.close()
