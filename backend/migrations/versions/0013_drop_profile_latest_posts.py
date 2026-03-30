"""drop profile_latest_posts table (no-op placeholder)

Revision ID: 0013
Revises: 0012
Create Date: 2026-03-28
"""


revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Kept as a no-op placeholder to preserve migration chain continuity.
    pass


def downgrade() -> None:
    pass
