"""Tests for the database layer."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from db.base import Base
from db.models import TrackedQuery, User, UserSettings
from db.service import (
    add_tracked_query,
    compute_next_digest_at,
    get_or_create_user_profile,
    list_tracked_queries,
    list_due_digest_profiles,
    mark_digest_sent,
    remove_tracked_query,
    update_digest_schedule,
    update_user_settings,
)
from db.session import DEFAULT_DATABASE_URL, create_engine_from_url, create_session_factory, get_database_url


class TestDatabaseSessionHelpers:
    def test_get_database_url_defaults_to_sqlite(self):
        assert get_database_url({}) == DEFAULT_DATABASE_URL

    def test_create_session_factory_with_sqlite(self):
        factory = create_session_factory("sqlite:///:memory:")
        session = factory()
        try:
            assert session is not None
        finally:
            session.close()


class TestDatabaseModels:
    def test_user_settings_and_queries_round_trip(self):
        engine = create_engine_from_url("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        factory = create_session_factory("sqlite:///:memory:")

        # Use the same engine for both metadata and session factory.
        factory.configure(bind=engine)

        session = factory()
        try:
            user = User(
                username="totik",
                email="totik@example.com",
                telegram_chat_id="123456",
            )
            user.settings = UserSettings(
                preferred_language="ru",
                business_model="us_arbitrage",
                min_profit_threshold=12.5,
                enabled_sources="amazon,walmart",
            )
            user.tracked_queries.append(
                TrackedQuery(
                    query="airpods pro",
                    category="electronics",
                    max_buy_price=80.0,
                    min_profit_threshold=15.0,
                )
            )

            session.add(user)
            session.commit()
            session.refresh(user)

            saved_user = session.scalar(select(User).where(User.username == "totik"))

            assert saved_user is not None
            assert saved_user.settings is not None
            assert saved_user.settings.preferred_language == "ru"
            assert len(saved_user.tracked_queries) == 1
            assert saved_user.tracked_queries[0].query == "airpods pro"
        finally:
            session.close()

    def test_user_profile_service_round_trip(self):
        engine = create_engine_from_url("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        factory = create_session_factory("sqlite:///:memory:")
        factory.configure(bind=engine)

        session = factory()
        try:
            profile = get_or_create_user_profile(
                session,
                telegram_chat_id="555",
                username="totik_bot",
                preferred_language="zh",
            )
            assert profile.telegram_chat_id == "555"
            assert profile.preferred_language == "zh"

            profile = update_user_settings(
                session,
                telegram_chat_id="555",
                min_profit_threshold=18.0,
                max_buy_price=120.0,
                enabled_sources=["walmart"],
            )
            assert profile.min_profit_threshold == 18.0
            assert profile.max_buy_price == 120.0
            assert profile.enabled_sources == ["walmart"]

            profile = add_tracked_query(
                session,
                telegram_chat_id="555",
                query="airpods pro",
                max_buy_price=85.0,
                min_profit_threshold=20.0,
            )
            assert len(profile.tracked_queries) == 1
            assert profile.tracked_queries[0].query == "airpods pro"

            tracked = list_tracked_queries(session, telegram_chat_id="555")
            assert len(tracked) == 1
            assert tracked[0].max_buy_price == 85.0

            profile = remove_tracked_query(
                session,
                telegram_chat_id="555",
                query="airpods pro",
            )
            assert profile.tracked_queries == []
        finally:
            session.close()

    def test_digest_schedule_due_and_mark_sent(self):
        engine = create_engine_from_url("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        factory = create_session_factory("sqlite:///:memory:")
        factory.configure(bind=engine)

        session = factory()
        try:
            now = datetime(2026, 4, 9, 8, 0, tzinfo=timezone.utc)
            profile = get_or_create_user_profile(
                session,
                telegram_chat_id="777",
                username="digest_user",
            )
            assert profile.digest_interval_days == 1

            profile = update_digest_schedule(
                session,
                telegram_chat_id="777",
                interval_days=2,
                enabled=True,
                now=now,
            )
            assert profile.digest_enabled is True
            assert profile.digest_interval_days == 2
            assert profile.next_digest_at is not None

            overdue = update_user_settings(
                session,
                telegram_chat_id="777",
                next_digest_at=now - timedelta(minutes=1),
            )
            assert overdue.next_digest_at is not None

            due_profiles = list_due_digest_profiles(session, now=now)
            assert len(due_profiles) == 1
            assert due_profiles[0].telegram_chat_id == "777"

            updated = mark_digest_sent(session, telegram_chat_id="777", sent_at=now)
            assert updated.next_digest_at > now
        finally:
            session.close()


class TestScheduleHelpers:
    def test_compute_next_digest_at_respects_interval(self):
        now = datetime(2026, 4, 9, 9, 0, tzinfo=timezone.utc)

        next_run = compute_next_digest_at(interval_days=3, alert_hour_utc=8, now=now)

        assert next_run == datetime(2026, 4, 12, 8, 0, tzinfo=timezone.utc)
