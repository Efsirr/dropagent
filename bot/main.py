"""Telegram polling bot for DropAgent."""

import asyncio
import os
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional

import httpx
from dotenv import load_dotenv

from bot.handlers.calc import handle_calc_command
from bot.handlers.digest import handle_digest_command
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
from db.service import (
    UserProfile,
    get_or_create_user_profile,
    list_due_digest_profiles,
    mark_digest_sent,
)
from db.session import get_database_url, get_session
from i18n import SUPPORTED_LANGUAGES, t


Router = Callable[[str, Optional[dict], Optional[str], Optional["BotContext"]], Awaitable[str]]


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
            "allowed_updates": '["message"]',
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

    async def send_message(self, chat_id: int, text: str) -> dict:
        """Send a plain text message to a Telegram chat."""
        client = await self._get_client()
        response = await client.post(
            f"{self.base_url}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
            },
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok", False):
            raise ValueError("Telegram sendMessage returned ok=false")
        return payload.get("result", {})

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()


async def handle_message(
    text: str,
    env: Optional[dict] = None,
    lang: Optional[str] = None,
    context: Optional[BotContext] = None,
) -> str:
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

    if stripped.startswith("/tracklist"):
        return handle_tracklist_command(
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

    if stripped.startswith("/track"):
        return handle_track_command(
            stripped,
            env=env,
            user_profile=user_profile,
            lang=lang,
        )

    if stripped.startswith("/settings"):
        return handle_settings_command(user_profile=user_profile, lang=lang)

    if stripped.startswith("/language"):
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
        return t("common.welcome", lang=lang)

    if stripped.startswith("/help"):
        return (
            "Available commands:\n"
            "/calc <buy_price> <sell_price> [shipping] [packaging]\n"
            "/digest [--query QUERY] [--top N] [--min-profit X]\n"
            "/track <query>\n"
            "/tracklist\n"
            "/untrack <query>\n"
            "/settings\n"
            "/language <en|ru|zh>\n"
            "/minprofit <amount>\n"
            "/maxbuy <amount|clear>\n"
            "/sources amazon,walmart\n"
            "/schedule <1d|2d|3d|weekly|off>"
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


async def process_update(
    update: dict,
    bot_client: TelegramBotClient,
    env: Optional[dict] = None,
    router: Router = handle_message,
) -> bool:
    """Process a single Telegram update and send the reply."""
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
            message = (
                "Auto digest skipped: no tracked queries saved.\n"
                "Use /track <query> to add products for automatic reports."
            )

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
