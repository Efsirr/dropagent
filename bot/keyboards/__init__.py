"""
Telegram keyboard layouts for DropAgent bot.

Provides reply keyboards (persistent bottom buttons) and inline keyboards
(in-message buttons with callback data) for all major bot interactions.

Reply keyboards appear at the bottom of the chat and persist until replaced.
Inline keyboards are attached to specific messages and trigger callback queries.
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import urlencode

from i18n import t


# ---------------------------------------------------------------------------
# Reply Keyboard builders (persistent bottom buttons)
# ---------------------------------------------------------------------------

def main_menu_keyboard(lang: Optional[str] = None) -> dict:
    """
    Main menu reply keyboard with primary commands.

    Shown after /start, /help, or when returning to main menu.
    """
    return {
        "keyboard": [
            [
                {"text": "📊 /digest"},
                {"text": "🧮 /calc"},
            ],
            [
                {"text": "📋 /tracklist"},
                {"text": "👁 /watchlist"},
            ],
            [
                {"text": "⚙️ /settings"},
                {"text": "❓ /help"},
            ],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def settings_reply_keyboard(lang: Optional[str] = None) -> dict:
    """Reply keyboard for settings sub-menu."""
    return {
        "keyboard": [
            [
                {"text": "🌐 /language"},
                {"text": "💰 /minprofit"},
            ],
            [
                {"text": "🏷 /maxbuy"},
                {"text": "🔗 /sources"},
            ],
            [
                {"text": "📅 /schedule"},
                {"text": "◀️ /help"},
            ],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }


def remove_keyboard() -> dict:
    """Remove the current reply keyboard."""
    return {"remove_keyboard": True}


# ---------------------------------------------------------------------------
# Inline Keyboard builders (in-message buttons)
# ---------------------------------------------------------------------------

def language_inline_keyboard(lang: Optional[str] = None) -> dict:
    """Inline keyboard for language selection."""
    return {
        "inline_keyboard": [
            [
                {"text": "🇺🇸 English", "callback_data": "lang:en"},
                {"text": "🇷🇺 Русский", "callback_data": "lang:ru"},
                {"text": "🇨🇳 中文", "callback_data": "lang:zh"},
            ],
        ],
    }


def settings_inline_keyboard(lang: Optional[str] = None) -> dict:
    """Inline keyboard for quick settings access."""
    return {
        "inline_keyboard": [
            [
                {"text": f"🌐 {t('settings.language', lang=lang)}", "callback_data": "settings:language"},
                {"text": f"💰 {t('settings.min_profit', lang=lang)}", "callback_data": "settings:minprofit"},
            ],
            [
                {"text": f"🏷 {t('settings.max_buy_price', lang=lang)}", "callback_data": "settings:maxbuy"},
                {"text": f"🔗 {t('settings.sources', lang=lang)}", "callback_data": "settings:sources"},
            ],
            [
                {"text": f"📅 {t('settings.digest_schedule', lang=lang)}", "callback_data": "settings:schedule"},
            ],
        ],
    }


def dashboard_setup_url(
    public_base_url: Optional[str],
    chat_id: Optional[int] = None,
    username: Optional[str] = None,
) -> Optional[str]:
    """Build a safe dashboard setup URL without secrets."""
    if not public_base_url:
        return None
    base_url = public_base_url.strip()
    if not base_url:
        return None
    params = {}
    if chat_id is not None:
        params["telegram_chat_id"] = str(chat_id)
    if username:
        params["username"] = username
    query = urlencode(params)
    return f"{base_url.rstrip('/')}/?{query}" if query else base_url.rstrip("/")


def onboarding_welcome_keyboard(
    lang: Optional[str] = None,
    dashboard_url: Optional[str] = None,
) -> dict:
    """Inline keyboard for first-run onboarding entry."""
    rows = []
    if dashboard_url:
        rows.append([{"text": t("onboarding.btn_open_dashboard", lang=lang), "url": dashboard_url}])
    rows.append(
        [
            {"text": t("onboarding.btn_begin", lang=lang), "callback_data": "onboarding:start"},
            {"text": t("onboarding.btn_skip", lang=lang), "callback_data": "onboarding:skip"},
        ]
    )
    return {
        "inline_keyboard": rows,
    }


def onboarding_model_keyboard(lang: Optional[str] = None) -> dict:
    """Inline keyboard for primary business model selection."""
    return {
        "inline_keyboard": [
            [
                {"text": t("onboarding.model_us_arbitrage", lang=lang), "callback_data": "onboarding:model:us_arbitrage"},
                {"text": t("onboarding.model_china_dropshipping", lang=lang), "callback_data": "onboarding:model:china_dropshipping"},
            ],
        ],
    }


def onboarding_integrations_keyboard(
    selected_integrations: Optional[list[str]] = None,
    business_model: Optional[str] = None,
    lang: Optional[str] = None,
) -> dict:
    """Inline keyboard for onboarding integration selection."""
    selected = set(selected_integrations or [])
    if business_model == "china_dropshipping":
        integration_rows = [
            ("aliexpress", "AliExpress"),
            ("cj", "CJDropshipping"),
            ("storeleads", "StoreLeads"),
            ("pipiads", "PiPiADS"),
            ("minea", "Minea"),
        ]
    else:
        integration_rows = [
            ("amazon", "Amazon"),
            ("walmart", "Walmart"),
            ("keepa", "Keepa"),
            ("zik", "ZIK Analytics"),
            ("storeleads", "StoreLeads"),
            ("similarweb", "SimilarWeb"),
        ]

    rows = []
    for integration_id, label in integration_rows:
        check = "✅" if integration_id in selected else "⬜"
        rows.append(
            [
                {
                    "text": f"{check} {label}",
                    "callback_data": f"onboarding:toggle:{integration_id}",
                }
            ]
        )
    rows.append(
        [
            {"text": t("onboarding.btn_starter", lang=lang), "callback_data": "onboarding:starter"},
            {"text": t("onboarding.btn_finish", lang=lang), "callback_data": "onboarding:finish"},
        ]
    )
    return {"inline_keyboard": rows}


def schedule_inline_keyboard(lang: Optional[str] = None) -> dict:
    """Inline keyboard for digest schedule selection."""
    return {
        "inline_keyboard": [
            [
                {"text": t("schedule.off", lang=lang), "callback_data": "schedule:off"},
                {"text": t("schedule.daily", lang=lang), "callback_data": "schedule:1"},
            ],
            [
                {"text": t("schedule.2days", lang=lang), "callback_data": "schedule:2"},
                {"text": t("schedule.3days", lang=lang), "callback_data": "schedule:3"},
            ],
            [
                {"text": t("schedule.weekly", lang=lang), "callback_data": "schedule:weekly"},
            ],
        ],
    }


def confirm_inline_keyboard(
    action: str,
    item_id: str = "",
    lang: Optional[str] = None,
) -> dict:
    """Generic confirm/cancel inline keyboard."""
    callback_yes = f"{action}:yes:{item_id}" if item_id else f"{action}:yes"
    callback_no = f"{action}:no:{item_id}" if item_id else f"{action}:no"
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Yes", "callback_data": callback_yes},
                {"text": "❌ No", "callback_data": callback_no},
            ],
        ],
    }


def tracked_query_inline_keyboard(
    queries: list,
    lang: Optional[str] = None,
) -> dict:
    """Inline keyboard with remove buttons for each tracked query."""
    rows = []
    for q in queries[:10]:  # Limit to 10 buttons
        query_text = q.query if hasattr(q, "query") else q.get("query", "?")
        rows.append([
            {"text": f"🗑 {query_text}", "callback_data": f"untrack:{query_text}"},
        ])
    return {"inline_keyboard": rows}


def export_inline_keyboard(lang: Optional[str] = None) -> dict:
    """Inline keyboard for export/notification actions after a result."""
    return {
        "inline_keyboard": [
            [
                {"text": "📊 Google Sheets", "callback_data": "export:sheets"},
                {"text": "📧 Email", "callback_data": "export:email"},
            ],
            [
                {"text": "💬 Discord", "callback_data": "export:discord"},
            ],
        ],
    }


def sources_inline_keyboard(
    current_sources: Optional[list] = None,
    lang: Optional[str] = None,
) -> dict:
    """Inline keyboard to toggle source marketplaces."""
    del lang
    current = set(current_sources or [])
    all_sources = [
        ("amazon", "Amazon"),
        ("walmart", "Walmart"),
        ("aliexpress", "AliExpress"),
        ("cj", "CJDropshipping"),
    ]
    rows = []
    for source_id, label in all_sources:
        check = "✅" if source_id in current else "⬜"
        rows.append([
            {"text": f"{check} {label}", "callback_data": f"source_toggle:{source_id}"},
        ])
    rows.append([
        {"text": "💾 Save", "callback_data": "source_toggle:save"},
    ])
    return {"inline_keyboard": rows}
