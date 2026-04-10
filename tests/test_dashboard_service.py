"""Tests for dashboard backend service helpers."""

import asyncio

from dashboard.backend.service import (
    add_saved_store_lead_payload,
    add_tracked_competitor_payload,
    add_watchlist_item_payload,
    add_watchlist_price_point_payload,
    add_tracked_query_payload,
    calculate_margin_payload,
    discover_competitor_stores_payload,
    discover_trending_ads_payload,
    generate_discovery_hub_payload,
    generate_digest_payload,
    generate_weekly_report_payload,
    generate_saved_digest_payload,
    get_user_profile_payload,
    list_saved_store_leads_payload,
    list_tracked_competitors_payload,
    list_watchlist_history_payload,
    list_watchlist_items_payload,
    list_tracked_queries_payload,
    remove_saved_store_lead_payload,
    remove_tracked_competitor_payload,
    remove_watchlist_item_payload,
    remove_tracked_query_payload,
    scan_tracked_competitor_payload,
    update_digest_schedule_payload,
    update_user_settings_payload,
)


class TestCalculateMarginPayload:
    def test_returns_dict_with_summary(self):
        payload = calculate_margin_payload(
            buy_price=25.0,
            sell_price=49.99,
            shipping_cost=5.0,
            packaging_cost=1.5,
        )

        assert payload["buy_price"] == 25.0
        assert payload["sell_price"] == 49.99
        assert "summary" in payload
        assert "MARGIN CALCULATOR" in payload["summary"]


class TestUserProfilePayloads:
    def test_profile_settings_and_tracked_queries_round_trip(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'dashboard.db'}"}

        profile = get_user_profile_payload(
            telegram_chat_id="999",
            env=env,
            username="totik",
            preferred_language="ru",
        )
        assert profile["telegram_chat_id"] == "999"
        assert profile["preferred_language"] == "ru"
        assert profile["onboarding_completed"] is False
        assert "setup_status" in profile
        assert "capabilities" in profile
        assert "next_step" in profile
        assert "Следующий шаг" not in profile["next_step"]

        updated = update_user_settings_payload(
            telegram_chat_id="999",
            env=env,
            business_model="china_dropshipping",
            min_profit_threshold=18.0,
            max_buy_price=120.0,
            enabled_sources=["aliexpress", "cj"],
            selected_integrations=["aliexpress", "cj", "storeleads"],
            onboarding_completed=True,
        )
        assert updated["min_profit_threshold"] == 18.0
        assert updated["max_buy_price"] == 120.0
        assert updated["business_model"] == "china_dropshipping"
        assert updated["enabled_sources"] == ["aliexpress", "cj"]
        assert updated["selected_integrations"] == ["aliexpress", "cj", "storeleads"]
        assert updated["alert_preferences"] == ["discovery", "watchlist", "competitor"]
        assert updated["onboarding_completed"] is True
        assert "дайджест" in updated["next_step"].lower()

        updated = update_user_settings_payload(
            telegram_chat_id="999",
            env=env,
            alert_preferences=["watchlist"],
        )
        assert updated["alert_preferences"] == ["watchlist"]

        updated = add_tracked_query_payload(
            telegram_chat_id="999",
            query="airpods pro",
            env=env,
            max_buy_price=85.0,
            min_profit_threshold=20.0,
        )
        assert len(updated["tracked_queries"]) == 1
        assert updated["tracked_queries"][0]["query"] == "airpods pro"

        tracked = list_tracked_queries_payload("999", env=env)
        assert tracked["tracked_queries"][0]["max_buy_price"] == 85.0

        updated = remove_tracked_query_payload(
            telegram_chat_id="999",
            query="airpods pro",
            env=env,
        )
        assert updated["tracked_queries"] == []

    def test_update_digest_schedule_payload(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'dashboard.db'}"}
        get_user_profile_payload(telegram_chat_id="555", env=env)

        updated = update_digest_schedule_payload(
            telegram_chat_id="555",
            interval_days=7,
            enabled=True,
            env=env,
        )

        assert updated["digest_enabled"] is True
        assert updated["digest_interval_days"] == 7
        assert updated["next_digest_at"] is not None

    def test_watchlist_payload_round_trip(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'dashboard.db'}"}
        get_user_profile_payload(telegram_chat_id="555", env=env)

        created = add_watchlist_item_payload(
            telegram_chat_id="555",
            product_name="AirPods Pro 2",
            source="amazon",
            env=env,
            current_buy_price=79.99,
        )
        assert created["product_name"] == "AirPods Pro 2"
        assert len(created["price_history"]) == 1

        listed = list_watchlist_items_payload("555", env=env)
        assert listed["watchlist_items"][0]["source"] == "amazon"

        updated = add_watchlist_price_point_payload(
            telegram_chat_id="555",
            item_id=created["item_id"],
            env=env,
            buy_price=74.5,
            sell_price=119.0,
        )
        assert updated["current_buy_price"] == 74.5
        assert len(updated["price_history"]) == 2

        history = list_watchlist_history_payload(
            telegram_chat_id="555",
            item_id=created["item_id"],
            env=env,
        )
        assert history["price_history"][-1]["sell_price"] == 119.0

        remaining = remove_watchlist_item_payload(
            telegram_chat_id="555",
            item_id=created["item_id"],
            env=env,
        )
        assert remaining["watchlist_items"] == []

    def test_competitor_payload_round_trip(self, monkeypatch, tmp_path):
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'dashboard.db'}",
            "EBAY_APP_ID": "test",
        }
        get_user_profile_payload(telegram_chat_id="555", env=env)

        created = add_tracked_competitor_payload(
            telegram_chat_id="555",
            seller_username="best_seller_usa",
            env=env,
        )
        assert created["seller_username"] == "best_seller_usa"

        listed = list_tracked_competitors_payload("555", env=env)
        assert listed["tracked_competitors"][0]["seller_username"] == "best_seller_usa"

        async def fake_scan(session, telegram_chat_id, competitor_id, tracker, query=None, limit=25):
            del session, tracker, query, limit
            assert telegram_chat_id == "555"
            assert competitor_id == created["competitor_id"]
            from agent.competitor import CompetitorItem, CompetitorReport
            from datetime import datetime, timezone

            return CompetitorReport(
                seller_username="best_seller_usa",
                generated_at=datetime.now(timezone.utc),
                items=[
                    CompetitorItem(
                        item_id="X1",
                        title="AirPods Pro 2",
                        sold_price=119.0,
                        sold_date=datetime.now(timezone.utc),
                        category="Headphones",
                        is_new=True,
                    )
                ],
            )

        monkeypatch.setattr("dashboard.backend.service.scan_tracked_competitor", fake_scan)
        scanned = asyncio.run(
            scan_tracked_competitor_payload(
                telegram_chat_id="555",
                competitor_id=created["competitor_id"],
                env=env,
            )
        )
        assert scanned["new_count"] == 1
        assert "summary" in scanned

        remaining = remove_tracked_competitor_payload(
            telegram_chat_id="555",
            competitor_id=created["competitor_id"],
            env=env,
        )
        assert remaining["tracked_competitors"] == []

    def test_store_lead_payload_round_trip(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'dashboard.db'}"}
        get_user_profile_payload(telegram_chat_id="555", env=env)

        created = add_saved_store_lead_payload(
            telegram_chat_id="555",
            domain="petjoy.example",
            merchant_name="Pet Joy",
            niche_query="pet accessories",
            estimated_visits=120000,
            estimated_sales_monthly_usd=45000.0,
            avg_price_usd=32.5,
            env=env,
        )
        assert created["domain"] == "petjoy.example"

        listed = list_saved_store_leads_payload("555", env=env)
        assert listed["saved_store_leads"][0]["merchant_name"] == "Pet Joy"

        remaining = remove_saved_store_lead_payload(
            telegram_chat_id="555",
            store_lead_id=created["store_lead_id"],
            env=env,
        )
        assert remaining["saved_store_leads"] == []


class TestGenerateDigestPayload:
    def test_returns_summary_payload(self, monkeypatch):
        async def fake_run_digest(args, env=None, keepa_adapter=None):
            del args, env, keepa_adapter
            return "digest summary"

        monkeypatch.setattr("dashboard.backend.service.run_digest", fake_run_digest)

        payload = asyncio.run(
            generate_digest_payload(
                queries=["airpods", "mouse"],
                env={"EBAY_APP_ID": "test"},
                sources=["amazon"],
                top=5,
                min_profit=10.0,
                title="Morning Report",
            )
        )

        assert payload == {
            "queries": ["airpods", "mouse"],
            "sources": ["amazon"],
            "summary": "digest summary",
        }

    def test_generate_saved_digest_payload_uses_profile_data(self, monkeypatch, tmp_path):
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'dashboard.db'}",
            "EBAY_APP_ID": "test",
        }
        get_user_profile_payload(telegram_chat_id="123", env=env)
        update_user_settings_payload(
            telegram_chat_id="123",
            env=env,
            min_profit_threshold=22.0,
            max_buy_price=95.0,
            enabled_sources=["amazon"],
        )
        add_tracked_query_payload(
            telegram_chat_id="123",
            query="airpods pro",
            env=env,
        )

        captured = {}
        fake_keepa = object()

        async def fake_generate_digest_payload(
            queries,
            env,
            sources=None,
            top=10,
            min_profit=5.0,
            max_buy_price=None,
            limit=20,
            title=None,
            keepa_adapter=None,
        ):
            captured["queries"] = queries
            captured["sources"] = sources
            captured["min_profit"] = min_profit
            captured["max_buy_price"] = max_buy_price
            captured["title"] = title
            captured["keepa_adapter"] = keepa_adapter
            return {"summary": "saved digest"}

        monkeypatch.setattr(
            "dashboard.backend.service.generate_digest_payload",
            fake_generate_digest_payload,
        )
        monkeypatch.setattr(
            "dashboard.backend.service.get_keepa_adapter_for_user",
            lambda telegram_chat_id, session, app_secret=None: fake_keepa,
        )

        payload = asyncio.run(
            generate_saved_digest_payload(
                telegram_chat_id="123",
                env=env,
                title="Preview",
            )
        )

        assert payload == {"summary": "saved digest"}
        assert captured["queries"] == ["airpods pro"]
        assert captured["sources"] == ["amazon"]
        assert captured["min_profit"] == 22.0
        assert captured["max_buy_price"] == 95.0
        assert captured["title"] == "Preview"
        assert captured["keepa_adapter"] is fake_keepa

    def test_generate_weekly_report_payload(self, monkeypatch):
        async def fake_run_weekly_report(args, env=None):
            del env
            assert args.category == ["electronics", "toys"]
            assert args.source == ["amazon"]
            assert args.title == "Weekly Winners"
            return "weekly summary"

        monkeypatch.setattr("dashboard.backend.service.run_weekly_report", fake_run_weekly_report)

        payload = asyncio.run(
            generate_weekly_report_payload(
                categories=["electronics", "toys"],
                env={"EBAY_APP_ID": "test"},
                sources=["amazon"],
                title="Weekly Winners",
            )
        )

        assert payload == {
            "categories": ["electronics", "toys"],
            "sources": ["amazon"],
            "summary": "weekly summary",
        }

    def test_discover_competitor_stores_payload(self, monkeypatch, tmp_path):
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'dashboard.db'}",
            "APP_SECRET_KEY": "dev-secret-with-enough-length",
        }

        class FakeAdapter:
            async def search_domains(self, **kwargs):
                assert kwargs["platform"] == "shopify"
                assert kwargs["categories"] == "pet accessories"
                return [
                    type(
                        "Domain",
                        (),
                        {
                            "domain": "petjoy.example",
                            "merchant_name": "Pet Joy",
                            "estimated_visits": 120000,
                            "estimated_sales_monthly_usd": 54000.0,
                            "avg_price_usd": 31.5,
                            "to_dict": lambda self: {
                                "domain": "petjoy.example",
                                "merchant_name": "Pet Joy",
                            },
                        },
                    )()
                ]

            async def close(self):
                return None

        monkeypatch.setattr(
            "dashboard.backend.service.get_storeleads_adapter_for_user",
            lambda telegram_chat_id, session, app_secret=None: FakeAdapter(),
        )

        payload = asyncio.run(
            discover_competitor_stores_payload(
                telegram_chat_id="123",
                query="pet accessories",
                env=env,
            )
        )

        assert payload["count"] == 1
        assert payload["stores"][0]["domain"] == "petjoy.example"
        assert "STORE DISCOVERY" in payload["summary"]

    def test_discover_trending_ads_payload(self, monkeypatch, tmp_path):
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'dashboard.db'}",
            "APP_SECRET_KEY": "dev-secret-with-enough-length",
        }

        class FakeAdapter:
            async def search_ads(self, **kwargs):
                assert kwargs["keyword"] == "pet hair remover"
                return type(
                    "AdResult",
                    (),
                    {
                        "ads": [
                            type(
                                "Ad",
                                (),
                                {
                                    "ad_id": "1",
                                    "title": "Pet Hair Remover Roller",
                                    "advertiser": "PetHero",
                                    "total_likes": 12000,
                                    "total_shares": 2100,
                                    "days_running": 7,
                                    "trend_score": 5432.1,
                                    "to_dict": lambda self: {"ad_id": "1", "title": "Pet Hair Remover Roller"},
                                },
                            )()
                        ]
                    },
                )()

            async def close(self):
                return None

        monkeypatch.setattr(
            "dashboard.backend.service.get_pipiads_adapter_for_user",
            lambda telegram_chat_id, session, app_secret=None: FakeAdapter(),
        )

        payload = asyncio.run(
            discover_trending_ads_payload(
                telegram_chat_id="123",
                query="pet hair remover",
                env=env,
            )
        )

        assert payload["count"] == 1
        assert payload["ads"][0]["ad_id"] == "1"
        assert "AD DISCOVERY" in payload["summary"]

    def test_generate_discovery_hub_payload(self, monkeypatch):
        env = {"DATABASE_URL": "sqlite:///:memory:"}

        get_user_profile_payload(telegram_chat_id="123", env=env)
        add_tracked_query_payload(
            telegram_chat_id="123",
            query="pet accessories",
            env=env,
        )

        async def fake_store(*, telegram_chat_id, query, env, country=None, limit=5):
            del telegram_chat_id, env, country, limit
            assert query == "pet accessories"
            return {"summary": "STORE DISCOVERY", "count": 1, "stores": [{"domain": "petjoy.example"}]}

        async def fake_ads(*, telegram_chat_id, query, env, country=None, limit=5):
            del telegram_chat_id, env, country, limit
            assert query == "pet accessories"
            return {"summary": "AD DISCOVERY", "count": 1, "ads": [{"ad_id": "1"}]}

        class FakeScanner:
            def scan_category(self, category, keywords, geo="US", limit=5):
                assert category == "pet accessories"
                assert keywords == ["pet accessories"]
                assert geo == "US"
                return type(
                    "TrendResult",
                    (),
                    {
                        "to_dict": lambda self: {
                            "category": "pet accessories",
                            "keywords": [{"keyword": "pet lint roller", "score": 180.0}],
                        }
                    },
                )()

        monkeypatch.setattr("dashboard.backend.service.discover_competitor_stores_payload", fake_store)
        monkeypatch.setattr("dashboard.backend.service.discover_trending_ads_payload", fake_ads)
        monkeypatch.setattr("dashboard.backend.service.GoogleTrendsScanner", lambda: FakeScanner())

        payload = asyncio.run(
            generate_discovery_hub_payload(
                telegram_chat_id="123",
                query="pet accessories",
                env=env,
            )
        )

        assert payload["query"] == "pet accessories"
        assert payload["store_report"]["count"] == 1
        assert payload["ad_report"]["count"] == 1
        assert payload["trend_report"]["category"] == "pet accessories"
        assert payload["recent_runs"][0]["query"] == "pet accessories"
        assert payload["recent_runs"][0]["store_count"] == 1
        assert payload["generated_alert"] is None

        async def fake_store_stronger(*, telegram_chat_id, query, env, country=None, limit=5):
            del telegram_chat_id, env, country, limit
            return {"summary": "STORE DISCOVERY", "count": 3, "stores": [{"domain": "petjoy.example"}]}

        async def fake_ads_stronger(*, telegram_chat_id, query, env, country=None, limit=5):
            del telegram_chat_id, env, country, limit
            return {"summary": "AD DISCOVERY", "count": 2, "ads": [{"ad_id": "1"}, {"ad_id": "2"}]}

        monkeypatch.setattr("dashboard.backend.service.discover_competitor_stores_payload", fake_store_stronger)
        monkeypatch.setattr("dashboard.backend.service.discover_trending_ads_payload", fake_ads_stronger)

        payload = asyncio.run(
            generate_discovery_hub_payload(
                telegram_chat_id="123",
                query="pet accessories",
                env=env,
            )
        )

        assert payload["generated_alert"]["alert_type"] == "discovery_signal_strength"
        assert payload["recent_alerts"][0]["related_query"] == "pet accessories"
