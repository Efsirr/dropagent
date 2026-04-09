"""Add onboarding fields to user settings."""

from alembic import op
import sqlalchemy as sa


revision = "0005_add_onboarding_fields"
down_revision = "0004_add_competitor_tracking_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column(
            "onboarding_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "user_settings",
        sa.Column(
            "selected_integrations",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "selected_integrations")
    op.drop_column("user_settings", "onboarding_completed")
