import os
import secrets
from datetime import datetime, timezone
from typing import Tuple

from db import execute, fetch_one
from payment_gateway import create_payment


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


PLAN_PRICING = {
    "monthly": 199,
    "quarterly": 500,
    "halfyear": 1000,
}


def create_order(payload: dict) -> Tuple[dict, int]:
    user_id = str(payload.get("user_id", "")).strip()
    plan = str(payload.get("plan", "monthly")).strip().lower()
    amount = float(payload.get("amount", 0) or 0)
    if not user_id:
        return {"error": "user_id is required"}, 400
    if amount <= 0:
        amount = float(PLAN_PRICING.get(plan, 0))
    if amount <= 0:
        return {"error": "invalid plan or amount"}, 400

    if fetch_one("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) is None:
        return {"error": "user not found"}, 404

    status, provider_order_id, error = create_payment(amount, "INR", user_id, plan)
    if status == "ERROR":
        return {"error": error or "payment provider error"}, 502

    payment_id = f"PAY{secrets.token_hex(4).upper()}"
    provider_name = os.environ.get("PAYMENT_PROVIDER", "local")
    payment = {
        "payment_id": payment_id,
        "user_id": user_id,
        "provider": provider_name,
        "provider_order_id": provider_order_id,
        "amount": amount,
        "currency": "INR",
        "plan": plan,
        "status": status,
        "created_at": _now_iso(),
    }
    execute(
        """
        INSERT INTO payments (payment_id, user_id, provider, provider_order_id, amount, currency, plan, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payment_id,
            user_id,
            payment["provider"],
            provider_order_id,
            amount,
            "INR",
            plan,
            payment["status"],
            payment["created_at"],
        ),
    )
    return payment, 200


def verify(payload: dict) -> Tuple[dict, int]:
    payment_id = str(payload.get("payment_id", "")).strip()
    if not payment_id:
        return {"error": "payment_id is required"}, 400
    payment = fetch_one("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
    if not payment:
        return {"error": "payment not found"}, 404
    execute("UPDATE payments SET status = ? WHERE payment_id = ?", ("VERIFIED", payment_id))
    payment["status"] = "VERIFIED"
    return dict(payment), 200


def activate_subscription(payload: dict) -> Tuple[dict, int]:
    user_id = str(payload.get("user_id", "")).strip()
    tier = str(payload.get("tier", "pro")).strip()
    user = fetch_one("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not user:
        return {"error": "user not found"}, 404
    execute(
        "UPDATE users SET subscription_tier = ?, subscription_updated_at = ? WHERE user_id = ?",
        (tier or "pro", _now_iso(), user_id),
    )
    return {"user_id": user_id, "subscription_tier": tier or "pro"}, 200
