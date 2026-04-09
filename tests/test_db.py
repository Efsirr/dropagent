"""Tests for the database layer."""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from db.base import Base
from db.models import PriceHistoryEntry, TrackedQuery, User, UserSettings, WatchlistItem
from db.service import (
    add_tracked_competitor,
    add_watchlist_item,
    add_watchlist_price_point,
    add_tracked_query,
    compute_next_digest_at,
    get_or_create_user_profile,
    list_tracked_competitors,
    list_watchlist_history,
    list_watchlist_items,
    list_tracked_queries,
    list_due_digest_profiles,
    mark_digest_sent,
    remove_tracked_competitor,
    remove_watchlist_item,
    remove_tracked_query,
    scan_tracked_competitor,
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
            user.watchlist_items.append(
                WatchlistItem(
                    product_name="AirPods Pro 2",
                    source="amazon",
                    current_buy_price=79.99,
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
            assert len(saved_user.watchlist_items) == 1
            assert saved_user.watchlist_items[0].product_name == "AirPods Pro 2"
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
                selected_integrations=["walmart", "keepa"],
                onboarding_completed=True,
            )
            assert profile.min_profit_threshold == 18.0
            assert profile.max_buy_price == 120.0
            assert profile.enabled_sources == ["walmart"]
            assert profile.selected_integrations == ["walmart", "keepa"]
            assert profile.onboarding_completed is True

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

            item = add_watchlist_item(
                session,
                telegram_chat_id="555",
                product_name="Lego set 75354",
                source="walmart",
                current_buy_price=54.0,
            )
            assert item.product_name == "Lego set 75354"
            assert len(item.price_history) == 1

            items = list_watchlist_items(session, telegram_chat_id="555")
            assert len(items) == 1
            assert items[0].source == "walmart"

            updated_item = add_watchlist_price_point(
                session,
                telegram_chat_id="555",
                item_id=item.item_id,
                buy_price=49.0,
                sell_price=79.0,
            )
            assert len(updated_item.price_history) == 2
            assert updated_item.current_buy_price == 49.0
            assert updated_item.current_sell_price == 79.0

            history = list_watchlist_history(
                session,
                telegram_chat_id="555",
                item_id=item.item_id,
            )
            assert len(history) == 2
            assert history[-1].sell_price == 79.0

            remaining = remove_watchlist_item(
                session,
                telegram_chat_id="555",
                item_id=item.item_id,
            )
            assert remaining == []

            competitor = add_tracked_competitor(
                session,
                telegram_chat_id="555",
                seller_username="best_seller_usa",
            )
            assert competitor.seller_username == "best_seller_usa"

            competitors = list_tracked_competitors(session, telegram_chat_id="555")
            assert len(competitors) == 1
            assert competitors[0].known_item_count == 0

            class FakeTracker:
                async def scan_seller(self, seller_username, known_item_ids=None, query=None, limit=25):
                    del known_item_ids, query, limit
                    assert seller_username == "best_seller_usa"
                    from agent.competitor import CompetitorItem, CompetitorReport

                    return CompetitorReport(
                        seller_username=seller_username,
                        generated_at=datetime.now(timezone.utc),
                        items=[
                            CompetitorItem(
                                item_id="E1",
                                title="AirPods Pro 2",
                                sold_price=119.0,
                                sold_date=datetime.now(timezone.utc),
                                category="Headphones",
                                is_new=True,
                            )
                        ],
                    )

            report = asyncio.run(
                scan_tracked_competitor(
                    session,
                    telegram_chat_id="555",
                    competitor_id=competitor.competitor_id,
                    tracker=FakeTracker(),
                )
            )
            assert report.new_count == 1

            competitors = list_tracked_competitors(session, telegram_chat_id="555")
            assert competitors[0].known_item_count == 1

            remaining_competitors = remove_tracked_competitor(
                session,
                telegram_chat_id="555",
                competitor_id=competitor.competitor_id,
            )
            assert remaining_competitors == []
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
