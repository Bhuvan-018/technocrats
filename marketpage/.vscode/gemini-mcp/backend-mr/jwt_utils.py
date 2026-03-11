import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, Optional, Tuple


JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
JWT_ISSUER = "market-brokerage"


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(message: bytes) -> str:
    signature = hmac.new(JWT_SECRET.encode("utf-8"), message, hashlib.sha256).digest()
    return _b64url_encode(signature)


def encode(payload: Dict[str, Any]) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = _sign(signing_input)
    return f"{header_b64}.{payload_b64}.{signature}"


def decode(token: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        header_b64, payload_b64, signature = token.split(".")
    except ValueError:
        return None, "invalid token format"

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected = _sign(signing_input)
    if not hmac.compare_digest(expected, signature):
        return None, "invalid signature"

    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception:
        return None, "invalid payload"

    if payload.get("iss") != JWT_ISSUER:
        return None, "invalid issuer"

    exp = payload.get("exp")
    if exp is not None and time.time() > float(exp):
        return None, "token expired"

    return payload, None


def build_access_token(user_id: str, ttl_seconds: int = 3600) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "typ": "access",
        "iss": JWT_ISSUER,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    return encode(payload)


def build_refresh_token(user_id: str, ttl_seconds: int = 60 * 60 * 24 * 30) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "typ": "refresh",
        "iss": JWT_ISSUER,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    return encode(payload)
