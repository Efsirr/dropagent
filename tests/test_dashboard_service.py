"""Tests for dashboard backend service helpers."""

import asyncio

from dashboard.backend.service import (
    add_tracked_query_payload,
    calculate_margin_payload,
    generate_digest_payload,
    generate_saved_digest_payload,
    get_user_profile_payload,
    list_tracked_queries_payload,
    remove_tracked_query_payload,
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

        updated = update_user_settings_payload(
            telegram_chat_id="999",
            env=env,
            min_profit_threshold=18.0,
            max_buy_price=120.0,
            enabled_sources=["walmart"],
        )
        assert updated["min_profit_threshold"] == 18.0
        assert updated["max_buy_price"] == 120.0
        assert updated["enabled_sources"] == ["walmart"]

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


class TestGenerateDigestPayload:
    def test_returns_summary_payload(self, monkeypatch):
        async def fake_run_digest(args, env=None):
            del args, env
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

        async def fake_generate_digest_payload(
            queries,
            env,
            sources=None,
            top=10,
            min_profit=5.0,
            max_buy_price=None,
            limit=20,
            title=None,
        ):
            captured["queries"] = queries
            captured["sources"] = sources
            captured["min_profit"] = min_profit
            captured["max_buy_price"] = max_buy_price
            captured["title"] = title
            return {"summary": "saved digest"}

        monkeypatch.setattr(
            "dashboard.backend.service.generate_digest_payload",
            fake_generate_digest_payload,
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
