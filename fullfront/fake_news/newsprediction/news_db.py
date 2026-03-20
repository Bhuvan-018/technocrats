from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Iterable

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "live_news.db"


def _hash_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def init_db(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS live_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                title TEXT,
                summary TEXT,
                url TEXT,
                url_hash TEXT UNIQUE,
                published_at TEXT,
                inserted_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def upsert_articles(articles: Iterable[dict[str, str]], db_path: Path = DB_PATH) -> int:
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    inserted = 0
    try:
        for item in articles:
            url = (item.get("url") or "").strip()
            title = (item.get("title") or "").strip()
            summary = (item.get("summary") or "").strip()
            source = (item.get("source") or "").strip()
            published_at = (item.get("published_at") or "").strip()

            key_source = url or f"{source}|{title}|{summary}"
            url_hash = _hash_key(key_source)

            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO live_news
                    (source, title, summary, url, url_hash, published_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (source, title, summary, url, url_hash, published_at),
            )
            if cursor.rowcount:
                inserted += 1
        conn.commit()
    finally:
        conn.close()
    return inserted


def fetch_articles(days: int = 90, db_path: Path = DB_PATH) -> list[dict[str, str]]:
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(
            """
            SELECT source, title, summary, url, published_at
            FROM live_news
            WHERE inserted_at >= datetime('now', ?)
            ORDER BY inserted_at DESC
            """,
            (f"-{int(days)} days",),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
