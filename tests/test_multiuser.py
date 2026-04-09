"""Tests for explicit multi-user isolation across the project."""

import asyncio
from datetime import datetime, timedelta, timezone

from bot.main import process_scheduled_digests, process_update
from dashboard.backend.service import (
    add_watchlist_item_payload,
    add_tracked_query_payload,
    get_user_profile_payload,
    list_tracked_queries_payload,
    update_digest_schedule_payload,
    update_user_settings_payload,
)
from db.base import Base
from db.service import (
    get_or_create_user_profile,
    list_due_digest_profiles,
    update_user_settings,
)
from db.session import create_engine_from_url, create_session_factory, get_database_url, get_session


class FakeTelegramClient:
    def __init__(self):
        self.sent_messages = []

    async def send_message(self, chat_id, text):
        self.sent_messages.append((chat_id, text))
        return {"chat": {"id": chat_id}, "text": text}


class TestMultiUserDatabaseIsolation:
    def test_two_users_keep_separate_profiles_and_queries(self):
        engine = create_engine_from_url("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        factory = create_session_factory("sqlite:///:memory:")
        factory.configure(bind=engine)

        session = factory()
        try:
            user_a = get_or_create_user_profile(
                session,
                telegram_chat_id="1001",
                username="alice",
                preferred_language="en",
            )
            user_b = get_or_create_user_profile(
                session,
                telegram_chat_id="2002",
                username="boris",
                preferred_language="ru",
            )

            update_user_settings(
                session,
                telegram_chat_id="1001",
                min_profit_threshold=10.0,
                enabled_sources=["amazon"],
            )
            update_user_settings(
                session,
                telegram_chat_id="2002",
                min_profit_threshold=25.0,
                enabled_sources=["walmart"],
            )

            from db.service import add_tracked_query

            alice = add_tracked_query(
                session,
                telegram_chat_id="1001",
                query="airpods pro",
            )
            boris = add_tracked_query(
                session,
                telegram_chat_id="2002",
                query="lego set",
            )

            assert user_a.telegram_chat_id != user_b.telegram_chat_id
            assert alice.tracked_queries[0].query == "airpods pro"
            assert boris.tracked_queries[0].query == "lego set"
            assert alice.min_profit_threshold == 10.0
            assert boris.min_profit_threshold == 25.0
            assert alice.enabled_sources == ["amazon"]
            assert boris.enabled_sources == ["walmart"]
        finally:
            session.close()

    def test_due_digest_profiles_only_returns_due_users(self):
        engine = create_engine_from_url("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        factory = create_session_factory("sqlite:///:memory:")
        factory.configure(bind=engine)

        now = datetime(2026, 4, 9, 8, 0, tzinfo=timezone.utc)
        session = factory()
        try:
            get_or_create_user_profile(session, telegram_chat_id="1001", username="alice")
            get_or_create_user_profile(session, telegram_chat_id="2002", username="boris")

            update_user_settings(
                session,
                telegram_chat_id="1001",
                next_digest_at=now - timedelta(minutes=5),
            )
            update_user_settings(
                session,
                telegram_chat_id="2002",
                next_digest_at=now + timedelta(days=1),
            )

            due = list_due_digest_profiles(session, now=now)

            assert [profile.telegram_chat_id for profile in due] == ["1001"]
        finally:
            session.close()


class TestMultiUserDashboardIsolation:
    def test_dashboard_payloads_stay_isolated(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'multiuser.db'}"}

        get_user_profile_payload("1001", env=env, username="alice", preferred_language="en")
        get_user_profile_payload("2002", env=env, username="boris", preferred_language="ru")

        update_user_settings_payload(
            "1001",
            env=env,
            min_profit_threshold=12.0,
            enabled_sources=["amazon"],
        )
        update_user_settings_payload(
            "2002",
            env=env,
            min_profit_threshold=30.0,
            enabled_sources=["walmart"],
        )

        add_tracked_query_payload("1001", "airpods pro", env=env)
        add_tracked_query_payload("2002", "lego set", env=env)

        alice = get_user_profile_payload("1001", env=env)
        boris = get_user_profile_payload("2002", env=env)

        assert alice["preferred_language"] == "en"
        assert boris["preferred_language"] == "ru"
        assert alice["tracked_queries"][0]["query"] == "airpods pro"
        assert boris["tracked_queries"][0]["query"] == "lego set"
        assert alice["enabled_sources"] == ["amazon"]
        assert boris["enabled_sources"] == ["walmart"]

    def test_watchlist_payloads_stay_isolated(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'multiuser.db'}"}

        get_user_profile_payload("1001", env=env, username="alice", preferred_language="en")
        get_user_profile_payload("2002", env=env, username="boris", preferred_language="ru")

        add_watchlist_item_payload(
            "1001",
            product_name="AirPods Pro 2",
            source="amazon",
            env=env,
            current_buy_price=79.99,
        )
        add_watchlist_item_payload(
            "2002",
            product_name="Lego set 75354",
            source="walmart",
            env=env,
            current_buy_price=54.0,
        )

        alice = get_user_profile_payload("1001", env=env)
        boris = get_user_profile_payload("2002", env=env)

        assert alice["watchlist_items"][0]["product_name"] == "AirPods Pro 2"
        assert boris["watchlist_items"][0]["product_name"] == "Lego set 75354"

    def test_digest_schedule_updates_are_user_specific(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'multiuser.db'}"}

        get_user_profile_payload("1001", env=env)
        get_user_profile_payload("2002", env=env)

        update_digest_schedule_payload("1001", interval_days=1, enabled=True, env=env)
        update_digest_schedule_payload("2002", interval_days=7, enabled=True, env=env)

        alice = get_user_profile_payload("1001", env=env)
        boris = get_user_profile_payload("2002", env=env)

        assert alice["digest_interval_days"] == 1
        assert boris["digest_interval_days"] == 7


class TestMultiUserBotIsolation:
    def test_process_update_creates_distinct_users(self, tmp_path):
        env = {"DATABASE_URL": f"sqlite:///{tmp_path / 'multiuser.db'}", "EBAY_APP_ID": "test"}
        client = FakeTelegramClient()

        async def fake_router(text, env=None, lang=None, context=None):
            del env
            return f"{context.user_profile.telegram_chat_id}:{lang}:{text}"

        asyncio.run(
            process_update(
                {
                    "update_id": 1,
                    "message": {
                        "chat": {"id": 1001},
                        "text": "/help",
                        "from": {"username": "alice", "language_code": "en-US"},
                    },
                },
                bot_client=client,
                env=env,
                router=fake_router,
            )
        )
        asyncio.run(
            process_update(
                {
                    "update_id": 2,
                    "message": {
                        "chat": {"id": 2002},
                        "text": "/help",
                        "from": {"username": "boris", "language_code": "ru-RU"},
                    },
                },
                bot_client=client,
                env=env,
                router=fake_router,
            )
        )

        assert client.sent_messages == [
            (1001, "1001:en:/help"),
            (2002, "2002:ru:/help"),
        ]

    def test_scheduled_digests_only_send_to_due_user(self, tmp_path):
        env = {
            "DATABASE_URL": f"sqlite:///{tmp_path / 'multiuser.db'}",
            "EBAY_APP_ID": "test",
        }
        session = get_session(get_database_url(env))
        try:
            get_or_create_user_profile(session, telegram_chat_id="1001", username="alice")
            get_or_create_user_profile(session, telegram_chat_id="2002", username="boris")

            from db.service import add_tracked_query

            add_tracked_query(session, telegram_chat_id="1001", query="airpods pro")
            add_tracked_query(session, telegram_chat_id="2002", query="lego set")

            now = datetime.now(timezone.utc)
            update_user_settings(
                session,
                telegram_chat_id="1001",
                next_digest_at=now - timedelta(minutes=1),
            )
            update_user_settings(
                session,
                telegram_chat_id="2002",
                next_digest_at=now + timedelta(days=1),
            )
        finally:
            session.close()

        client = FakeTelegramClient()

        async def fake_digest_command(text, env=None, lang=None, runner=None, user_profile=None):
            del text, env, lang, runner
            return f"digest-for-{user_profile.telegram_chat_id}"

        import bot.main

        original = bot.main.handle_digest_command
        bot.main.handle_digest_command = fake_digest_command
        try:
            sent = asyncio.run(process_scheduled_digests(bot_client=client, env=env))
        finally:
            bot.main.handle_digest_command = original

        assert sent == 1
        assert client.sent_messages == [(1001, "digest-for-1001")]
