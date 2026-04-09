"""Core SQLAlchemy models for DropAgent."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    """A DropAgent user account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    telegram_chat_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    settings: Mapped[Optional["UserSettings"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    tracked_queries: Mapped[list["TrackedQuery"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    watchlist_items: Mapped[list["WatchlistItem"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    tracked_competitors: Mapped[list["TrackedCompetitor"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    integration_credentials: Mapped[list["UserIntegrationCredential"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserSettings(TimestampMixin, Base):
    """Per-user preferences for language, sourcing, and alerts."""

    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    preferred_language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")
    business_model: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="us_arbitrage",
    )
    min_profit_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    max_buy_price: Mapped[Optional[float]] = mapped_column(Float)
    alert_hour_utc: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    digest_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    digest_interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    next_digest_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    selected_integrations: Mapped[str] = mapped_column(Text, nullable=False, default="")
    enabled_sources: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="amazon,walmart",
    )

    user: Mapped["User"] = relationship(back_populates="settings")


class TrackedQuery(TimestampMixin, Base):
    """Saved product/category searches for recurring digests and alerts."""

    __tablename__ = "tracked_queries"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "query",
            "category",
            name="uq_tracked_queries_user_query_category",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    query: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(128))
    max_buy_price: Mapped[Optional[float]] = mapped_column(Float)
    min_profit_threshold: Mapped[Optional[float]] = mapped_column(Float)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["User"] = relationship(back_populates="tracked_queries")


class WatchlistItem(TimestampMixin, Base):
    """User-saved product watchlist item with the latest known prices."""

    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="amazon")
    product_url: Mapped[Optional[str]] = mapped_column(Text)
    target_buy_price: Mapped[Optional[float]] = mapped_column(Float)
    target_sell_price: Mapped[Optional[float]] = mapped_column(Float)
    current_buy_price: Mapped[Optional[float]] = mapped_column(Float)
    current_sell_price: Mapped[Optional[float]] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["User"] = relationship(back_populates="watchlist_items")
    price_history: Mapped[list["PriceHistoryEntry"]] = relationship(
        back_populates="watchlist_item",
        cascade="all, delete-orphan",
        order_by="PriceHistoryEntry.recorded_at",
    )


class PriceHistoryEntry(Base):
    """Historical watchlist price snapshot for charting and alerts."""

    __tablename__ = "price_history_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    watchlist_item_id: Mapped[int] = mapped_column(
        ForeignKey("watchlist_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    buy_price: Mapped[Optional[float]] = mapped_column(Float)
    sell_price: Mapped[Optional[float]] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    watchlist_item: Mapped["WatchlistItem"] = relationship(back_populates="price_history")


class TrackedCompetitor(TimestampMixin, Base):
    """User-saved competitor seller to monitor on eBay."""

    __tablename__ = "tracked_competitors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    seller_username: Mapped[str] = mapped_column(String(128), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String(255))
    last_scan_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["User"] = relationship(back_populates="tracked_competitors")
    observations: Mapped[list["CompetitorObservation"]] = relationship(
        back_populates="competitor",
        cascade="all, delete-orphan",
    )


class CompetitorObservation(TimestampMixin, Base):
    """Previously observed sold item for competitor change detection."""

    __tablename__ = "competitor_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    competitor_id: Mapped[int] = mapped_column(
        ForeignKey("tracked_competitors.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(128))
    sold_price: Mapped[Optional[float]] = mapped_column(Float)
    sold_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    competitor: Mapped["TrackedCompetitor"] = relationship(back_populates="observations")


class UserIntegrationCredential(TimestampMixin, Base):
    """Encrypted per-user API key for an external service."""

    __tablename__ = "user_integration_credentials"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "integration_id",
            name="uq_user_integration_credentials_user_integration",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    integration_id: Mapped[str] = mapped_column(String(64), nullable=False)
    encrypted_secret: Mapped[str] = mapped_column(Text, nullable=False)
    secret_hint: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="connected")
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="integration_credentials")
