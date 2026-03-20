import os
from typing import Tuple

from services.angelone_broker_service import place_order as angelone_place_order


def place_order(payload: dict) -> Tuple[str, str | None, str | None]:
    provider = os.environ.get("BROKER_PROVIDER", "paper").lower()
    if provider in ("", "paper", "demo"):
        return "EXECUTED", None, None

    if provider == "zerodha":
        api_key = os.environ.get("ZERODHA_API_KEY")
        access_token = os.environ.get("ZERODHA_ACCESS_TOKEN")
        if not api_key or not access_token:
            return "ERROR", None, "missing Zerodha credentials"
        return "PENDING", f"ZER-{payload.get('order_id')}", None

    if provider == "upstox":
        api_key = os.environ.get("UPSTOX_API_KEY")
        access_token = os.environ.get("UPSTOX_ACCESS_TOKEN")
        if not api_key or not access_token:
            return "ERROR", None, "missing Upstox credentials"
        return "PENDING", f"UPX-{payload.get('order_id')}", None

    if provider in ("angelone", "angel", "paytm", "paytm_money", "paytmmoney"):
        return angelone_place_order(payload)

    return "ERROR", None, "unknown broker provider"
