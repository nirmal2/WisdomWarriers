"""add scrape profile source table

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-28
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scrape_profiles",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("username", sa.Text, nullable=False, unique=True),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_scrape_profiles_username", "scrape_profiles", ["username"])


def downgrade() -> None:
    op.drop_index("ix_scrape_profiles_username", table_name="scrape_profiles")
    op.drop_table("scrape_profiles")