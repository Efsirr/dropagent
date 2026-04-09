"""Database engine and session helpers."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from db.base import Base

DEFAULT_DATABASE_URL = "sqlite:///./dropagent.db"


def get_database_url(env: Optional[dict] = None) -> str:
    """Resolve the active database URL from env, with a local SQLite fallback."""
    env = env or os.environ
    return env.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def create_engine_from_url(database_url: str, echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine with SQLite-safe defaults."""
    kwargs = {"echo": echo, "future": True}
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(database_url, **kwargs)


@lru_cache(maxsize=8)
def get_initialized_engine(database_url: str, echo: bool = False) -> Engine:
    """Create and initialize an engine once per database URL."""
    engine = create_engine_from_url(database_url, echo=echo)
    Base.metadata.create_all(engine)
    return engine


def create_session_factory(database_url: str, echo: bool = False) -> sessionmaker:
    """Build a configured SQLAlchemy session factory."""
    engine = get_initialized_engine(database_url, echo=echo)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session(database_url: Optional[str] = None, echo: bool = False) -> Session:
    """Open a new database session."""
    factory = create_session_factory(database_url or get_database_url(), echo=echo)
    return factory()
