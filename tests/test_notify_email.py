"""Tests for agent.notify_email — Email notification module."""

from __future__ import annotations

from unittest.mock import patch, MagicMock, ANY

import pytest

from agent.notify_email import (
    _resolve_smtp_config,
    send_email,
    send_alert_email,
    send_digest_email,
    send_margin_email,
    _escape,
)


# ---------------------------------------------------------------------------
# _resolve_smtp_config tests
# ---------------------------------------------------------------------------


class TestResolveSmtpConfig:
    """Tests for SMTP config resolution."""

    def test_resolve_from_env(self):
        env = {
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@gmail.com",
            "SMTP_PASSWORD": "secret",
            "SMTP_FROM": "noreply@example.com",
            "SMTP_TO": "admin@example.com",
        }
        config = _resolve_smtp_config(env=env)
        assert config["host"] == "smtp.gmail.com"
        assert config["port"] == 587
        assert config["user"] == "user@gmail.com"
        assert config["password"] == "secret"
        assert config["from_addr"] == "noreply@example.com"
        assert config["to_addr"] == "admin@example.com"

    def test_from_addr_defaults_to_user(self):
        env = {
            "SMTP_HOST": "smtp.test.com",
            "SMTP_USER": "user@test.com",
            "SMTP_PASSWORD": "pass",
            "SMTP_TO": "admin@test.com",
        }
        config = _resolve_smtp_config(env=env)
        assert config["from_addr"] == "user@test.com"

    def test_overrides_take_precedence(self):
        env = {
            "SMTP_HOST": "smtp.env.com",
            "SMTP_USER": "env@test.com",
            "SMTP_PASSWORD": "env_pass",
            "SMTP_TO": "env_to@test.com",
        }
        config = _resolve_smtp_config(
            env=env,
            host="smtp.override.com",
            to_addr="override@test.com",
        )
        assert config["host"] == "smtp.override.com"
        assert config["to_addr"] == "override@test.com"

    def test_missing_host_raises(self):
        env = {"SMTP_USER": "u", "SMTP_PASSWORD": "p", "SMTP_TO": "t"}
        with pytest.raises(ValueError, match="SMTP host is required"):
            _resolve_smtp_config(env=env)

    def test_missing_credentials_raises(self):
        env = {"SMTP_HOST": "smtp.test.com", "SMTP_TO": "t"}
        with pytest.raises(ValueError, match="SMTP credentials are required"):
            _resolve_smtp_config(env=env)

    def test_missing_recipient_raises(self):
        env = {
            "SMTP_HOST": "smtp.test.com",
            "SMTP_USER": "u",
            "SMTP_PASSWORD": "p",
        }
        with pytest.raises(ValueError, match="Recipient email is required"):
            _resolve_smtp_config(env=env)

    def test_default_port(self):
        env = {
            "SMTP_HOST": "smtp.test.com",
            "SMTP_USER": "u",
            "SMTP_PASSWORD": "p",
            "SMTP_TO": "t",
        }
        config = _resolve_smtp_config(env=env)
        assert config["port"] == 587


# ---------------------------------------------------------------------------
# send_email tests
# ---------------------------------------------------------------------------


_VALID_ENV = {
    "SMTP_HOST": "smtp.test.com",
    "SMTP_PORT": "587",
    "SMTP_USER": "sender@test.com",
    "SMTP_PASSWORD": "testpass",
    "SMTP_TO": "recipient@test.com",
}


class TestSendEmail:
    """Tests for the core send_email function."""

    @patch("agent.notify_email.smtplib.SMTP")
    def test_send_plain_text(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        result = send_email("Test Subject", "Test body", env=_VALID_ENV)

        assert result["ok"] is True
        assert result["to"] == "recipient@test.com"
        assert result["subject"] == "Test Subject"
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("sender@test.com", "testpass")
        mock_server.send_message.assert_called_once()

    @patch("agent.notify_email.smtplib.SMTP")
    def test_send_html_email(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        result = send_email(
            "HTML Test", "Plain fallback", "<h1>Hello</h1>", env=_VALID_ENV
        )

        assert result["ok"] is True
        # Verify message was sent
        sent_msg = mock_server.send_message.call_args[0][0]
        assert sent_msg["Subject"] == "HTML Test"

    @patch("agent.notify_email.smtplib.SMTP")
    def test_to_addr_override(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        result = send_email(
            "Test", "Body",
            to_addr="override@test.com",
            env=_VALID_ENV,
        )

        assert result["to"] == "override@test.com"


# ---------------------------------------------------------------------------
# Formatted sender tests
# ---------------------------------------------------------------------------


class TestSendAlertEmail:
    """Tests for send_alert_email."""

    @patch("agent.notify_email.smtplib.SMTP")
    def test_alert_includes_title(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        result = send_alert_email(
            "Price Drop!", "AirPods now $20 cheaper", env=_VALID_ENV
        )
        assert result["ok"] is True
        assert "[DropAgent] Price Drop!" in result["subject"]


class TestSendDigestEmail:
    """Tests for send_digest_email."""

    @patch("agent.notify_email.smtplib.SMTP")
    def test_digest_with_opportunities(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        opps = [
            {"query": "airpods", "buy_price": 25, "sell_price": 50,
             "net_profit": 15, "margin_percent": 30},
        ]
        result = send_digest_email(opps, env=_VALID_ENV)
        assert result["ok"] is True

    @patch("agent.notify_email.smtplib.SMTP")
    def test_digest_empty(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        result = send_digest_email([], env=_VALID_ENV)
        assert result["ok"] is True

    @patch("agent.notify_email.smtplib.SMTP")
    def test_digest_truncates_at_20(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        opps = [
            {"query": f"product_{i}", "buy_price": 10, "sell_price": 20,
             "net_profit": 5, "margin_percent": 25}
            for i in range(25)
        ]
        result = send_digest_email(opps, env=_VALID_ENV)
        assert result["ok"] is True


class TestSendMarginEmail:
    """Tests for send_margin_email."""

    @patch("agent.notify_email.smtplib.SMTP")
    def test_profitable_margin(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        result_data = {
            "buy_price": 25, "sell_price": 50, "net_profit": 14.74,
            "margin_percent": 29.48, "roi_percent": 58.96, "markup": 2.0,
            "total_fees": 8.25, "platform": "ebay", "is_profitable": True,
        }
        result = send_margin_email(result_data, env=_VALID_ENV)
        assert result["ok"] is True
        assert "PROFIT" in result["subject"]

    @patch("agent.notify_email.smtplib.SMTP")
    def test_loss_margin(self, mock_smtp_class):
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        result_data = {
            "buy_price": 50, "sell_price": 30, "net_profit": -28,
            "margin_percent": -93.33, "roi_percent": -56, "markup": 0.6,
            "total_fees": 8.0, "platform": "ebay", "is_profitable": False,
        }
        result = send_margin_email(result_data, env=_VALID_ENV)
        assert result["ok"] is True
        assert "LOSS" in result["subject"]


# ---------------------------------------------------------------------------
# _escape tests
# ---------------------------------------------------------------------------


class TestEscape:
    """Tests for HTML escaping helper."""

    def test_escape_special_chars(self):
        assert _escape("<script>alert('xss')</script>") == (
            "&lt;script&gt;alert('xss')&lt;/script&gt;"
        )

    def test_escape_ampersand(self):
        assert _escape("A & B") == "A &amp; B"

    def test_escape_quotes(self):
        assert _escape('"hello"') == "&quot;hello&quot;"
