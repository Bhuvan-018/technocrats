from datetime import datetime, timezone
from typing import Tuple

from db import execute, fetch_all, fetch_one
from services.market_data_service import get_company_quotes


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_watchlist(user_id: str) -> Tuple[list[dict], int]:
    rows = fetch_all("SELECT symbol, name FROM watchlist WHERE user_id = ?", (user_id,))
    symbols = [row["symbol"] for row in rows]
    quotes = get_company_quotes(symbols)
    return quotes, 200


def add_watchlist(user_id: str, symbol: str, name: str | None = None) -> Tuple[dict, int]:
    if not symbol:
        return {"error": "symbol is required"}, 400
    execute(
        """
        INSERT INTO watchlist (user_id, symbol, name, created_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, symbol) DO NOTHING
        """,
        (user_id, symbol.upper(), name or "", _now_iso()),
    )
    return {"status": "ok"}, 200


def remove_watchlist(user_id: str, symbol: str) -> Tuple[dict, int]:
    if not symbol:
        return {"error": "symbol is required"}, 400
    execute("DELETE FROM watchlist WHERE user_id = ? AND symbol = ?", (user_id, symbol.upper()))
    return {"status": "ok"}, 200
