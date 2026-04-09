"""Add per-user integration credentials."""

from alembic import op
import sqlalchemy as sa


revision = "0006_add_user_integration_credentials"
down_revision = "0005_add_onboarding_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_integration_credentials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("integration_id", sa.String(length=64), nullable=False),
        sa.Column("encrypted_secret", sa.Text(), nullable=False),
        sa.Column("secret_hint", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="connected"),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "integration_id",
            name="uq_user_integration_credentials_user_integration",
        ),
    )


def downgrade() -> None:
    op.drop_table("user_integration_credentials")
