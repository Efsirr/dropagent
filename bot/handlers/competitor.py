"""Telegram-style handlers for competitor tracking."""

from __future__ import annotations

from typing import Optional

from agent.competitor import CompetitorTracker
from agent.scanner import EbayScanner
from db.service import (
    UserProfile,
    add_tracked_competitor,
    list_alert_events,
    list_tracked_competitors,
    remove_tracked_competitor,
    scan_tracked_competitor,
)
from db.session import get_database_url, get_session
from i18n import t


def _get_chat_id(user_profile: Optional[UserProfile]) -> Optional[str]:
    if user_profile is None:
        return None
    return user_profile.telegram_chat_id


def handle_competitor_command(
    text: str,
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Add a competitor seller to the user's tracker."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: user profile not available"

    raw = text[len("/competitor"):].strip()
    if not raw:
        return "Usage: /competitor <seller_username>"

    session = get_session(get_database_url(env))
    try:
        item = add_tracked_competitor(
            session,
            telegram_chat_id=chat_id,
            seller_username=raw,
        )
        return f'Tracked competitor saved: #{item.competitor_id} "{item.seller_username}"'
    finally:
        session.close()


def handle_competitors_command(
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """List tracked competitors for the current user."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: user profile not available"

    session = get_session(get_database_url(env))
    try:
        items = list_tracked_competitors(session, telegram_chat_id=chat_id)
    finally:
        session.close()

    if not items:
        return "No competitors tracked yet.\nUse /competitor <seller_username> to add one."

    lines = ["Tracked competitors:"]
    for item in items:
        suffix = f" · seen {item.known_item_count} item(s)"
        lines.append(f'#{item.competitor_id} "{item.seller_username}"{suffix}')
    return "\n".join(lines)


def handle_uncompetitor_command(
    text: str,
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Remove a tracked competitor."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: user profile not available"

    parts = text.strip().split()
    if len(parts) != 2:
        return "Usage: /uncompetitor <competitor_id>"

    try:
        competitor_id = int(parts[1])
    except ValueError:
        return f"{t('common.error', lang=lang)}: invalid competitor id"

    session = get_session(get_database_url(env))
    try:
        items = remove_tracked_competitor(
            session,
            telegram_chat_id=chat_id,
            competitor_id=competitor_id,
        )
        return f"Removed competitor #{competitor_id}\nRemaining competitors: {len(items)}"
    except ValueError as error:
        return f"{t('common.error', lang=lang)}: {error}"
    finally:
        session.close()


async def handle_checkcompetitor_command(
    text: str,
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Run a fresh scan for one tracked competitor."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: user profile not available"
    if not (env or {}).get("EBAY_APP_ID", "").strip():
        return f"{t('common.error', lang=lang)}: EBAY_APP_ID is required"

    parts = text.strip().split(maxsplit=2)
    if len(parts) < 2:
        return "Usage: /checkcompetitor <competitor_id> [query]"

    try:
        competitor_id = int(parts[1])
    except ValueError:
        return f"{t('common.error', lang=lang)}: invalid competitor id"

    query = parts[2].strip() if len(parts) == 3 else None

    session = get_session(get_database_url(env))
    scanner = EbayScanner(app_id=(env or {}).get("EBAY_APP_ID"))
    tracker = CompetitorTracker(scanner)
    try:
        report = await scan_tracked_competitor(
            session,
            telegram_chat_id=chat_id,
            competitor_id=competitor_id,
            tracker=tracker,
            query=query,
        )
        return report.summary(lang=lang) + _competitor_alert_suffix(
            session=session,
            chat_id=chat_id,
            competitor_id=competitor_id,
            lang=lang,
        )
    except ValueError as error:
        return f"{t('common.error', lang=lang)}: {error}"
    finally:
        session.close()
        await scanner.close()


def _competitor_alert_suffix(
    session,
    chat_id: str,
    competitor_id: int,
    lang: Optional[str] = None,
) -> str:
    """Append the freshest competitor alert if this scan triggered one."""
    alerts = list_alert_events(session, telegram_chat_id=chat_id, limit=5)
    for item in alerts:
        metadata = item.metadata or {}
        if item.alert_type != "competitor_activity":
            continue
        if metadata.get("competitor_id") != competitor_id:
            continue
        return "\n\n" + t("alerts.triggered", lang=lang, title=item.title, message=item.message)
    return ""
