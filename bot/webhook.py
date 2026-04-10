"""HTTP-friendly Telegram webhook handler for hosted DropAgent deployments."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Optional

from bot.main import TelegramBotClient, process_update


TELEGRAM_SECRET_HEADER = "x-telegram-bot-api-secret-token"


@dataclass(frozen=True)
class WebhookResponse:
    """Small response object for framework/serverless adapters."""

    status_code: int
    payload: dict


def verify_webhook_secret(headers: Optional[dict], env: Optional[dict] = None) -> bool:
    """Validate Telegram's webhook secret header when the instance configured one."""
    env = env or {}
    expected = env.get("TELEGRAM_WEBHOOK_SECRET", "").strip()
    if not expected:
        return True
    headers = headers or {}
    normalized = {str(key).lower(): str(value) for key, value in headers.items()}
    return normalized.get(TELEGRAM_SECRET_HEADER) == expected


async def handle_telegram_webhook_async(
    body: bytes,
    headers: Optional[dict] = None,
    env: Optional[dict] = None,
    bot_client: Optional[TelegramBotClient] = None,
) -> WebhookResponse:
    """Process one Telegram webhook HTTP request."""
    env = env or {}
    if not verify_webhook_secret(headers=headers, env=env):
        return WebhookResponse(status_code=401, payload={"ok": False, "error": "invalid webhook secret"})

    token = env.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token and bot_client is None:
        return WebhookResponse(status_code=500, payload={"ok": False, "error": "TELEGRAM_BOT_TOKEN is required"})

    try:
        update = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return WebhookResponse(status_code=400, payload={"ok": False, "error": "invalid Telegram update JSON"})
    if not isinstance(update, dict):
        return WebhookResponse(status_code=400, payload={"ok": False, "error": "Telegram update must be an object"})

    owns_client = bot_client is None
    bot_client = bot_client or TelegramBotClient(token=token)
    try:
        handled = await process_update(update, bot_client=bot_client, env=env)
    finally:
        if owns_client:
            await bot_client.close()

    return WebhookResponse(status_code=200, payload={"ok": True, "handled": handled})


def handle_telegram_webhook(
    body: bytes,
    headers: Optional[dict] = None,
    env: Optional[dict] = None,
    bot_client: Optional[TelegramBotClient] = None,
) -> WebhookResponse:
    """Synchronous wrapper for serverless function adapters and tests."""
    return asyncio.run(
        handle_telegram_webhook_async(
            body=body,
            headers=headers,
            env=env,
            bot_client=bot_client,
        )
    )
