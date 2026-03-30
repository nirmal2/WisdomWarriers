"""add category and grade to scrape_profiles

Revision ID: 0015
Revises: 0014
Create Date: 2026-03-30
"""

from alembic import op
import sqlalchemy as sa


revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


CATEGORY_VALUES = ("Dedicated", "In-house influencer")
GRADE_VALUES = ("A", "B", "C", "D", "E")


def upgrade() -> None:
    op.add_column("scrape_profiles", sa.Column("category", sa.Text(), nullable=True))
    op.add_column("scrape_profiles", sa.Column("grade", sa.Text(), nullable=True))
    op.create_check_constraint(
        "scrape_profiles_category_check",
        "scrape_profiles",
        sa.text("category is null or category in ('Dedicated', 'In-house influencer')"),
    )
    op.create_check_constraint(
        "scrape_profiles_grade_check",
        "scrape_profiles",
        sa.text("grade is null or grade in ('A', 'B', 'C', 'D', 'E')"),
    )


def downgrade() -> None:
    op.drop_constraint("scrape_profiles_grade_check", "scrape_profiles", type_="check")
    op.drop_constraint("scrape_profiles_category_check", "scrape_profiles", type_="check")
    op.drop_column("scrape_profiles", "grade")
    op.drop_column("scrape_profiles", "category")
