"""Tests for agent.notify_discord — Discord webhook notification module."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from agent.notify_discord import (
    _resolve_webhook_url,
    send_discord_message,
    send_discord_alert,
    send_discord_digest,
    send_discord_margin_result,
    COLOR_PROFIT,
    COLOR_LOSS,
    COLOR_INFO,
)


# ---------------------------------------------------------------------------
# _resolve_webhook_url tests
# ---------------------------------------------------------------------------


class TestResolveWebhookUrl:
    """Tests for webhook URL resolution."""

    def test_resolve_from_arg(self):
        url = _resolve_webhook_url(webhook_url="https://discord.com/api/webhooks/123/abc")
        assert url == "https://discord.com/api/webhooks/123/abc"

    def test_resolve_from_env(self):
        env = {"DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/456/def"}
        url = _resolve_webhook_url(env=env)
        assert url == "https://discord.com/api/webhooks/456/def"

    def test_arg_overrides_env(self):
        env = {"DISCORD_WEBHOOK_URL": "https://discord.com/env"}
        url = _resolve_webhook_url(webhook_url="https://discord.com/arg", env=env)
        assert url == "https://discord.com/arg"

    def test_missing_url_raises(self):
        with pytest.raises(ValueError, match="webhook URL is required"):
            _resolve_webhook_url(env={})


# ---------------------------------------------------------------------------
# send_discord_message tests
# ---------------------------------------------------------------------------


class TestSendDiscordMessage:
    """Tests for simple message sending."""

    @patch("agent.notify_discord._post_webhook")
    def test_send_simple_message(self, mock_post):
        mock_post.return_value = {"ok": True}

        result = send_discord_message(
            "Hello DropAgent!",
            webhook_url="https://discord.com/api/webhooks/test",
        )

        mock_post.assert_called_once()
        payload = mock_post.call_args[0][1]
        assert payload["content"] == "Hello DropAgent!"
        assert payload["username"] == "DropAgent"
        assert result["ok"] is True

    @patch("agent.notify_discord._post_webhook")
    def test_custom_username(self, mock_post):
        mock_post.return_value = {"ok": True}

        send_discord_message(
            "Test",
            webhook_url="https://discord.com/api/webhooks/test",
            username="CustomBot",
        )

        payload = mock_post.call_args[0][1]
        assert payload["username"] == "CustomBot"


# ---------------------------------------------------------------------------
# send_discord_alert tests
# ---------------------------------------------------------------------------


class TestSendDiscordAlert:
    """Tests for rich embed alerts."""

    @patch("agent.notify_discord._post_webhook")
    def test_alert_with_fields(self, mock_post):
        mock_post.return_value = {"ok": True}

        send_discord_alert(
            "High Margin Product!",
            description="AirPods Pro found at great price",
            fields={"Buy": "$25.00", "Sell": "$49.99", "Profit": "$15.74"},
            color=COLOR_PROFIT,
            webhook_url="https://discord.com/api/webhooks/test",
        )

        payload = mock_post.call_args[0][1]
        embed = payload["embeds"][0]
        assert embed["title"] == "High Margin Product!"
        assert embed["description"] == "AirPods Pro found at great price"
        assert embed["color"] == COLOR_PROFIT
        assert len(embed["fields"]) == 3
        assert embed["fields"][0]["name"] == "Buy"
        assert embed["fields"][0]["value"] == "$25.00"

    @patch("agent.notify_discord._post_webhook")
    def test_alert_without_fields(self, mock_post):
        mock_post.return_value = {"ok": True}

        send_discord_alert(
            "Simple Alert",
            webhook_url="https://discord.com/api/webhooks/test",
        )

        payload = mock_post.call_args[0][1]
        embed = payload["embeds"][0]
        assert embed["title"] == "Simple Alert"
        assert "fields" not in embed
        assert embed["color"] == COLOR_INFO

    @patch("agent.notify_discord._post_webhook")
    def test_alert_has_timestamp_and_footer(self, mock_post):
        mock_post.return_value = {"ok": True}

        send_discord_alert(
            "Test",
            webhook_url="https://discord.com/api/webhooks/test",
        )

        embed = mock_post.call_args[0][1]["embeds"][0]
        assert "timestamp" in embed
        assert embed["footer"]["text"] == "DropAgent"


# ---------------------------------------------------------------------------
# send_discord_digest tests
# ---------------------------------------------------------------------------


class TestSendDiscordDigest:
    """Tests for digest summary embeds."""

    @patch("agent.notify_discord._post_webhook")
    def test_digest_with_opportunities(self, mock_post):
        mock_post.return_value = {"ok": True}

        opps = [
            {"query": "airpods", "net_profit": 15.0, "margin_percent": 30.0},
            {"query": "mouse", "net_profit": 8.5, "margin_percent": 22.0},
        ]

        send_discord_digest(
            opps,
            webhook_url="https://discord.com/api/webhooks/test",
        )

        payload = mock_post.call_args[0][1]
        embed = payload["embeds"][0]
        assert "airpods" in embed["description"]
        assert "mouse" in embed["description"]
        assert embed["color"] == COLOR_PROFIT
        assert embed["fields"][0]["value"] == "2"  # Products count
        assert embed["fields"][1]["value"] == "$15.00"  # Best profit

    @patch("agent.notify_discord._post_webhook")
    def test_digest_empty_sends_plain_message(self, mock_post):
        mock_post.return_value = {"ok": True}

        send_discord_digest(
            [],
            webhook_url="https://discord.com/api/webhooks/test",
        )

        payload = mock_post.call_args[0][1]
        assert "No profitable opportunities" in payload["content"]
        assert "embeds" not in payload

    @patch("agent.notify_discord._post_webhook")
    def test_digest_truncates_at_10(self, mock_post):
        mock_post.return_value = {"ok": True}

        opps = [
            {"query": f"product_{i}", "net_profit": float(i), "margin_percent": 10.0}
            for i in range(15)
        ]

        send_discord_digest(
            opps,
            webhook_url="https://discord.com/api/webhooks/test",
        )

        embed = mock_post.call_args[0][1]["embeds"][0]
        assert "...and 5 more" in embed["description"]


# ---------------------------------------------------------------------------
# send_discord_margin_result tests
# ---------------------------------------------------------------------------


class TestSendDiscordMarginResult:
    """Tests for margin result embeds."""

    @patch("agent.notify_discord._post_webhook")
    def test_profitable_result(self, mock_post):
        mock_post.return_value = {"ok": True}

        result = {
            "buy_price": 25.0, "sell_price": 49.99, "net_profit": 14.74,
            "margin_percent": 29.48, "roi_percent": 58.96, "markup": 2.0,
            "total_fees": 8.25, "platform": "ebay", "is_profitable": True,
        }

        send_discord_margin_result(
            result,
            webhook_url="https://discord.com/api/webhooks/test",
        )

        embed = mock_post.call_args[0][1]["embeds"][0]
        assert "PROFIT" in embed["title"]
        assert embed["color"] == COLOR_PROFIT

    @patch("agent.notify_discord._post_webhook")
    def test_loss_result(self, mock_post):
        mock_post.return_value = {"ok": True}

        result = {
            "buy_price": 50.0, "sell_price": 30.0, "net_profit": -28.0,
            "margin_percent": -93.33, "roi_percent": -56.0, "markup": 0.6,
            "total_fees": 8.0, "platform": "ebay", "is_profitable": False,
        }

        send_discord_margin_result(
            result,
            webhook_url="https://discord.com/api/webhooks/test",
        )

        embed = mock_post.call_args[0][1]["embeds"][0]
        assert "LOSS" in embed["title"]
        assert embed["color"] == COLOR_LOSS
