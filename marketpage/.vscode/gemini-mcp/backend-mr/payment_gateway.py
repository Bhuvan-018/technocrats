import base64
import json
import os
import time
import urllib.request
from typing import Tuple


def create_payment(amount: float, currency: str, user_id: str, plan: str) -> Tuple[str, str | None, str | None]:
    provider = os.environ.get("PAYMENT_PROVIDER", "local").lower()
    if provider in ("", "local", "demo"):
        return "CREATED", None, None

    if provider == "razorpay":
        key = os.environ.get("RAZORPAY_KEY_ID")
        secret = os.environ.get("RAZORPAY_KEY_SECRET")
        if not key or not secret:
            return "ERROR", None, "missing Razorpay credentials"

        payload = {
            "amount": int(amount * 100),
            "currency": currency,
            "receipt": f"{user_id}-{plan}-{int(time.time())}",
        }
        auth = base64.b64encode(f"{key}:{secret}".encode("utf-8")).decode("utf-8")
        req = urllib.request.Request(
            "https://api.razorpay.com/v1/orders",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Basic {auth}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                response = json.loads(resp.read().decode("utf-8"))
            order_id = response.get("id")
            if not order_id:
                return "ERROR", None, "Razorpay order id missing"
            return "CREATED", order_id, None
        except Exception as exc:
            return "ERROR", None, str(exc)

    if provider == "paytm":
        key = os.environ.get("PAYTM_MERCHANT_ID")
        secret = os.environ.get("PAYTM_MERCHANT_KEY")
        if not key or not secret:
            return "ERROR", None, "missing Paytm credentials"
        return "CREATED", None, None

    return "ERROR", None, "unknown payment provider"
