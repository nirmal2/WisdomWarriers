"""add resume payload column to scrape_runs

Revision ID: 0026
Revises: 0025
Create Date: 2026-05-05
"""

from alembic import op
import sqlalchemy as sa


revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scrape_runs", sa.Column("resume_payload", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("scrape_runs", "resume_payload")
