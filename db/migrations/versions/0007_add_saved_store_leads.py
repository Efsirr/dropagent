"""Add saved store leads table."""

from alembic import op
import sqlalchemy as sa


revision = "0007_add_saved_store_leads"
down_revision = "0006_add_user_integration_credentials"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_store_leads",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("merchant_name", sa.String(length=255), nullable=True),
        sa.Column("niche_query", sa.String(length=255), nullable=True),
        sa.Column("source_integration", sa.String(length=64), nullable=False, server_default="storeleads"),
        sa.Column("estimated_visits", sa.Integer(), nullable=True),
        sa.Column("estimated_sales_monthly_usd", sa.Float(), nullable=True),
        sa.Column("avg_price_usd", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "domain", name="uq_saved_store_leads_user_domain"),
    )


def downgrade() -> None:
    op.drop_table("saved_store_leads")
