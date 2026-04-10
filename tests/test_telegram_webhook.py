"""Tests for Telegram webhook hosting adapter."""

import json

from bot.webhook import handle_telegram_webhook, verify_webhook_secret


class FakeWebhookBotClient:
    def __init__(self):
        self.sent_messages = []
        self.closed = False

    async def send_message(self, chat_id, text, reply_markup=None):
        self.sent_messages.append((chat_id, text, reply_markup))
        return {"chat": {"id": chat_id}, "text": text}

    async def answer_callback_query(self, callback_query_id, text=None):
        return True

    async def close(self):
        self.closed = True


class TestTelegramWebhook:
    def test_verify_webhook_secret_is_optional(self):
        assert verify_webhook_secret(headers={}, env={}) is True

    def test_verify_webhook_secret_checks_header_case_insensitively(self):
        env = {"TELEGRAM_WEBHOOK_SECRET": "secret"}

        assert verify_webhook_secret(
            headers={"X-Telegram-Bot-Api-Secret-Token": "secret"},
            env=env,
        ) is True
        assert verify_webhook_secret(
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
            env=env,
        ) is False

    def test_webhook_rejects_bad_secret(self):
        response = handle_telegram_webhook(
            body=b"{}",
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
            env={"TELEGRAM_WEBHOOK_SECRET": "secret", "TELEGRAM_BOT_TOKEN": "token"},
        )

        assert response.status_code == 401
        assert response.payload["ok"] is False

    def test_webhook_rejects_invalid_json(self):
        response = handle_telegram_webhook(
            body=b"not-json",
            env={"TELEGRAM_BOT_TOKEN": "token"},
            bot_client=FakeWebhookBotClient(),
        )

        assert response.status_code == 400

    def test_webhook_processes_text_update(self, tmp_path):
        client = FakeWebhookBotClient()
        body = json.dumps(
            {
                "update_id": 1,
                "message": {
                    "chat": {"id": 123},
                    "text": "/status",
                    "from": {"language_code": "en-US", "username": "totik"},
                },
            }
        ).encode("utf-8")

        response = handle_telegram_webhook(
            body=body,
            headers={"X-Telegram-Bot-Api-Secret-Token": "secret"},
            env={
                "DATABASE_URL": f"sqlite:///{tmp_path / 'webhook.db'}",
                "TELEGRAM_WEBHOOK_SECRET": "secret",
            },
            bot_client=client,
        )

        assert response.status_code == 200
        assert response.payload == {"ok": True, "handled": True}
        assert client.sent_messages
        assert client.sent_messages[0][0] == 123
        assert "Current stack status:" in client.sent_messages[0][1]

    def test_webhook_acknowledges_ignored_update(self):
        client = FakeWebhookBotClient()

        response = handle_telegram_webhook(
            body=json.dumps({"update_id": 2}).encode("utf-8"),
            env={"DATABASE_URL": "sqlite:///:memory:"},
            bot_client=client,
        )

        assert response.status_code == 200
        assert response.payload == {"ok": True, "handled": False}
        assert client.sent_messages == []
