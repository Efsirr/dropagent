# Database Module

This module contains the shared database layer for DropAgent.

Current scope:
- SQLAlchemy models for the first multi-user tables
- Engine and session helpers
- Alembic migration scaffolding
- watchlist items with price-history snapshots

Default direction:
- Production and self-hosted deployments should use PostgreSQL
- Tests and lightweight local development can use SQLite

Current tables:
- `users`
- `user_settings`
- `tracked_queries`
- `watchlist_items`
- `price_history_entries`
- `tracked_competitors`
- `competitor_observations`
