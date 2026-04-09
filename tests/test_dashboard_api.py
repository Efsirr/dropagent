"""Tests for the dashboard backend API router."""

import json

from dashboard.backend.api import handle_api_request


class TestDashboardAPI:
    def test_health_endpoint(self):
        response = handle_api_request("GET", "/health")

        assert response.status_code == 200
        assert response.payload == {"status": "ok"}

    def test_calc_endpoint(self):
        response = handle_api_request(
            "POST",
            "/api/calc",
            body=json.dumps({"buy_price": 25.0, "sell_price": 49.99}).encode("utf-8"),
        )

        assert response.status_code == 200
        assert response.payload["buy_price"] == 25.0
        assert "summary" in response.payload

    def test_calc_endpoint_validates_required_fields(self):
        response = handle_api_request(
            "POST",
            "/api/calc",
            body=json.dumps({"buy_price": 25.0}).encode("utf-8"),
        )

        assert response.status_code == 400
        assert response.payload["error"] == "buy_price and sell_price are required"

    def test_user_profile_settings_and_tracked_queries_flow(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'api.db'}"}

        response = handle_api_request(
            "GET",
            "/api/users/123?username=totik&preferred_language=ru",
            env=env,
        )
        assert response.status_code == 200
        assert response.payload["telegram_chat_id"] == "123"
        assert response.payload["preferred_language"] == "ru"

        response = handle_api_request(
            "PATCH",
            "/api/users/123/settings",
            body=json.dumps(
                {
                    "min_profit_threshold": 19.0,
                    "max_buy_price": 80.0,
                    "enabled_sources": ["amazon"],
                }
            ).encode("utf-8"),
            env=env,
        )
        assert response.status_code == 200
        assert response.payload["min_profit_threshold"] == 19.0
        assert response.payload["enabled_sources"] == ["amazon"]

        response = handle_api_request(
            "POST",
            "/api/users/123/tracked-queries",
            body=json.dumps({"query": "airpods pro"}).encode("utf-8"),
            env=env,
        )
        assert response.status_code == 201
        assert response.payload["tracked_queries"][0]["query"] == "airpods pro"

        response = handle_api_request(
            "GET",
            "/api/users/123/tracked-queries",
            env=env,
        )
        assert response.status_code == 200
        assert response.payload["tracked_queries"][0]["query"] == "airpods pro"

        response = handle_api_request(
            "DELETE",
            "/api/users/123/tracked-queries/airpods%20pro",
            env=env,
        )
        assert response.status_code == 200
        assert response.payload["tracked_queries"] == []

    def test_schedule_endpoint(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'api.db'}"}
        handle_api_request("GET", "/api/users/777", env=env)

        response = handle_api_request(
            "PATCH",
            "/api/users/777/schedule",
            body=json.dumps({"interval_days": 7, "enabled": True}).encode("utf-8"),
            env=env,
        )

        assert response.status_code == 200
        assert response.payload["digest_enabled"] is True
        assert response.payload["digest_interval_days"] == 7

    def test_saved_digest_preview_endpoint(self, monkeypatch, tmp_path):
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'api.db'}",
            "EBAY_APP_ID": "test",
        }
        handle_api_request("GET", "/api/users/444", env=env)
        handle_api_request(
            "POST",
            "/api/users/444/tracked-queries",
            body=json.dumps({"query": "airpods pro"}).encode("utf-8"),
            env=env,
        )

        async def fake_generate_saved_digest_payload(
            telegram_chat_id,
            env,
            top=10,
            limit=20,
            title=None,
        ):
            assert telegram_chat_id == "444"
            assert top == 5
            assert title == "Preview"
            return {"summary": "saved preview"}

        monkeypatch.setattr(
            "dashboard.backend.api.generate_saved_digest_payload",
            fake_generate_saved_digest_payload,
        )

        response = handle_api_request(
            "POST",
            "/api/users/444/digest-preview",
            body=json.dumps({"top": 5, "title": "Preview"}).encode("utf-8"),
            env=env,
        )

        assert response.status_code == 200
        assert response.payload == {"summary": "saved preview"}

    def test_digest_preview_endpoint_requires_queries(self):
        response = handle_api_request(
            "POST",
            "/api/digest-preview",
            body=json.dumps({}).encode("utf-8"),
            env={"EBAY_APP_ID": "test"},
        )

        assert response.status_code == 400
        assert response.payload["error"] == "queries are required"

    def test_invalid_json_returns_400(self):
        response = handle_api_request(
            "POST",
            "/api/calc",
            body=b"{not-json",
        )

        assert response.status_code == 400
        assert response.payload["error"] == "Invalid JSON body"

    def test_unknown_route_returns_404(self):
        response = handle_api_request("GET", "/api/nope")

        assert response.status_code == 404
        assert response.payload["error"] == "Not found"
