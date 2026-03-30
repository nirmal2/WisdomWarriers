"""add missing_usernames to scrape_runs

Revision ID: 0010
Revises: 0009
Create Date: 2026-03-28
"""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scrape_runs", sa.Column("missing_usernames", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("scrape_runs", "missing_usernames")
