"""Telegram-style handlers for simple competitor store discovery."""

from __future__ import annotations

from typing import Optional

from agent.adapters.storeleads import get_storeleads_adapter_for_user
from agent.store_discovery import build_store_discovery_report
from db.service import UserProfile
from db.session import get_database_url, get_session
from i18n import t


def _get_chat_id(user_profile: Optional[UserProfile]) -> Optional[str]:
    if user_profile is None:
        return None
    return user_profile.telegram_chat_id


async def handle_discoverstores_command(
    text: str,
    env: Optional[dict] = None,
    user_profile: Optional[UserProfile] = None,
    lang: Optional[str] = None,
) -> str:
    """Discover competitor stores for a niche using StoreLeads."""
    chat_id = _get_chat_id(user_profile)
    if chat_id is None:
        return f"{t('common.error', lang=lang)}: {t('common.user_not_available', lang=lang)}"

    query = text[len("/discoverstores"):].strip()
    if not query:
        return t("discovery.usage", lang=lang)

    session = get_session(get_database_url(env))
    adapter = None
    try:
        adapter = get_storeleads_adapter_for_user(
            telegram_chat_id=chat_id,
            session=session,
            app_secret=(env or {}).get("APP_SECRET_KEY"),
        )
        if adapter is None:
            return t("discovery.connect_first", lang=lang)

        try:
            stores = await adapter.search_domains(
                platform="shopify",
                categories=query,
                page_size=5,
            )
        except Exception:
            return t("common.api_error", lang=lang)
        report = build_store_discovery_report(
            query=query,
            stores=stores[:5],
            platform="shopify",
        )
        return report.summary(lang=lang)
    finally:
        session.close()
        if adapter is not None:
            await adapter.close()
