"""add watchlist

Revision ID: 0002_watchlist
Revises: 0001_initial
Create Date: 2026-03-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_watchlist"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "watchlist",
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "symbol"),
    )
    op.create_index("idx_watchlist_user", "watchlist", ["user_id"])


def downgrade():
    op.drop_index("idx_watchlist_user", table_name="watchlist")
    op.drop_table("watchlist")
