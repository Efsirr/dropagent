"""Telegram polling bot for DropAgent."""

import asyncio
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Awaitable, Callable, Optional, Union

import httpx
from dotenv import load_dotenv

from bot.handlers.calc import handle_calc_command
from bot.handlers.digest import handle_digest_command
from bot.handlers.listing import handle_listing_command
from bot.handlers.competitor import (
    handle_checkcompetitor_command,
    handle_competitor_command,
    handle_competitors_command,
    handle_uncompetitor_command,
)
from bot.handlers.settings import (
    handle_language_command,
    handle_maxbuy_command,
    handle_minprofit_command,
    handle_schedule_command,
    handle_settings_command,
    handle_sources_command,
    handle_track_command,
    handle_tracklist_command,
    handle_untrack_command,
)
from bot.handlers.status import handle_status_command
from bot.handlers.watchlist import (
    handle_pricepoint_command,
    handle_unwatch_command,
    handle_watch_command,
    handle_watchlist_command,
)
from bot.onboarding import (
    render_integration_recommendations,
    render_model_prompt,
    render_onboarding_complete,
    render_onboarding_welcome,
)
from bot.handlers.weekly import handle_weekly_command
from db.service import (
    UserProfile,
    get_or_create_user_profile,
    list_due_digest_profiles,
    mark_digest_sent,
    update_user_settings,
)
from db.session import get_database_url, get_session
from i18n import SUPPORTED_LANGUAGES, t
from bot.keyboards import (
    main_menu_keyboard,
    settings_reply_keyboard,
    settings_inline_keyboard,
    onboarding_welcome_keyboard,
    onboarding_model_keyboard,
    onboarding_integrations_keyboard,
    language_inline_keyboard,
    schedule_inline_keyboard,
    tracked_query_inline_keyboard,
    export_inline_keyboard,
    sources_inline_keyboard,
)


@dataclass
class BotResponse:
    """Wrapper for a bot reply — text + optional keyboard markup."""

    text: str
    reply_markup: Optional[dict] = None


Router = Callable[[str, Optional[dict], Optional[str], Optional["BotContext"]], Awaitable[Union[str, BotResponse]]]
DEFAULT_BOT_HEARTBEAT_PATH = Path("/tmp/dropagent-bot-heartbeat")


@dataclass
class BotContext:
    """Current Telegram user context passed to handlers."""

    user_profile: Optional[UserProfile] = None
    username: Optional[str] = None
    chat_id: Optional[int] = None


class TelegramBotClient:
    """Minimal Telegram Bot API client using long polling."""

    def __init__(self, token: str, timeout: float = 35.0):
        self.token = token
        self.timeout = timeout
        self.base_url = f"https://api.telegram.org/bot{token}"
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def get_updates(self, offset: Optional[int] = None, timeout: int = 30) -> list[dict]:
        """Fetch updates from Telegram via long polling."""
        params = {
            "timeout": timeout,
            "allowed_updates": '["message","callback_query"]',
        }
        if offset is not None:
            params["offset"] = offset

        client = await self._get_client()
        response = await client.get(f"{self.base_url}/getUpdates", params=params)
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok", False):
            raise ValueError("Telegram getUpdates returned ok=false")
        return payload.get("result", [])

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: Optional[dict] = None,
    ) -> dict:
        """Send a text message to a Telegram chat, optionally with a keyboard."""
        client = await self._get_client()
        body: dict = {
            "chat_id": chat_id,
            "text": text,
        }
        if reply_markup is not None:
            body["reply_markup"] = reply_markup
        response = await client.post(
            f"{self.base_url}/sendMessage",
            json=body,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok", False):
            raise ValueError("Telegram sendMessage returned ok=false")
        return payload.get("result", {})

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
    ) -> dict:
        """Acknowledge a callback query from an inline keyboard button."""
        client = await self._get_client()
        body: dict = {"callback_query_id": callback_query_id}
        if text:
            body["text"] = text
        response = await client.post(
            f"{self.base_url}/answerCallbackQuery",
            json=body,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("result", {})

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()


def get_bot_heartbeat_path(env: Optional[dict] = None) -> Path:
    """Resolve the heartbeat file path used by Docker health checks."""
    env = env or os.environ
    configured = env.get("BOT_HEARTBEAT_PATH", str(DEFAULT_BOT_HEARTBEAT_PATH))
    return Path(configured)


def write_heartbeat(path: Optional[Path] = None) -> None:
    """Write a timestamp heartbeat file for Docker health checks."""
    heartbeat_path = path or get_bot_heartbeat_path()
    heartbeat_path.write_text(str(time.time()), encoding="utf-8")


def is_heartbeat_fresh(
    path: Optional[Path] = None,
    max_age_seconds: float = 120.0,
) -> bool:
    """Check whether the bot heartbeat file has been updated recently."""
    heartbeat_path = path or get_bot_heartbeat_path()
    if not heartbeat_path.exists():
        return False
    age_seconds = time.time() - heartbeat_path.stat().st_mtime
    return age_seconds <= max_age_seconds


async def handle_message(
    text: str,
    env: Optional[dict] = None,
    lang: Optional[str] = None,
    context: Optional[BotContext] = None,
) -> Union[str, BotResponse]:
    """Route a bot message to the appropriate command handler."""
    stripped = text.strip()
    user_profile = context.user_profile if context else None

    if not stripped:
        return t("common.help", lang=lang)

    if stripped.startswith("/calc"):
        return handle_calc_command(stripped, lang=lang)

    if stripped.startswith("/digest"):
        return await handle_digest_command(
            stripped,
            env=env,
            lang=lang,
            user_profile=user_profile,
        )

    if stripped.startswith("/weekly"):
        return await handle_weekly_command(
            stripped,
            env=env,
            lang=lang,
        )

    if stripped.startswith("/listing"):
        return handle_listing_command(stripped, lang=lang)

    if stripped.startswith("/competitors"):
        return handle_competitors_command(
            env=env,
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/competitor"):
        return handle_competitor_command(
            stripped,
            env=env,
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/uncompetitor"):
        return handle_uncompetitor_command(
            stripped,
            env=env,
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/checkcompetitor"):
        return await handle_checkcompetitor_command(
            stripped,
            env=env,
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/tracklist"):
        return handle_tracklist_command(
            env=env,
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/watchlist"):
        return handle_watchlist_command(
            env=env,
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/untrack"):
        return handle_untrack_command(
            stripped,
            env=env,
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/unwatch"):
        return handle_unwatch_command(
            stripped,
            env=env,
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/track"):
        return handle_track_command(
            stripped,
            env=env,
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/watch"):
        return handle_watch_command(
            stripped,
            env=env,
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/pricepoint"):
        return handle_pricepoint_command(
            stripped,
            env=env,
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/setup"):
        return BotResponse(
            text=render_onboarding_welcome(env=env, lang=lang),
            reply_markup=onboarding_welcome_keyboard(lang=lang),
        )

    if stripped.startswith("/status"):
        return handle_status_command(
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/settings"):
        text = handle_settings_command(user_profile=user_profile, lang=lang)
        return BotResponse(text=text, reply_markup=settings_inline_keyboard(lang=lang))

    if stripped.startswith("/language"):
        # If just "/language" with no arg, show inline picker
        if stripped.strip() == "/language":
            return BotResponse(
                text=t("language.usage", lang=lang),
                reply_markup=language_inline_keyboard(lang=lang),
            )
        return handle_language_command(
            stripped,
            env=env,
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/minprofit"):
        return handle_minprofit_command(
            stripped,
            env=env,
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/maxbuy"):
        return handle_maxbuy_command(
            stripped,
            env=env,
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/sources"):
        return handle_sources_command(
            stripped,
            env=env,
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/schedule"):
        return handle_schedule_command(
            stripped,
            env=env,
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/start"):
        if user_profile is not None and not user_profile.onboarding_completed:
            return BotResponse(
                text=render_onboarding_welcome(env=env, lang=lang),
                reply_markup=onboarding_welcome_keyboard(lang=lang),
            )
        return BotResponse(
            text=t("common.welcome", lang=lang),
            reply_markup=main_menu_keyboard(lang=lang),
        )

    if stripped.startswith("/help"):
        return (
            f"{t('help.title', lang=lang)}\n"
            f"{t('help.setup', lang=lang)}\n"
            f"{t('help.status', lang=lang)}\n"
            f"{t('help.calc', lang=lang)}\n"
            f"{t('help.digest', lang=lang)}\n"
            f"{t('help.weekly', lang=lang)}\n"
            f"{t('help.listing', lang=lang)}\n"
            f"{t('help.competitor', lang=lang)}\n"
            f"{t('help.competitors', lang=lang)}\n"
            f"{t('help.uncompetitor', lang=lang)}\n"
            f"{t('help.checkcompetitor', lang=lang)}\n"
            f"{t('help.track', lang=lang)}\n"
            f"{t('help.tracklist', lang=lang)}\n"
            f"{t('help.untrack', lang=lang)}\n"
            f"{t('help.watch', lang=lang)}\n"
            f"{t('help.watchlist', lang=lang)}\n"
            f"{t('help.unwatch', lang=lang)}\n"
            f"{t('help.pricepoint', lang=lang)}\n"
            f"{t('help.settings', lang=lang)}\n"
            f"{t('help.language_cmd', lang=lang)}\n"
            f"{t('help.minprofit', lang=lang)}\n"
            f"{t('help.maxbuy', lang=lang)}\n"
            f"{t('help.sources', lang=lang)}\n"
            f"{t('help.schedule', lang=lang)}"
        )

    return t("common.help", lang=lang)


def _extract_language(update: dict) -> Optional[str]:
    """Extract a supported Telegram language code from an update."""
    language = (
        update.get("message", {})
        .get("from", {})
        .get("language_code")
    )
    if not language:
        return None

    normalized = language.split("-")[0].lower()
    if normalized in SUPPORTED_LANGUAGES:
        return normalized
    return None


def _extract_text_message(update: dict) -> tuple[Optional[int], Optional[str]]:
    """Extract chat ID and text from a Telegram update."""
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text")
    if chat_id is None or not text:
        return None, None
    return chat_id, text


def _extract_username(update: dict) -> Optional[str]:
    """Extract Telegram username from the update when available."""
    return update.get("message", {}).get("from", {}).get("username")


async def process_callback_query(
    update: dict,
    bot_client: TelegramBotClient,
    env: Optional[dict] = None,
) -> bool:
    """Handle inline keyboard button presses (callback queries)."""
    callback = update.get("callback_query")
    if not callback:
        return False

    callback_id = callback.get("id", "")
    data = callback.get("data", "")
    chat_id = callback.get("message", {}).get("chat", {}).get("id")
    if not chat_id or not data:
        return False

    # Resolve user profile
    lang_code = callback.get("from", {}).get("language_code", "")
    lang = lang_code.split("-")[0].lower() if lang_code else None
    if lang not in SUPPORTED_LANGUAGES:
        lang = None
    username = callback.get("from", {}).get("username")

    session = get_session(get_database_url(env))
    try:
        user_profile = get_or_create_user_profile(
            session,
            telegram_chat_id=str(chat_id),
            username=username,
            preferred_language=lang,
        )
    finally:
        session.close()

    effective_lang = user_profile.preferred_language or lang
    reply_text = None
    reply_markup = None

    # --- Route callback data ---

    if data.startswith("lang:"):
        new_lang = data.split(":")[1]
        reply_text = handle_language_command(
            f"/language {new_lang}",
            env=env,
            user_profile=user_profile,
            lang=effective_lang,
        )

    elif data.startswith("schedule:"):
        value = data.split(":")[1]
        reply_text = handle_schedule_command(
            f"/schedule {value}",
            env=env,
            user_profile=user_profile,
            lang=effective_lang,
        )

    elif data.startswith("untrack:"):
        query = data.split(":", 1)[1]
        reply_text = handle_untrack_command(
            f"/untrack {query}",
            env=env,
            user_profile=user_profile,
            lang=effective_lang,
        )

    elif data.startswith("settings:"):
        action = data.split(":")[1]
        if action == "language":
            reply_text = t("language.usage", lang=effective_lang)
            reply_markup = language_inline_keyboard(lang=effective_lang)
        elif action == "schedule":
            reply_text = t("schedule.usage", lang=effective_lang)
            reply_markup = schedule_inline_keyboard(lang=effective_lang)
        elif action == "sources":
            reply_markup = sources_inline_keyboard(
                current_sources=user_profile.enabled_sources,
                lang=effective_lang,
            )
            reply_text = t("settings.sources", lang=effective_lang)
        else:
            # minprofit, maxbuy — prompt text input
            usage_key = f"{action}.usage"
            reply_text = t(usage_key, lang=effective_lang)

    elif data.startswith("source_toggle:"):
        value = data.split(":")[1]
        if value == "save":
            reply_text = t("settings.saved", lang=effective_lang)
        else:
            reply_text = f"Toggle {value} — use /sources command to update."

    elif data.startswith("onboarding:"):
        parts = data.split(":")
        action = parts[1] if len(parts) > 1 else ""
        session = get_session(get_database_url(env))
        try:
            if action == "start":
                reply_text = render_model_prompt(lang=effective_lang)
                reply_markup = onboarding_model_keyboard(lang=effective_lang)
            elif action == "skip":
                user_profile = update_user_settings(
                    session,
                    telegram_chat_id=str(chat_id),
                    onboarding_completed=True,
                )
                reply_text = t("onboarding.skipped", lang=effective_lang)
                reply_markup = main_menu_keyboard(lang=effective_lang)
            elif action == "model" and len(parts) >= 3:
                business_model = parts[2]
                enabled_sources = (
                    ["aliexpress", "cj"]
                    if business_model == "china_dropshipping"
                    else ["amazon", "walmart"]
                )
                user_profile = update_user_settings(
                    session,
                    telegram_chat_id=str(chat_id),
                    business_model=business_model,
                    enabled_sources=enabled_sources,
                    selected_integrations=enabled_sources,
                    onboarding_completed=False,
                )
                reply_text = render_integration_recommendations(
                    user_profile=user_profile,
                    env=env,
                    lang=effective_lang,
                )
                reply_markup = onboarding_integrations_keyboard(
                    selected_integrations=user_profile.selected_integrations,
                    business_model=user_profile.business_model,
                    lang=effective_lang,
                )
            elif action == "toggle" and len(parts) >= 3:
                integration_id = parts[2]
                selected = set(user_profile.selected_integrations)
                if integration_id in selected:
                    selected.remove(integration_id)
                else:
                    selected.add(integration_id)
                user_profile = update_user_settings(
                    session,
                    telegram_chat_id=str(chat_id),
                    selected_integrations=sorted(selected),
                )
                reply_text = render_integration_recommendations(
                    user_profile=user_profile,
                    env=env,
                    lang=effective_lang,
                )
                reply_markup = onboarding_integrations_keyboard(
                    selected_integrations=user_profile.selected_integrations,
                    business_model=user_profile.business_model,
                    lang=effective_lang,
                )
            elif action == "starter":
                reply_text = (
                    f"{render_model_prompt(lang=effective_lang)}\n\n"
                    f"{render_integration_recommendations(user_profile=user_profile, env=env, lang=effective_lang)}"
                )
                reply_markup = onboarding_integrations_keyboard(
                    selected_integrations=user_profile.selected_integrations,
                    business_model=user_profile.business_model,
                    lang=effective_lang,
                )
            elif action == "finish":
                user_profile = update_user_settings(
                    session,
                    telegram_chat_id=str(chat_id),
                    onboarding_completed=True,
                )
                reply_text = render_onboarding_complete(
                    user_profile=user_profile,
                    lang=effective_lang,
                )
                reply_markup = main_menu_keyboard(lang=effective_lang)
        finally:
            session.close()

    # Acknowledge the callback
    await bot_client.answer_callback_query(callback_id)

    # Send reply if we produced one
    if reply_text:
        await bot_client.send_message(chat_id, reply_text, reply_markup=reply_markup)

    return True


async def process_update(
    update: dict,
    bot_client: TelegramBotClient,
    env: Optional[dict] = None,
    router: Router = handle_message,
) -> bool:
    """Process a single Telegram update and send the reply."""
    # Handle callback queries from inline keyboards
    if "callback_query" in update:
        return await process_callback_query(update, bot_client, env)

    chat_id, text = _extract_text_message(update)
    if chat_id is None or text is None:
        return False

    lang = _extract_language(update)
    username = _extract_username(update)
    session = get_session(get_database_url(env))
    try:
        user_profile = get_or_create_user_profile(
            session,
            telegram_chat_id=str(chat_id),
            username=username,
            preferred_language=lang,
        )
    finally:
        session.close()

    effective_lang = user_profile.preferred_language or lang
    context = BotContext(
        user_profile=user_profile,
        username=username,
        chat_id=chat_id,
    )
    reply = await router(text, env, effective_lang, context)

    # Handle both str and BotResponse returns
    if isinstance(reply, BotResponse):
        await bot_client.send_message(chat_id, reply.text, reply_markup=reply.reply_markup)
    else:
        await bot_client.send_message(chat_id, reply)
    return True


async def poll_once(
    bot_client: TelegramBotClient,
    offset: Optional[int] = None,
    env: Optional[dict] = None,
    router: Router = handle_message,
    timeout: int = 30,
) -> Optional[int]:
    """Poll Telegram once, process updates, and return the next offset."""
    updates = await bot_client.get_updates(offset=offset, timeout=timeout)
    next_offset = offset

    for update in updates:
        await process_update(update, bot_client=bot_client, env=env, router=router)
        update_id = update.get("update_id")
        if update_id is not None:
            next_offset = update_id + 1

    return next_offset


async def process_scheduled_digests(
    bot_client: TelegramBotClient,
    env: Optional[dict] = None,
) -> int:
    """Send due scheduled digests to users and advance their next run time."""
    env = env or os.environ
    session = get_session(get_database_url(env))
    sent_count = 0

    try:
        due_profiles = list_due_digest_profiles(session)
    finally:
        session.close()

    for profile in due_profiles:
        if profile.tracked_queries:
            message = await handle_digest_command(
                "/digest",
                env=env,
                lang=profile.preferred_language,
                user_profile=profile,
            )
        else:
            message = t("digest.auto_skipped", lang=profile.preferred_language)

        await bot_client.send_message(int(profile.telegram_chat_id), message)

        session = get_session(get_database_url(env))
        try:
            mark_digest_sent(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()
        sent_count += 1

    return sent_count


async def run_polling(
    bot_client: TelegramBotClient,
    env: Optional[dict] = None,
    router: Router = handle_message,
    timeout: int = 30,
) -> None:
    """Run the Telegram long-polling loop until interrupted."""
    offset = None
    try:
        while True:
            write_heartbeat()
            offset = await poll_once(
                bot_client=bot_client,
                offset=offset,
                env=env,
                router=router,
                timeout=timeout,
            )
            await process_scheduled_digests(bot_client=bot_client, env=env)
    finally:
        await bot_client.close()


def main() -> int:
    """CLI entry point for running the Telegram bot."""
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN is required")
        return 1

    bot_client = TelegramBotClient(token=token)
    try:
        asyncio.run(run_polling(bot_client=bot_client, env=os.environ))
    except KeyboardInterrupt:
        return 0
    except (httpx.HTTPError, ValueError) as error:
        print(f"Error: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
