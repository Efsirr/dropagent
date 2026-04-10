"""Tests for the bot command layer."""

import asyncio

from bot.handlers.calc import handle_calc_command
from bot.handlers.competitor import (
    handle_checkcompetitor_command,
    handle_competitor_command,
    handle_competitors_command,
    handle_uncompetitor_command,
)
from bot.handlers.connect import handle_connect_command, handle_disconnect_command
from bot.handlers.ad_discovery import handle_discoverads_command
from bot.handlers.alerts import handle_alerts_command
from bot.handlers.discovery import handle_discoverstores_command
from bot.handlers.digest import handle_digest_command
from bot.handlers.listing import handle_listing_command
from bot.handlers.settings import (
    handle_language_command,
    handle_maxbuy_command,
    handle_minprofit_command,
    handle_schedule_command,
    handle_settings_command,
    handle_sources_command,
    handle_track_command,
    handle_tracklist_command,
    handle_untrack_command,
)
from bot.handlers.watchlist import (
    handle_pricepoint_command,
    handle_unwatch_command,
    handle_watch_command,
    handle_watchlist_command,
)
from bot.handlers.weekly import handle_weekly_command
from bot.main import (
    BotResponse,
    BotContext,
    _extract_language,
    _extract_text_message,
    _extract_username,
    handle_message,
    main,
    poll_once,
    process_callback_query,
    process_scheduled_digests,
    process_update,
)
from db.service import (
    AlertEventRecord,
    UserProfile,
    get_or_create_user_profile,
    update_user_settings,
)
from db.session import get_database_url, get_session


class TestCalcHandler:
    def test_calc_handler_returns_usage_for_missing_args(self):
        result = handle_calc_command("/calc")

        assert "Usage: /calc" in result

    def test_calc_handler_returns_margin_summary(self):
        result = handle_calc_command("/calc 25 49.99 5 1.5")

        assert "MARGIN CALCULATOR" in result
        assert "$25.00" in result
        assert "$49.99" in result

    def test_calc_handler_handles_invalid_numbers(self):
        result = handle_calc_command("/calc nope 49.99")

        assert "Error: invalid numeric values" == result


class TestListingHandler:
    def test_listing_handler_returns_usage_for_missing_args(self):
        result = handle_listing_command("/listing")

        assert "Usage: /listing" in result

    def test_listing_handler_returns_single_draft(self):
        result = handle_listing_command("/listing airpods pro")

        assert "EBAY LISTING DRAFT" in result
        assert "airpods pro" in result.lower()

    def test_listing_handler_supports_bulk_input(self):
        result = handle_listing_command("/listing airpods pro | gaming mouse")

        assert result.count("EBAY LISTING DRAFT") == 2


class TestDigestHandler:
    def test_digest_handler_supports_shorthand_queries(self):
        captured = {}

        async def fake_runner(args, env=None):
            del env
            captured["args"] = args
            return "digest ok"

        result = asyncio.run(
            handle_digest_command(
                "/digest airpods mouse",
                env={"EBAY_APP_ID": "test"},
                runner=fake_runner,
            )
        )

        assert result == "digest ok"
        assert captured["args"].query == ["airpods", "mouse"]

    def test_digest_handler_reports_value_errors(self):
        async def fake_runner(args, env=None):
            del args, env
            raise ValueError("broken")

        result = asyncio.run(handle_digest_command("/digest", runner=fake_runner))

        assert result == "Error: broken"

    def test_digest_handler_uses_saved_queries_and_settings(self):
        captured = {}

        async def fake_runner(args, env=None):
            del env
            captured["args"] = args
            return "digest ok"

        profile = UserProfile(
            user_id=1,
            telegram_chat_id="123",
            username="totik",
            preferred_language="ru",
            business_model="us_arbitrage",
            min_profit_threshold=17.0,
            max_buy_price=75.0,
            digest_enabled=True,
            digest_interval_days=1,
            next_digest_at=None,
            enabled_sources=["amazon"],
            tracked_queries=[],
        )
        profile.tracked_queries.append(type("Tracked", (), {"query": "airpods pro"})())

        result = asyncio.run(
            handle_digest_command(
                "/digest",
                env={"EBAY_APP_ID": "test"},
                runner=fake_runner,
                user_profile=profile,
            )
        )

        assert result == "digest ok"
        assert captured["args"].query == ["airpods pro"]
        assert captured["args"].min_profit == 17.0
        assert captured["args"].max_buy_price == 75.0
        assert captured["args"].source == ["amazon"]


class TestWeeklyHandler:
    def test_weekly_handler_supports_shorthand_categories(self):
        captured = {}

        async def fake_runner(args, env=None):
            del env
            captured["args"] = args
            return "weekly ok"

        result = asyncio.run(
            handle_weekly_command(
                "/weekly electronics toys",
                env={"EBAY_APP_ID": "test"},
                runner=fake_runner,
            )
        )

        assert result == "weekly ok"
        assert captured["args"].category == ["electronics", "toys"]


class TestCompetitorHandlers:
    def test_competitor_handler_saves_seller(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        result = handle_competitor_command("/competitor best_seller_usa", env=env, user_profile=profile)

        assert 'Tracked competitor saved: #1 "best_seller_usa"' in result

    def test_competitors_handler_lists_saved_sellers(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        handle_competitor_command("/competitor best_seller_usa", env=env, user_profile=profile)
        result = handle_competitors_command(env=env, user_profile=profile)

        assert "Tracked competitors:" in result
        assert '"best_seller_usa"' in result

    def test_uncompetitor_handler_removes_seller(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        handle_competitor_command("/competitor best_seller_usa", env=env, user_profile=profile)
        result = handle_uncompetitor_command("/uncompetitor 1", env=env, user_profile=profile)

        assert "Removed competitor #1" in result

    def test_checkcompetitor_handler_runs_scan(self, monkeypatch, tmp_path):
        profile = make_user_profile()
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}",
            "EBAY_APP_ID": "test",
        }
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()
        handle_competitor_command("/competitor best_seller_usa", env=env, user_profile=profile)

        async def fake_scan(session, telegram_chat_id, competitor_id, tracker, query=None, limit=25):
            del session, tracker, query, limit
            assert telegram_chat_id == profile.telegram_chat_id
            assert competitor_id == 1
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

        monkeypatch.setattr("bot.handlers.competitor.scan_tracked_competitor", fake_scan)
        monkeypatch.setattr(
            "bot.handlers.competitor.list_alert_events",
            lambda session, telegram_chat_id, limit=5: [
                AlertEventRecord(
                    alert_event_id=1,
                    alert_type="competitor_activity",
                    title="best_seller_usa changed",
                    message="1 new item(s)",
                    created_at=None,
                    related_query=None,
                    metadata={"competitor_id": 1},
                )
            ],
        )

        result = asyncio.run(
            handle_checkcompetitor_command(
                "/checkcompetitor 1 airpods",
                env=env,
                user_profile=profile,
            )
        )

        assert "COMPETITOR TRACKER" in result
        assert "Alert:" in result


class TestConnectHandlers:
    def test_connect_command_returns_usage(self):
        profile = make_user_profile()

        result = handle_connect_command("/connect", user_profile=profile)

        assert "Connect a service key:" in result
        assert "/connect keepa" in result

    def test_connect_command_explains_service(self):
        profile = make_user_profile()

        result = handle_connect_command("/connect keepa", user_profile=profile)

        assert "Connect Keepa" in result
        assert "What it adds:" in result
        assert "price history" in result

    def test_connect_command_encrypts_and_saves_key(self, tmp_path):
        profile = make_user_profile()
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}",
            "APP_SECRET_KEY": "dev-secret-with-enough-length",
        }
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        result = handle_connect_command(
            "/connect keepa keepa-api-key-123",
            env=env,
            user_profile=profile,
        )

        assert "Keepa connected." in result
        assert "keepa-api-key-123" not in result
        assert "keepa-...-123" in result

    def test_connect_command_requires_app_secret(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}

        result = handle_connect_command(
            "/connect keepa keepa-api-key-123",
            env=env,
            user_profile=profile,
        )

        assert "APP_SECRET_KEY" in result or "key" in result.lower()

    def test_disconnect_command_removes_key(self, tmp_path):
        profile = make_user_profile()
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}",
            "APP_SECRET_KEY": "dev-secret-with-enough-length",
        }
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()
        handle_connect_command("/connect keepa keepa-api-key-123", env=env, user_profile=profile)

        result = handle_disconnect_command("/disconnect keepa", env=env, user_profile=profile)

        assert result == "Keepa disconnected.\nConnected services left: 0"


class TestDiscoveryHandlers:
    def test_discoverstores_requires_connected_storeleads(self, tmp_path):
        profile = make_user_profile()
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}",
            "APP_SECRET_KEY": "dev-secret-with-enough-length",
        }
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        result = asyncio.run(
            handle_discoverstores_command(
                "/discoverstores pet accessories",
                env=env,
                user_profile=profile,
            )
        )

        assert "Connect StoreLeads first" in result

    def test_discoverstores_returns_summary(self, monkeypatch, tmp_path):
        profile = make_user_profile()
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}",
            "APP_SECRET_KEY": "dev-secret-with-enough-length",
        }
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        class FakeAdapter:
            async def search_domains(self, **kwargs):
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
                            "to_dict": lambda self: {"domain": "petjoy.example"},
                        },
                    )()
                ]

            async def close(self):
                return None

        monkeypatch.setattr(
            "bot.handlers.discovery.get_storeleads_adapter_for_user",
            lambda telegram_chat_id, session, app_secret=None: FakeAdapter(),
        )

        result = asyncio.run(
            handle_discoverstores_command(
                "/discoverstores pet accessories",
                env=env,
                user_profile=profile,
            )
        )

        assert "STORE DISCOVERY" in result
        assert "Pet Joy" in result


class TestAdDiscoveryHandlers:
    def test_discoverads_requires_connected_pipiads(self, tmp_path):
        profile = make_user_profile()
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}",
            "APP_SECRET_KEY": "dev-secret-with-enough-length",
        }
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        result = asyncio.run(
            handle_discoverads_command(
                "/discoverads pet hair remover",
                env=env,
                user_profile=profile,
            )
        )

        assert "Connect PiPiADS first" in result

    def test_discoverads_returns_summary(self, monkeypatch, tmp_path):
        profile = make_user_profile()
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}",
            "APP_SECRET_KEY": "dev-secret-with-enough-length",
        }
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

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
                                    "to_dict": lambda self: {"ad_id": "1"},
                                },
                            )()
                        ]
                    },
                )()

            async def close(self):
                return None

        monkeypatch.setattr(
            "bot.handlers.ad_discovery.get_pipiads_adapter_for_user",
            lambda telegram_chat_id, session, app_secret=None: FakeAdapter(),
        )

        result = asyncio.run(
            handle_discoverads_command(
                "/discoverads pet hair remover",
                env=env,
                user_profile=profile,
            )
        )

        assert "AD DISCOVERY" in result
        assert "PetHero" in result


def make_user_profile():
    return UserProfile(
        user_id=1,
        telegram_chat_id="123",
        username="totik",
        preferred_language="en",
        business_model="us_arbitrage",
        min_profit_threshold=12.0,
        max_buy_price=90.0,
        digest_enabled=True,
        digest_interval_days=1,
        next_digest_at=None,
        enabled_sources=["amazon", "walmart"],
        tracked_queries=[],
    )


class TestSettingsHandlers:
    def test_settings_handler_renders_profile(self):
        profile = make_user_profile()

        result = handle_settings_command(profile)

        assert "Saved settings:" in result
        assert "Min profit: $12.00" in result
        assert "Digest schedule: every 1 day(s)" in result

    def test_track_handler_saves_query(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}

        # Ensure user exists before issuing commands.
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        result = handle_track_command(
            "/track airpods pro",
            env=env,
            user_profile=profile,
        )

        assert 'Saved tracked query: "airpods pro"' in result

    def test_tracklist_handler_shows_saved_queries(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        handle_track_command("/track airpods pro", env=env, user_profile=profile)

        result = handle_tracklist_command(env=env, user_profile=profile)

        assert "Tracked queries:" in result
        assert '"airpods pro"' in result

    def test_untrack_handler_removes_query(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        handle_track_command("/track airpods pro", env=env, user_profile=profile)
        result = handle_untrack_command(
            "/untrack airpods pro",
            env=env,
            user_profile=profile,
        )

        assert 'Removed tracked query: "airpods pro"' in result

    def test_language_handler_updates_language(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        result = handle_language_command("/language ru", env=env, user_profile=profile)

        assert "Русский" in result

    def test_minprofit_handler_updates_threshold(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        result = handle_minprofit_command("/minprofit 25", env=env, user_profile=profile)

        assert "Minimum profit saved: $25.00" == result

    def test_maxbuy_handler_can_clear_value(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        result = handle_maxbuy_command("/maxbuy clear", env=env, user_profile=profile)

        assert "Maximum buy price cleared" == result

    def test_sources_handler_validates_and_saves(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        result = handle_sources_command(
            "/sources walmart",
            env=env,
            user_profile=profile,
        )

        assert "Enabled sources saved: walmart" == result

    def test_sources_handler_accepts_aliexpress(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        result = handle_sources_command(
            "/sources aliexpress",
            env=env,
            user_profile=profile,
        )

        assert "Enabled sources saved: aliexpress" == result

    def test_sources_handler_accepts_cj(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        result = handle_sources_command(
            "/sources cj",
            env=env,
            user_profile=profile,
        )

        assert "Enabled sources saved: cj" == result

    def test_schedule_handler_saves_weekly(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        result = handle_schedule_command(
            "/schedule weekly",
            env=env,
            user_profile=profile,
        )

        assert "Auto digest schedule saved: weekly" == result


class TestWatchlistHandlers:
    def test_watch_handler_saves_item(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        result = handle_watch_command(
            "/watch amazon | AirPods Pro 2 | 79.99",
            env=env,
            user_profile=profile,
        )

        assert 'Watchlist item saved: #1 "AirPods Pro 2" (amazon)' in result

    def test_watch_handler_accepts_aliexpress_source(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        result = handle_watch_command(
            "/watch aliexpress | Anime Desk Lamp | 24.00",
            env=env,
            user_profile=profile,
        )

        assert 'Watchlist item saved: #1 "Anime Desk Lamp" (aliexpress)' in result

    def test_watchlist_handler_lists_items(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        handle_watch_command("/watch walmart | Lego set 75354 | 54", env=env, user_profile=profile)
        result = handle_watchlist_command(env=env, user_profile=profile)

        assert "Watchlist items:" in result
        assert '"Lego set 75354"' in result

    def test_pricepoint_handler_appends_history(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        handle_watch_command("/watch amazon | AirPods Pro 2 | 79.99", env=env, user_profile=profile)
        result = handle_pricepoint_command(
            "/pricepoint 1 74.50 119.00",
            env=env,
            user_profile=profile,
        )

        assert 'Price point saved for #1 "AirPods Pro 2"' in result
        assert "History points: 2" in result
        assert "Alert:" in result
        assert "buy price dropped" in result

    def test_alerts_handler_lists_recent_alerts(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        handle_watch_command("/watch amazon | AirPods Pro 2 | 79.99", env=env, user_profile=profile)
        handle_pricepoint_command(
            "/pricepoint 1 74.50 119.00",
            env=env,
            user_profile=profile,
        )

        result = handle_alerts_command(env=env, user_profile=profile)
        assert "Recent alerts:" in result
        assert "AirPods Pro 2 improved" in result

    def test_unwatch_handler_removes_item(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        handle_watch_command("/watch amazon | AirPods Pro 2 | 79.99", env=env, user_profile=profile)
        result = handle_unwatch_command(
            "/unwatch 1",
            env=env,
            user_profile=profile,
        )

        assert "Removed watchlist item #1" in result


class TestBotRouter:
    def test_handle_start(self):
        result = asyncio.run(handle_message("/start"))

        assert isinstance(result, BotResponse)
        assert "DropAgent" in result.text
        assert result.reply_markup is not None

    def test_handle_start_shows_onboarding_for_first_run(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            profile = get_or_create_user_profile(
                session,
                telegram_chat_id="900",
                username="new_user",
            )
        finally:
            session.close()

        result = asyncio.run(
            handle_message(
                "/start",
                env=env,
                context=BotContext(user_profile=profile, chat_id=900, username="new_user"),
            )
        )

        assert isinstance(result, BotResponse)
        assert "DROPAGENT" in result.text
        assert result.reply_markup is not None

    def test_handle_help(self):
        result = asyncio.run(handle_message("/help"))

        assert "/setup" in result
        assert "/status" in result
        assert "/connect" in result
        assert "/disconnect" in result
        assert "/calc" in result
        assert "/digest" in result
        assert "/weekly" in result
        assert "/listing" in result
        assert "/discoverads" in result
        assert "/discoverstores" in result
        assert "/competitor" in result
        assert "/competitors" in result
        assert "/uncompetitor" in result
        assert "/checkcompetitor" in result
        assert "/track" in result
        assert "/tracklist" in result
        assert "/untrack" in result
        assert "/watch" in result
        assert "/watchlist" in result
        assert "/unwatch" in result
        assert "/pricepoint" in result
        assert "/alerts" in result
        assert "/schedule" in result

    def test_handle_calc(self):
        result = asyncio.run(handle_message("/calc 20 50"))

        assert "MARGIN CALCULATOR" in result

    def test_handle_digest(self, monkeypatch):
        async def fake_handle_digest_command(text, env=None, lang=None, user_profile=None):
            del text, env, lang, user_profile
            return "digest reply"

        monkeypatch.setattr("bot.main.handle_digest_command", fake_handle_digest_command)

        result = asyncio.run(handle_message("/digest airpods"))

        assert result == "digest reply"

    def test_handle_weekly(self, monkeypatch):
        async def fake_handle_weekly_command(text, env=None, lang=None):
            del text, env, lang
            return "weekly reply"

        monkeypatch.setattr("bot.main.handle_weekly_command", fake_handle_weekly_command)

        result = asyncio.run(handle_message("/weekly electronics"))

        assert result == "weekly reply"

    def test_handle_discoverstores(self, monkeypatch):
        async def fake_handle_discoverstores_command(text, env=None, user_profile=None, lang=None):
            del text, env, user_profile, lang
            return "discovery reply"

        monkeypatch.setattr("bot.main.handle_discoverstores_command", fake_handle_discoverstores_command)

        result = asyncio.run(handle_message("/discoverstores pet accessories"))

        assert result == "discovery reply"

    def test_handle_discoverads(self, monkeypatch):
        async def fake_handle_discoverads_command(text, env=None, user_profile=None, lang=None):
            del text, env, user_profile, lang
            return "ad reply"

        monkeypatch.setattr("bot.main.handle_discoverads_command", fake_handle_discoverads_command)

        result = asyncio.run(handle_message("/discoverads pet hair remover"))

        assert result == "ad reply"

    def test_handle_listing(self):
        result = asyncio.run(handle_message("/listing airpods pro"))

        assert "EBAY LISTING DRAFT" in result

    def test_handle_settings(self):
        profile = make_user_profile()

        result = asyncio.run(
            handle_message(
                "/settings",
                context=BotContext(user_profile=profile, chat_id=123, username="totik"),
            )
        )

        assert isinstance(result, BotResponse)
        assert "Saved settings:" in result.text
        assert result.reply_markup is not None

    def test_handle_setup_returns_onboarding(self):
        result = asyncio.run(handle_message("/setup"))

        assert isinstance(result, BotResponse)
        assert "DROPAGENT" in result.text
        assert result.reply_markup is not None

    def test_handle_setup_can_include_dashboard_deep_link(self):
        result = asyncio.run(
            handle_message(
                "/setup",
                env={"DASHBOARD_PUBLIC_URL": "https://dropagent.example"},
                context=BotContext(chat_id=123, username="totik"),
            )
        )

        assert isinstance(result, BotResponse)
        assert result.reply_markup["inline_keyboard"][0][0]["url"] == (
            "https://dropagent.example/?telegram_chat_id=123&username=totik"
        )

    def test_handle_status_returns_simple_capability_summary(self):
        profile = make_user_profile()

        result = asyncio.run(
            handle_message(
                "/status",
                context=BotContext(user_profile=profile, chat_id=123, username="totik"),
            )
        )

        assert "Current stack status:" in result
        assert "Product validation" in result

    def test_handle_connect_routes_to_connect_handler(self, tmp_path):
        profile = make_user_profile()
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}",
            "APP_SECRET_KEY": "dev-secret-with-enough-length",
        }
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        result = asyncio.run(
            handle_message(
                "/connect keepa keepa-api-key-123",
                env=env,
                context=BotContext(user_profile=profile, chat_id=123, username="totik"),
            )
        )

        assert "Keepa connected." in result

    def test_handle_tracklist(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()
        handle_track_command("/track airpods pro", env=env, user_profile=profile)

        result = asyncio.run(
            handle_message(
                "/tracklist",
                env=env,
                context=BotContext(user_profile=profile, chat_id=123, username="totik"),
            )
        )

        assert "Tracked queries:" in result

    def test_handle_watchlist(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()
        handle_watch_command("/watch amazon | AirPods Pro 2 | 79.99", env=env, user_profile=profile)

        result = asyncio.run(
            handle_message(
                "/watchlist",
                env=env,
                context=BotContext(user_profile=profile, chat_id=123, username="totik"),
            )
        )

        assert "Watchlist items:" in result

    def test_handle_competitors(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()
        handle_competitor_command("/competitor best_seller_usa", env=env, user_profile=profile)

        result = asyncio.run(
            handle_message(
                "/competitors",
                env=env,
                context=BotContext(user_profile=profile, chat_id=123, username="totik"),
            )
        )

        assert "Tracked competitors:" in result

    def test_handle_untrack(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()
        handle_track_command("/track airpods pro", env=env, user_profile=profile)

        result = asyncio.run(
            handle_message(
                "/untrack airpods pro",
                env=env,
                context=BotContext(user_profile=profile, chat_id=123, username="totik"),
            )
        )

        assert 'Removed tracked query: "airpods pro"' in result

    def test_handle_schedule(self, tmp_path):
        profile = make_user_profile()
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id=profile.telegram_chat_id)
        finally:
            session.close()

        result = asyncio.run(
            handle_message(
                "/schedule off",
                env=env,
                context=BotContext(user_profile=profile, chat_id=123, username="totik"),
            )
        )

        assert "Auto digest schedule turned off" in result

    def test_unknown_command_falls_back_to_help(self):
        result = asyncio.run(handle_message("/unknown"))

        assert "Type /help" in result


class FakeTelegramClient:
    def __init__(self, updates=None):
        self.updates = updates or []
        self.sent_messages = []
        self.closed = False
        self.last_offset = None
        self.last_timeout = None
        self.answered_callbacks = []

    async def get_updates(self, offset=None, timeout=30):
        self.last_offset = offset
        self.last_timeout = timeout
        return self.updates

    async def send_message(self, chat_id, text, reply_markup=None):
        self.sent_messages.append((chat_id, text, reply_markup))
        return {"chat": {"id": chat_id}, "text": text}

    async def answer_callback_query(self, callback_query_id, text=None):
        self.answered_callbacks.append((callback_query_id, text))
        return {"ok": True}

    async def close(self):
        self.closed = True


class TestTelegramTransport:
    def test_extract_text_message(self):
        chat_id, text = _extract_text_message(
            {"message": {"chat": {"id": 123}, "text": "/start"}}
        )

        assert chat_id == 123
        assert text == "/start"

    def test_extract_text_message_ignores_non_text(self):
        chat_id, text = _extract_text_message({"message": {"chat": {"id": 123}}})

        assert chat_id is None
        assert text is None

    def test_extract_language_normalizes_supported_code(self):
        lang = _extract_language({"message": {"from": {"language_code": "ru-RU"}}})

        assert lang == "ru"

    def test_extract_language_drops_unsupported_code(self):
        lang = _extract_language({"message": {"from": {"language_code": "de-DE"}}})

        assert lang is None

    def test_extract_username(self):
        username = _extract_username({"message": {"from": {"username": "totik"}}})

        assert username == "totik"

    def test_process_update_sends_reply(self):
        client = FakeTelegramClient()

        async def fake_router(text, env=None, lang=None, context=None):
            del text, env, lang
            assert context is not None
            assert context.user_profile is not None
            return "reply text"

        handled = asyncio.run(
            process_update(
                {
                    "update_id": 10,
                    "message": {
                        "chat": {"id": 321},
                        "text": "/help",
                        "from": {"language_code": "en-US", "username": "totik"},
                    },
                },
                bot_client=client,
                env={"EBAY_APP_ID": "test", "DATABASE_URL": "sqlite:///:memory:"},
                router=fake_router,
            )
        )

        assert handled is True
        assert client.sent_messages == [(321, "reply text", None)]

    def test_process_update_ignores_non_text_messages(self):
        client = FakeTelegramClient()

        async def fake_router(text, env=None, lang=None, context=None):
            del text, env, lang, context
            return "reply text"

        handled = asyncio.run(
            process_update(
                {"update_id": 10, "message": {"chat": {"id": 321}}},
                bot_client=client,
                router=fake_router,
            )
        )

        assert handled is False
        assert client.sent_messages == []

    def test_poll_once_processes_updates_and_returns_next_offset(self):
        client = FakeTelegramClient(
            updates=[
                {"update_id": 41, "message": {"chat": {"id": 1}, "text": "/start"}},
                {"update_id": 42, "message": {"chat": {"id": 2}, "text": "/help"}},
            ]
        )

        async def fake_router(text, env=None, lang=None, context=None):
            del env, lang, context
            return f"handled {text}"

        next_offset = asyncio.run(
            poll_once(
                bot_client=client,
                offset=10,
                env={"TELEGRAM_BOT_TOKEN": "x", "DATABASE_URL": "sqlite:///:memory:"},
                router=fake_router,
                timeout=15,
            )
        )

        assert next_offset == 43
        assert client.last_offset == 10
        assert client.last_timeout == 15
        assert client.sent_messages == [
            (1, "handled /start", None),
            (2, "handled /help", None),
        ]

    def test_process_callback_query_onboarding_model_flow(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        client = FakeTelegramClient()

        handled = asyncio.run(
            process_callback_query(
                {
                    "callback_query": {
                        "id": "cb-1",
                        "data": "onboarding:model:china_dropshipping",
                        "from": {"language_code": "en-US", "username": "totik"},
                        "message": {"chat": {"id": 555}},
                    }
                },
                bot_client=client,
                env=env,
            )
        )

        session = get_session(get_database_url(env))
        try:
            profile = get_or_create_user_profile(session, telegram_chat_id="555")
        finally:
            session.close()

        assert handled is True
        assert profile.business_model == "china_dropshipping"
        assert profile.enabled_sources == ["aliexpress", "cj"]
        assert client.answered_callbacks == [("cb-1", None)]
        assert client.sent_messages
        assert "Recommended integrations" in client.sent_messages[0][1]

    def test_process_callback_query_onboarding_toggle_selection(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        client = FakeTelegramClient()
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id="556")
            update_user_settings(
                session,
                telegram_chat_id="556",
                business_model="us_arbitrage",
                selected_integrations=["amazon"],
            )
        finally:
            session.close()

        handled = asyncio.run(
            process_callback_query(
                {
                    "callback_query": {
                        "id": "cb-2",
                        "data": "onboarding:toggle:keepa",
                        "from": {"language_code": "en-US", "username": "totik"},
                        "message": {"chat": {"id": 556}},
                    }
                },
                bot_client=client,
                env=env,
            )
        )

        session = get_session(get_database_url(env))
        try:
            profile = get_or_create_user_profile(session, telegram_chat_id="556")
        finally:
            session.close()

        assert handled is True
        assert "amazon" in profile.selected_integrations
        assert "keepa" in profile.selected_integrations

    def test_process_scheduled_digests_sends_due_reports(self, tmp_path):
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'schedule.db'}",
            "EBAY_APP_ID": "test",
        }
        session = get_session(get_database_url(env))
        try:
            profile = get_or_create_user_profile(session, telegram_chat_id="555", username="totik")
            update_user_settings(
                session,
                telegram_chat_id="555",
                next_digest_at=profile.next_digest_at.replace(year=2020) if profile.next_digest_at else None,
            )
        finally:
            session.close()

        client = FakeTelegramClient()

        sent = asyncio.run(process_scheduled_digests(bot_client=client, env=env))

        assert sent == 1
        assert client.sent_messages
        assert "Auto digest skipped" in client.sent_messages[0][1]

    def test_status_command_includes_next_step(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'bot.db'}"}
        client = FakeTelegramClient()
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id="557", preferred_language="en")
        finally:
            session.close()

        response = asyncio.run(
            process_update(
                {
                    "message": {
                        "chat": {"id": 557},
                        "text": "/status",
                        "from": {"language_code": "en-US"},
                    }
                },
                bot_client=client,
                env=env,
            )
        )

        assert response is True
        assert client.sent_messages
        assert "Current stack status:" in client.sent_messages[0][1]
        assert "Next step:" in client.sent_messages[0][1]
        assert "Add your first tracked product with /track" in client.sent_messages[0][1]


class TestBotMain:
    def test_main_requires_token(self, monkeypatch, capsys):
        monkeypatch.setattr("bot.main.load_dotenv", lambda: None)
        monkeypatch.setattr("bot.main.os.getenv", lambda key, default="": "")

        exit_code = main()

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "TELEGRAM_BOT_TOKEN is required" in captured.out

    def test_main_handles_keyboard_interrupt(self, monkeypatch):
        monkeypatch.setattr("bot.main.load_dotenv", lambda: None)
        monkeypatch.setattr("bot.main.os.getenv", lambda key, default="": "token")

        async def fake_run_polling(bot_client, env=None):
            del bot_client, env
            raise KeyboardInterrupt()

        monkeypatch.setattr("bot.main.run_polling", fake_run_polling)

        exit_code = main()

        assert exit_code == 0
