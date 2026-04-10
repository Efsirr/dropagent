"""Add discovery runs table."""

from alembic import op
import sqlalchemy as sa


revision = "0008_add_discovery_runs"
down_revision = "0007_add_saved_store_leads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "discovery_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("query", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=16), nullable=True),
        sa.Column("result_limit", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("store_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ad_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trend_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("discovery_runs")
