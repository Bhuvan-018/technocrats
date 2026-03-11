from sqlalchemy import Column, Float, String, Text, UniqueConstraint

from sa_db import Base


class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    subscription_tier = Column(Text, nullable=False, default="free")
    created_at = Column(Text, nullable=False)
    subscription_updated_at = Column(Text)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    token = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=False)
    expires_at = Column(Text, nullable=False)
    created_at = Column(Text, nullable=False)


class Order(Base):
    __tablename__ = "orders"
    order_id = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=False)
    ticker = Column(Text, nullable=False)
    company = Column(Text, nullable=False)
    side = Column(Text, nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(Text, nullable=False)
    broker_order_id = Column(Text)
    timestamp = Column(Text, nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"
    transaction_id = Column(Text, primary_key=True)
    order_id = Column(Text, nullable=False)
    user_id = Column(Text, nullable=False)
    ticker = Column(Text, nullable=False)
    company = Column(Text, nullable=False)
    side = Column(Text, nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(Text, nullable=False)
    timestamp = Column(Text, nullable=False)


class Portfolio(Base):
    __tablename__ = "portfolio"
    user_id = Column(Text, primary_key=True)
    ticker = Column(Text, primary_key=True)
    company = Column(Text, nullable=False)
    quantity = Column(Float, nullable=False)
    avg_buy_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    pnl = Column(Float, nullable=False)


class Payment(Base):
    __tablename__ = "payments"
    payment_id = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=False)
    provider = Column(Text, nullable=False)
    provider_order_id = Column(Text)
    amount = Column(Float, nullable=False)
    currency = Column(Text, nullable=False)
    plan = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    created_at = Column(Text, nullable=False)


class MarketCache(Base):
    __tablename__ = "market_cache"
    cache_key = Column(Text, primary_key=True)
    payload = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)
    expires_at = Column(Text, nullable=False)


__all__ = [
    "User",
    "RefreshToken",
    "Order",
    "Transaction",
    "Portfolio",
    "Payment",
    "MarketCache",
]
