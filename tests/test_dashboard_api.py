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
        assert "setup_status" in response.payload
        assert "capabilities" in response.payload
        assert "next_step" in response.payload

        response = handle_api_request(
            "PATCH",
            "/api/users/123/settings",
            body=json.dumps(
                {
                    "business_model": "china_dropshipping",
                    "min_profit_threshold": 19.0,
                    "max_buy_price": 80.0,
                    "enabled_sources": ["aliexpress", "cj"],
                    "selected_integrations": ["aliexpress", "cj", "storeleads"],
                    "alert_preferences": ["watchlist"],
                    "onboarding_completed": True,
                }
            ).encode("utf-8"),
            env=env,
        )
        assert response.status_code == 200
        assert response.payload["min_profit_threshold"] == 19.0
        assert response.payload["business_model"] == "china_dropshipping"
        assert response.payload["enabled_sources"] == ["aliexpress", "cj"]
        assert response.payload["selected_integrations"] == ["aliexpress", "cj", "storeleads"]
        assert response.payload["alert_preferences"] == ["watchlist"]
        assert response.payload["onboarding_completed"] is True
        assert "дайджест" in response.payload["next_step"].lower()

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

    def test_user_integration_secret_flow(self, tmp_path):
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'api.db'}",
            "APP_SECRET_KEY": "dev-secret-with-enough-length",
        }
        handle_api_request("GET", "/api/users/123", env=env)

        response = handle_api_request(
            "PUT",
            "/api/users/123/integrations/keepa/secret",
            body=json.dumps({"api_key": "keepa-api-key-123"}).encode("utf-8"),
            env=env,
        )

        assert response.status_code == 200
        assert response.payload["integration_id"] == "keepa"
        assert response.payload["configured"] is True
        assert response.payload["secret_hint"] == "keepa-...-123"
        assert "api_key" not in response.payload
        assert "encrypted_secret" not in response.payload

        response = handle_api_request(
            "GET",
            "/api/users/123/integrations",
            env=env,
        )
        assert response.status_code == 200
        assert response.payload["integrations"][0]["integration_id"] == "keepa"
        assert "keepa-api-key-123" not in json.dumps(response.payload)

        response = handle_api_request(
            "DELETE",
            "/api/users/123/integrations/keepa/secret",
            env=env,
        )
        assert response.status_code == 200
        assert response.payload["integrations"] == []

    def test_user_integration_secret_requires_app_secret(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'api.db'}"}

        response = handle_api_request(
            "PUT",
            "/api/users/123/integrations/keepa/secret",
            body=json.dumps({"api_key": "keepa-api-key-123"}).encode("utf-8"),
            env=env,
        )

        assert response.status_code == 400
        assert "APP_SECRET_KEY" in response.payload["error"]

    def test_watchlist_endpoints(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'api.db'}"}
        handle_api_request("GET", "/api/users/888", env=env)

        response = handle_api_request(
            "POST",
            "/api/users/888/watchlist",
            body=json.dumps(
                {
                    "product_name": "AirPods Pro 2",
                    "source": "amazon",
                    "current_buy_price": 79.99,
                }
            ).encode("utf-8"),
            env=env,
        )
        assert response.status_code == 201
        item_id = response.payload["item_id"]
        assert response.payload["product_name"] == "AirPods Pro 2"

        response = handle_api_request(
            "GET",
            "/api/users/888/watchlist",
            env=env,
        )
        assert response.status_code == 200
        assert response.payload["watchlist_items"][0]["item_id"] == item_id

        response = handle_api_request(
            "POST",
            f"/api/users/888/watchlist/{item_id}/history",
            body=json.dumps({"buy_price": 74.5, "sell_price": 118.0}).encode("utf-8"),
            env=env,
        )
        assert response.status_code == 201
        assert response.payload["current_sell_price"] == 118.0

        response = handle_api_request(
            "GET",
            f"/api/users/888/watchlist/{item_id}/history",
            env=env,
        )
        assert response.status_code == 200
        assert len(response.payload["price_history"]) == 2

        response = handle_api_request(
            "DELETE",
            f"/api/users/888/watchlist/{item_id}",
            env=env,
        )
        assert response.status_code == 200
        assert response.payload["watchlist_items"] == []

    def test_competitor_endpoints(self, monkeypatch, tmp_path):
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'api.db'}",
            "EBAY_APP_ID": "test",
        }
        handle_api_request("GET", "/api/users/333", env=env)

        response = handle_api_request(
            "POST",
            "/api/users/333/competitors",
            body=json.dumps({"seller_username": "best_seller_usa"}).encode("utf-8"),
            env=env,
        )
        assert response.status_code == 201
        competitor_id = response.payload["competitor_id"]

        response = handle_api_request("GET", "/api/users/333/competitors", env=env)
        assert response.status_code == 200
        assert response.payload["tracked_competitors"][0]["seller_username"] == "best_seller_usa"

        async def fake_scan_tracked_competitor_payload(
            telegram_chat_id,
            competitor_id,
            env,
            query=None,
            limit=25,
        ):
            del env, query, limit
            assert telegram_chat_id == "333"
            assert competitor_id == competitor_id
            return {"summary": "competitor scan", "new_count": 1}

        monkeypatch.setattr(
            "dashboard.backend.api.scan_tracked_competitor_payload",
            fake_scan_tracked_competitor_payload,
        )

        response = handle_api_request(
            "POST",
            f"/api/users/333/competitors/{competitor_id}/scan",
            body=json.dumps({}).encode("utf-8"),
            env=env,
        )
        assert response.status_code == 200
        assert response.payload["new_count"] == 1

        response = handle_api_request(
            "DELETE",
            f"/api/users/333/competitors/{competitor_id}",
            env=env,
        )
        assert response.status_code == 200
        assert response.payload["tracked_competitors"] == []

    def test_store_discovery_endpoint(self, monkeypatch, tmp_path):
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'api.db'}",
            "APP_SECRET_KEY": "dev-secret-with-enough-length",
        }

        async def fake_discovery(telegram_chat_id, query, env, country=None, platform="shopify", limit=5):
            assert telegram_chat_id == "333"
            assert query == "pet accessories"
            assert platform == "shopify"
            return {
                "count": 1,
                "stores": [{"domain": "petjoy.example"}],
                "summary": "STORE DISCOVERY",
            }

        monkeypatch.setattr(
            "dashboard.backend.api.discover_competitor_stores_payload",
            fake_discovery,
        )

        response = handle_api_request(
            "POST",
            "/api/users/333/store-discovery",
            body=json.dumps({"query": "pet accessories"}).encode("utf-8"),
            env=env,
        )

        assert response.status_code == 200
        assert response.payload["count"] == 1
        assert response.payload["stores"][0]["domain"] == "petjoy.example"

    def test_store_lead_endpoints(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'api.db'}"}
        handle_api_request("GET", "/api/users/333", env=env)

        response = handle_api_request(
            "POST",
            "/api/users/333/store-leads",
            body=json.dumps(
                {
                    "domain": "petjoy.example",
                    "merchant_name": "Pet Joy",
                    "niche_query": "pet accessories",
                    "estimated_visits": 120000,
                }
            ).encode("utf-8"),
            env=env,
        )
        assert response.status_code == 201
        store_lead_id = response.payload["store_lead_id"]

        response = handle_api_request("GET", "/api/users/333/store-leads", env=env)
        assert response.status_code == 200
        assert response.payload["saved_store_leads"][0]["domain"] == "petjoy.example"

        response = handle_api_request(
            "DELETE",
            f"/api/users/333/store-leads/{store_lead_id}",
            env=env,
        )
        assert response.status_code == 200
        assert response.payload["saved_store_leads"] == []

    def test_ad_discovery_endpoint(self, monkeypatch, tmp_path):
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'api.db'}",
            "APP_SECRET_KEY": "dev-secret-with-enough-length",
        }

        async def fake_discovery(telegram_chat_id, query, env, country=None, limit=5):
            assert telegram_chat_id == "333"
            assert query == "pet hair remover"
            return {
                "count": 1,
                "ads": [{"ad_id": "1"}],
                "summary": "AD DISCOVERY",
            }

        monkeypatch.setattr(
            "dashboard.backend.api.discover_trending_ads_payload",
            fake_discovery,
        )

        response = handle_api_request(
            "POST",
            "/api/users/333/ad-discovery",
            body=json.dumps({"query": "pet hair remover"}).encode("utf-8"),
            env=env,
        )

        assert response.status_code == 200
        assert response.payload["count"] == 1
        assert response.payload["ads"][0]["ad_id"] == "1"

    def test_discovery_hub_endpoint(self, monkeypatch, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'api.db'}"}

        async def fake_hub(telegram_chat_id, query, env, country=None, limit=5):
            assert telegram_chat_id == "333"
            assert query == "pet accessories"
            return {
                "query": "pet accessories",
                "store_report": {"count": 1},
                "ad_report": {"count": 1},
                "trend_report": {"category": "pet accessories"},
                "recent_runs": [{"query": "pet accessories"}],
            }

        monkeypatch.setattr(
            "dashboard.backend.api.generate_discovery_hub_payload",
            fake_hub,
        )

        response = handle_api_request(
            "POST",
            "/api/users/333/discovery-hub",
            body=json.dumps({"query": "pet accessories"}).encode("utf-8"),
            env=env,
        )

        assert response.status_code == 200
        assert response.payload["query"] == "pet accessories"
        assert response.payload["store_report"]["count"] == 1
        assert response.payload["recent_runs"][0]["query"] == "pet accessories"

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

    def test_weekly_report_preview_endpoint_requires_categories(self):
        response = handle_api_request(
            "POST",
            "/api/weekly-report-preview",
            body=json.dumps({}).encode("utf-8"),
            env={"EBAY_APP_ID": "test"},
        )

        assert response.status_code == 400
        assert response.payload["error"] == "categories are required"

    def test_weekly_report_preview_endpoint(self, monkeypatch):
        async def fake_generate_weekly_report_payload(
            categories,
            env,
            sources=None,
            top_products=5,
            trend_limit=5,
            query_limit=10,
            title=None,
        ):
            del env
            assert categories == ["electronics"]
            assert sources == ["amazon"]
            assert title == "Weekly Winners"
            return {"summary": "weekly preview"}

        monkeypatch.setattr(
            "dashboard.backend.api.generate_weekly_report_payload",
            fake_generate_weekly_report_payload,
        )

        response = handle_api_request(
            "POST",
            "/api/weekly-report-preview",
            body=json.dumps(
                {
                    "categories": ["electronics"],
                    "sources": ["amazon"],
                    "title": "Weekly Winners",
                }
            ).encode("utf-8"),
            env={"EBAY_APP_ID": "test"},
        )

        assert response.status_code == 200
        assert response.payload == {"summary": "weekly preview"}

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
