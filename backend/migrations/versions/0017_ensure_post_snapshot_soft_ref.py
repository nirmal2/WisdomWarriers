"""ensure post_snapshots.post_id has no FK to posts

Some environments are initialized from setup SQL instead of full Alembic history,
which can leave a foreign key from post_snapshots.post_id to posts.id in place.
The snapshots table is intended to be historical and must survive posts table resets.

Revision ID: 0017
Revises: 0016
Create Date: 2026-04-23
"""

from alembic import op


revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        DECLARE
            fk RECORD;
        BEGIN
            FOR fk IN
                SELECT con.conname
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
                JOIN pg_attribute att ON att.attrelid = rel.oid AND att.attnum = ANY(con.conkey)
                WHERE con.contype = 'f'
                  AND rel.relname = 'post_snapshots'
                  AND att.attname = 'post_id'
            LOOP
                EXECUTE format('ALTER TABLE post_snapshots DROP CONSTRAINT %I', fk.conname);
            END LOOP;
        END $$;
        """
    )


def downgrade() -> None:
    op.create_foreign_key(
        "post_snapshots_post_id_fkey",
        "post_snapshots",
        "posts",
        ["post_id"],
        ["id"],
    )
