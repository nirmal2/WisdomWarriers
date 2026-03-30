"""add additional fields to posts

Revision ID: 0012
Revises: 0011
Create Date: 2026-03-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("posts", sa.Column("owner_id", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("owner_profile_pic_url", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("video_view_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("posts", sa.Column("audio_url", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("video_duration", sa.Float(), nullable=True))
    op.add_column("posts", sa.Column("dimensions_height", sa.Integer(), nullable=True))
    op.add_column("posts", sa.Column("dimensions_width", sa.Integer(), nullable=True))
    op.add_column("posts", sa.Column("is_comments_disabled", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("posts", sa.Column("alt", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("comments_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column(
        "posts",
        sa.Column(
            "latest_comments",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "posts",
        sa.Column(
            "images",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "posts",
        sa.Column(
            "child_posts",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "posts",
        sa.Column(
            "music_info",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("posts", "music_info")
    op.drop_column("posts", "child_posts")
    op.drop_column("posts", "images")
    op.drop_column("posts", "latest_comments")
    op.drop_column("posts", "comments_count")
    op.drop_column("posts", "alt")
    op.drop_column("posts", "is_comments_disabled")
    op.drop_column("posts", "dimensions_width")
    op.drop_column("posts", "dimensions_height")
    op.drop_column("posts", "video_duration")
    op.drop_column("posts", "audio_url")
    op.drop_column("posts", "video_view_count")
    op.drop_column("posts", "owner_profile_pic_url")
    op.drop_column("posts", "owner_id")
