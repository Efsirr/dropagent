"""Add digest scheduling fields to user settings."""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_digest_schedule_fields"
down_revision = "0001_initial_core_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("digest_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "user_settings",
        sa.Column("digest_interval_days", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "user_settings",
        sa.Column("next_digest_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "next_digest_at")
    op.drop_column("user_settings", "digest_interval_days")
    op.drop_column("user_settings", "digest_enabled")
