import secrets
from datetime import datetime, timezone
from typing import Tuple

from broker_adapter import place_order as broker_place_order
from db import execute, fetch_all, fetch_one


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_order_id() -> str:
    return f"ORD{secrets.token_hex(3).upper()}"


def _build_position(existing: dict | None, payload: dict) -> dict:
    ticker = str(payload.get("ticker", "")).upper()
    company = str(payload.get("company", "")).strip() or ticker
    quantity = float(payload.get("quantity", 0) or 0)
    price = float(payload.get("price", 0) or 0)
    side = str(payload.get("type", "BUY")).upper()

    if existing is None:
        existing = {
            "ticker": ticker,
            "company": company,
            "quantity": 0.0,
            "avg_buy_price": 0.0,
            "current_price": price,
            "pnl": 0.0,
        }

    if side == "BUY":
        total_cost = existing["avg_buy_price"] * existing["quantity"] + price * quantity
        new_qty = existing["quantity"] + quantity
        avg_price = total_cost / new_qty if new_qty > 0 else 0.0
        existing["quantity"] = new_qty
        existing["avg_buy_price"] = avg_price
        existing["current_price"] = price
    else:
        existing["quantity"] = max(0.0, existing["quantity"] - quantity)
        existing["current_price"] = price

    existing["pnl"] = (existing["current_price"] - existing["avg_buy_price"]) * existing["quantity"]
    return existing


def _validate_trade_payload(payload: dict) -> Tuple[dict | None, dict | None]:
    user_id = str(payload.get("user_id", "")).strip()
    ticker = str(payload.get("ticker", "")).strip()
    quantity = payload.get("quantity")
    price = payload.get("price")
    if not user_id or not ticker or quantity is None or price is None:
        return None, {"error": "user_id, ticker, quantity, price are required"}
    return {
        "user_id": user_id,
        "ticker": ticker,
        "company": str(payload.get("company", "")).strip(),
        "quantity": float(quantity),
        "price": float(price),
    }, None


def place_order(payload: dict, side: str) -> Tuple[dict, int]:
    normalized, err = _validate_trade_payload(payload)
    if err:
        return err, 400

    user_id = normalized["user_id"]
    if fetch_one("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) is None:
        return {"error": "user not found"}, 404

    order_id = _make_order_id()
    broker_status, broker_order_id, broker_error = broker_place_order({"order_id": order_id, **normalized, "side": side})
    if broker_status == "ERROR":
        return {"error": broker_error or "broker error"}, 502

    order = {
        "order_id": order_id,
        "user_id": user_id,
        "ticker": normalized["ticker"].upper(),
        "company": normalized["company"] or normalized["ticker"].upper(),
        "type": side,
        "quantity": normalized["quantity"],
        "price": normalized["price"],
        "status": broker_status,
        "broker_order_id": broker_order_id,
        "timestamp": _now_iso(),
    }
    execute(
        """
        INSERT INTO orders (order_id, user_id, ticker, company, side, quantity, price, status, broker_order_id, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            order_id,
            user_id,
            order["ticker"],
            order["company"],
            side,
            order["quantity"],
            order["price"],
            order["status"],
            order["broker_order_id"],
            order["timestamp"],
        ),
    )

    transaction = {
        "transaction_id": f"TXN{secrets.token_hex(4).upper()}",
        "order_id": order_id,
        "user_id": user_id,
        "ticker": order["ticker"],
        "company": order["company"],
        "type": side,
        "quantity": order["quantity"],
        "price": order["price"],
        "status": order["status"],
        "timestamp": order["timestamp"],
    }
    execute(
        """
        INSERT INTO transactions (transaction_id, order_id, user_id, ticker, company, side, quantity, price, status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            transaction["transaction_id"],
            order_id,
            user_id,
            order["ticker"],
            order["company"],
            side,
            order["quantity"],
            order["price"],
            transaction["status"],
            order["timestamp"],
        ),
    )

    existing = fetch_one(
        "SELECT * FROM portfolio WHERE user_id = ? AND ticker = ?",
        (user_id, order["ticker"]),
    )
    position = _build_position(existing, {**normalized, "type": side})
    position["ticker"] = order["ticker"]
    position["company"] = order["company"]
    execute(
        """
        INSERT INTO portfolio (user_id, ticker, company, quantity, avg_buy_price, current_price, pnl)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, ticker) DO UPDATE SET
            company=excluded.company,
            quantity=excluded.quantity,
            avg_buy_price=excluded.avg_buy_price,
            current_price=excluded.current_price,
            pnl=excluded.pnl
        """,
        (
            user_id,
            order["ticker"],
            order["company"],
            position["quantity"],
            position["avg_buy_price"],
            position["current_price"],
            position["pnl"],
        ),
    )

    return {"order": order, "transaction": transaction}, 200


def portfolio(user_id: str) -> Tuple[dict, int]:
    if fetch_one("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) is None:
        return {"error": "user not found"}, 404
    holdings = fetch_all("SELECT * FROM portfolio WHERE user_id = ?", (user_id,))
    total_value = sum(h.get("current_price", 0.0) * h.get("quantity", 0.0) for h in holdings)
    total_pnl = sum(h.get("pnl", 0.0) for h in holdings)
    return {
        "user_id": user_id,
        "portfolio": holdings,
        "total_value": total_value,
        "total_pnl": total_pnl,
        "last_updated": _now_iso(),
    }, 200


def history(user_id: str) -> Tuple[dict, int]:
    if fetch_one("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) is None:
        return {"error": "user not found"}, 404
    return {
        "user_id": user_id,
        "transactions": fetch_all(
            "SELECT * FROM transactions WHERE user_id = ? ORDER BY timestamp DESC",
            (user_id,),
        ),
    }, 200


def order_status(order_id: str) -> Tuple[dict, int]:
    order = fetch_one("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    if not order:
        return {"error": "order not found"}, 404
    return order, 200


def dashboard(user_id: str) -> Tuple[dict, int]:
    if fetch_one("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) is None:
        return {"error": "user not found"}, 404

    holdings = fetch_all("SELECT * FROM portfolio WHERE user_id = ?", (user_id,))
    orders = fetch_all(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY timestamp DESC",
        (user_id,),
    )
    txns = fetch_all(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10",
        (user_id,),
    )

    total_value = sum(h.get("current_price", 0.0) * h.get("quantity", 0.0) for h in holdings)
    total_pnl = sum(h.get("pnl", 0.0) for h in holdings)
    open_orders = [o for o in orders if str(o.get("status", "")).upper() not in ("EXECUTED", "VERIFIED", "COMPLETED")]

    return {
        "user_id": user_id,
        "summary": {
            "total_value": total_value,
            "total_pnl": total_pnl,
            "holdings_count": len(holdings),
            "open_orders_count": len(open_orders),
            "orders_count": len(orders),
        },
        "holdings": holdings,
        "recent_transactions": txns,
        "recent_orders": orders[:10],
        "last_updated": _now_iso(),
    }, 200
