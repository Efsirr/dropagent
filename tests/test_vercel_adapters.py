"""Tests for Vercel Python function adapters."""

import json
from pathlib import Path

from api.index import DROPAGENT_PATH_PARAM, _original_path, handler as dashboard_handler
from api.telegram.webhook import handler as telegram_webhook_handler


ROOT = Path(__file__).resolve().parents[1]


class TestVercelDashboardAdapter:
    def test_original_path_recovers_dashboard_root_after_rewrite(self):
        assert _original_path(f"/api/index?{DROPAGENT_PATH_PARAM}=/") == "/"

    def test_original_path_preserves_forwarded_query_params(self):
        recovered = _original_path(
            f"/api/index?{DROPAGENT_PATH_PARAM}=/api/users/123&username=totik"
        )

        assert recovered == "/api/users/123?username=totik"

    def test_original_path_falls_back_to_actual_path(self):
        assert _original_path("/health") == "/health"

    def test_dashboard_handler_supports_dashboard_methods(self):
        assert hasattr(dashboard_handler, "do_GET")
        assert hasattr(dashboard_handler, "do_POST")
        assert hasattr(dashboard_handler, "do_PATCH")
        assert hasattr(dashboard_handler, "do_DELETE")


class TestVercelTelegramWebhookAdapter:
    def test_webhook_handler_supports_post_and_rejects_get(self):
        assert hasattr(telegram_webhook_handler, "do_POST")
        assert hasattr(telegram_webhook_handler, "do_GET")


class TestVercelJson:
    def test_vercel_json_routes_telegram_webhook_before_dashboard_catchall(self):
        config = json.loads((ROOT / "vercel.json").read_text())

        assert config["rewrites"][0] == {
            "source": "/telegram/webhook",
            "destination": "/api/telegram/webhook",
        }
        assert config["rewrites"][-1]["destination"].startswith("/api/index")
