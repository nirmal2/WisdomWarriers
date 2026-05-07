"""add per-profile progress checkpoints for scrape runs

Revision ID: 0027
Revises: 0026
Create Date: 2026-05-07
"""

from alembic import op
import sqlalchemy as sa


revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scrape_run_profile_progress",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("last_checkpoint_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "username", name="uq_scrape_run_profile_progress_run_username"),
    )
    op.create_index(
        "ix_scrape_run_profile_progress_run_id",
        "scrape_run_profile_progress",
        ["run_id"],
        unique=False,
    )
    op.create_index(
        "ix_scrape_run_profile_progress_run_status",
        "scrape_run_profile_progress",
        ["run_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_scrape_run_profile_progress_run_status", table_name="scrape_run_profile_progress")
    op.drop_index("ix_scrape_run_profile_progress_run_id", table_name="scrape_run_profile_progress")
    op.drop_table("scrape_run_profile_progress")
