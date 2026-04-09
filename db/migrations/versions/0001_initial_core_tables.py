"""Initial core user and query tables."""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_core_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(length=64), nullable=True, unique=True),
        sa.Column("email", sa.String(length=255), nullable=True, unique=True),
        sa.Column("telegram_chat_id", sa.String(length=64), nullable=True, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("preferred_language", sa.String(length=8), nullable=False, server_default="en"),
        sa.Column("business_model", sa.String(length=32), nullable=False, server_default="us_arbitrage"),
        sa.Column("min_profit_threshold", sa.Float(), nullable=False, server_default="5.0"),
        sa.Column("max_buy_price", sa.Float(), nullable=True),
        sa.Column("alert_hour_utc", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("enabled_sources", sa.Text(), nullable=False, server_default="amazon,walmart"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "tracked_queries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("query", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("max_buy_price", sa.Float(), nullable=True),
        sa.Column("min_profit_threshold", sa.Float(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "user_id",
            "query",
            "category",
            name="uq_tracked_queries_user_query_category",
        ),
    )


def downgrade() -> None:
    op.drop_table("tracked_queries")
    op.drop_table("user_settings")
    op.drop_table("users")
