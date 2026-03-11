import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterable, Optional

try:
    import psycopg
    from psycopg.rows import dict_row
except Exception:  # pragma: no cover
    psycopg = None
    dict_row = None

try:
    import psycopg2
    import psycopg2.extras
except Exception:  # pragma: no cover
    psycopg2 = None


BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "brokerage.db")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))


def _ensure_dirs() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


@contextmanager
def get_conn():
    _ensure_dirs()
    if USE_POSTGRES:
        if psycopg is not None:
            conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        elif psycopg2 is not None:
            conn = psycopg2.connect(DATABASE_URL)
        else:
            raise RuntimeError("Postgres requested but no driver installed (psycopg or psycopg2)")
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    _ensure_dirs()
    with get_conn() as conn:
        schema = """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            subscription_tier TEXT NOT NULL,
            created_at TEXT NOT NULL,
            subscription_updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS refresh_tokens (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            ticker TEXT NOT NULL,
            company TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL,
            broker_order_id TEXT,
            timestamp TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            ticker TEXT NOT NULL,
            company TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS portfolio (
            user_id TEXT NOT NULL,
            ticker TEXT NOT NULL,
            company TEXT NOT NULL,
            quantity REAL NOT NULL,
            avg_buy_price REAL NOT NULL,
            current_price REAL NOT NULL,
            pnl REAL NOT NULL,
            PRIMARY KEY(user_id, ticker)
        );

        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            provider_order_id TEXT,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            plan TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS market_cache (
            cache_key TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS watchlist (
            user_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            name TEXT,
            created_at TEXT NOT NULL,
            PRIMARY KEY(user_id, symbol)
        );

        CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
        CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
        CREATE INDEX IF NOT EXISTS idx_portfolio_user ON portfolio(user_id);
        CREATE INDEX IF NOT EXISTS idx_refresh_user ON refresh_tokens(user_id);
        CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id);
        """
        if USE_POSTGRES:
            with conn.cursor() as cur:
                for stmt in schema.split(";"):
                    if stmt.strip():
                        cur.execute(stmt)
        else:
            conn.executescript(
                "PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;" + schema
            )


def _adapt_sql(sql: str) -> str:
    return sql.replace("?", "%s") if USE_POSTGRES else sql


def fetch_one(sql: str, params: Iterable[Any] = ()) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        if USE_POSTGRES:
            with conn.cursor() as cur:
                cur.execute(_adapt_sql(sql), tuple(params))
                row = cur.fetchone()
                if row is None:
                    return None
                if isinstance(row, dict):
                    return row
                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None


def fetch_all(sql: str, params: Iterable[Any] = ()) -> list[Dict[str, Any]]:
    with get_conn() as conn:
        if USE_POSTGRES:
            with conn.cursor() as cur:
                cur.execute(_adapt_sql(sql), tuple(params))
                rows = cur.fetchall()
                if rows and isinstance(rows[0], dict):
                    return list(rows)
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in rows]
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def execute(sql: str, params: Iterable[Any] = ()) -> None:
    with get_conn() as conn:
        if USE_POSTGRES:
            with conn.cursor() as cur:
                cur.execute(_adapt_sql(sql), tuple(params))
            return
        conn.execute(sql, params)


def execute_many(sql: str, params: Iterable[Iterable[Any]]) -> None:
    with get_conn() as conn:
        if USE_POSTGRES:
            with conn.cursor() as cur:
                cur.executemany(_adapt_sql(sql), params)
            return
        conn.executemany(sql, params)


def cache_get(cache_key: str) -> Optional[str]:
    row = fetch_one(
        "SELECT payload, expires_at FROM market_cache WHERE cache_key = ?",
        (cache_key,),
    )
    if not row:
        return None
    try:
        if float(row["expires_at"]) < float(datetime.utcnow().timestamp()):
            execute("DELETE FROM market_cache WHERE cache_key = ?", (cache_key,))
            return None
    except Exception:
        return None
    return row["payload"]


def cache_set(cache_key: str, payload: str, ttl_seconds: int) -> None:
    expires_at = str(float(datetime.utcnow().timestamp()) + float(ttl_seconds))
    execute(
        """
        INSERT INTO market_cache (cache_key, payload, updated_at, expires_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(cache_key) DO UPDATE SET
            payload=excluded.payload,
            updated_at=excluded.updated_at,
            expires_at=excluded.expires_at
        """,
        (cache_key, payload, str(datetime.utcnow().timestamp()), expires_at),
    )
