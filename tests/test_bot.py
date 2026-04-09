"""Tests for the bot command layer."""

import asyncio

from bot.handlers.calc import handle_calc_command
from bot.handlers.digest import handle_digest_command
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
from bot.main import (
    BotContext,
    _extract_language,
    _extract_text_message,
    _extract_username,
    handle_message,
    main,
    poll_once,
    process_scheduled_digests,
    process_update,
)
from db.service import UserProfile, get_or_create_user_profile, update_user_settings
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


class TestBotRouter:
    def test_handle_start(self):
        result = asyncio.run(handle_message("/start"))

        assert "Welcome to DropAgent!" == result

    def test_handle_help(self):
        result = asyncio.run(handle_message("/help"))

        assert "/calc" in result
        assert "/digest" in result
        assert "/track" in result
        assert "/tracklist" in result
        assert "/untrack" in result
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

    def test_handle_settings(self):
        profile = make_user_profile()

        result = asyncio.run(
            handle_message(
                "/settings",
                context=BotContext(user_profile=profile, chat_id=123, username="totik"),
            )
        )

        assert "Saved settings:" in result

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

    async def get_updates(self, offset=None, timeout=30):
        self.last_offset = offset
        self.last_timeout = timeout
        return self.updates

    async def send_message(self, chat_id, text):
        self.sent_messages.append((chat_id, text))
        return {"chat": {"id": chat_id}, "text": text}

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
        assert client.sent_messages == [(321, "reply text")]

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
            (1, "handled /start"),
            (2, "handled /help"),
        ]

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
