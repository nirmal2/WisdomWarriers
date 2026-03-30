"""add more fields to posts from Apify payload

Revision ID: 0014
Revises: 0013
Create Date: 2026-03-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("posts", sa.Column("source_post_id", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("short_code", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("location_name", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("location_id", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("first_comment", sa.Text(), nullable=True))
    op.add_column(
        "posts",
        sa.Column(
            "mentions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "posts",
        sa.Column(
            "tagged_users",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "posts",
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("posts", "is_pinned")
    op.drop_column("posts", "tagged_users")
    op.drop_column("posts", "mentions")
    op.drop_column("posts", "first_comment")
    op.drop_column("posts", "location_id")
    op.drop_column("posts", "location_name")
    op.drop_column("posts", "short_code")
    op.drop_column("posts", "source_post_id")
