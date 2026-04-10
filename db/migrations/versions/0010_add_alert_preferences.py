"""Add alert preferences to user settings."""

from alembic import op
import sqlalchemy as sa


revision = "0010_add_alert_preferences"
down_revision = "0009_add_alert_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column(
            "alert_preferences",
            sa.Text(),
            nullable=False,
            server_default="discovery,watchlist,competitor",
        ),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "alert_preferences")
