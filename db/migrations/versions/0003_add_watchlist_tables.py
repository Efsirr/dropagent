"""Add watchlist items and price history tables."""

from alembic import op
import sqlalchemy as sa


revision = "0003_add_watchlist_tables"
down_revision = "0002_add_digest_schedule_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="amazon"),
        sa.Column("product_url", sa.Text(), nullable=True),
        sa.Column("target_buy_price", sa.Float(), nullable=True),
        sa.Column("target_sell_price", sa.Float(), nullable=True),
        sa.Column("current_buy_price", sa.Float(), nullable=True),
        sa.Column("current_sell_price", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
    )

    op.create_table(
        "price_history_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("watchlist_item_id", sa.Integer(), sa.ForeignKey("watchlist_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("buy_price", sa.Float(), nullable=True),
        sa.Column("sell_price", sa.Float(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("price_history_entries")
    op.drop_table("watchlist_items")
