"""initial schema

Revision ID: 0001_initial
Revises: None
Create Date: 2026-03-10
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("user_id", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("subscription_tier", sa.Text(), nullable=False, server_default="free"),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("subscription_updated_at", sa.Text(), nullable=True),
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("token", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
    )
    op.create_table(
        "orders",
        sa.Column("order_id", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("ticker", sa.Text(), nullable=False),
        sa.Column("company", sa.Text(), nullable=False),
        sa.Column("side", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("broker_order_id", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.Text(), nullable=False),
    )
    op.create_table(
        "transactions",
        sa.Column("transaction_id", sa.Text(), primary_key=True),
        sa.Column("order_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("ticker", sa.Text(), nullable=False),
        sa.Column("company", sa.Text(), nullable=False),
        sa.Column("side", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.Text(), nullable=False),
    )
    op.create_table(
        "portfolio",
        sa.Column("user_id", sa.Text(), primary_key=True),
        sa.Column("ticker", sa.Text(), primary_key=True),
        sa.Column("company", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("avg_buy_price", sa.Float(), nullable=False),
        sa.Column("current_price", sa.Float(), nullable=False),
        sa.Column("pnl", sa.Float(), nullable=False),
    )
    op.create_table(
        "payments",
        sa.Column("payment_id", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("provider_order_id", sa.Text(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.Text(), nullable=False),
        sa.Column("plan", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
    )
    op.create_table(
        "market_cache",
        sa.Column("cache_key", sa.Text(), primary_key=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.Text(), nullable=False),
    )

    op.create_index("idx_orders_user", "orders", ["user_id"])
    op.create_index("idx_transactions_user", "transactions", ["user_id"])
    op.create_index("idx_portfolio_user", "portfolio", ["user_id"])
    op.create_index("idx_refresh_user", "refresh_tokens", ["user_id"])


def downgrade():
    op.drop_index("idx_refresh_user", table_name="refresh_tokens")
    op.drop_index("idx_portfolio_user", table_name="portfolio")
    op.drop_index("idx_transactions_user", table_name="transactions")
    op.drop_index("idx_orders_user", table_name="orders")
    op.drop_table("market_cache")
    op.drop_table("payments")
    op.drop_table("portfolio")
    op.drop_table("transactions")
    op.drop_table("orders")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
