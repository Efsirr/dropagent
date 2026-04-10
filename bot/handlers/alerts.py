"""Telegram-style handlers for recent alert events."""

from __future__ import annotations

from typing import Optional

from db.service import UserProfile, list_alert_events
from db.session import get_database_url, get_session
from i18n import t


def _get_chat_id(user_profile: Optional[UserProfile]) -> Optional[str]:
    if user_profile is None:
        return None
    return user_profile.telegram_chat_id


def handle_alerts_command(
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Render recent alert events for the current user."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: {t('common.user_not_available', lang=lang)}"

    session = get_session(get_database_url(env))
    try:
        alerts = list_alert_events(session, telegram_chat_id=chat_id, limit=5)
    finally:
        session.close()

    if not alerts:
        return t("alerts.empty", lang=lang)

    lines = [t("alerts.title", lang=lang)]
    for item in alerts:
        lines.append(f'- {item.title}: {item.message}')
    return "\n".join(lines)
