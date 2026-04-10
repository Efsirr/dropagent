"""Tests for the thin Vercel Function adapters."""

from __future__ import annotations

import json
from pathlib import Path

from api.index import _original_path


class TestVercelAdapter:
    def test_original_path_recovers_rewritten_dashboard_route(self):
        assert _original_path("/api/index?dropagent_path=/app.js") == "/app.js"

    def test_original_path_recovers_rewritten_api_route_with_query(self):
        path = _original_path(
            "/api/index?dropagent_path=/api/users/123&username=totik&preferred_language=ru"
        )

        assert path == "/api/users/123?username=totik&preferred_language=ru"

    def test_original_path_defaults_to_runtime_path_without_rewrite_param(self):
        assert _original_path("/api/calc") == "/api/calc"

    def test_vercel_config_routes_to_python_adapters(self):
        config = json.loads(Path("vercel.json").read_text(encoding="utf-8"))

        rewrites = config["rewrites"]
        assert rewrites[0] == {
            "source": "/telegram/webhook",
            "destination": "/api/telegram/webhook",
        }
        assert rewrites[1]["destination"].startswith("/api/index?dropagent_path=/api/")
        assert rewrites[2]["destination"].startswith("/api/index?dropagent_path=/")

