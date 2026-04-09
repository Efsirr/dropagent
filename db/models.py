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
