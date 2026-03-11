import hashlib
import secrets
from datetime import datetime, timezone
from typing import Tuple

from db import execute, fetch_one
from jwt_utils import build_access_token, build_refresh_token, decode


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_user_id() -> str:
    return f"U{secrets.token_hex(4).upper()}"


def _make_token() -> str:
    return secrets.token_hex(24)


def _hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    if "$" not in stored:
        return False
    salt, _ = stored.split("$", 1)
    return _hash_password(password, salt) == stored


def signup(payload: dict) -> Tuple[dict, int]:
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()
    password = str(payload.get("password", "")).strip()
    if not name or not email or not password:
        return {"error": "name, email, password are required"}, 400

    existing = fetch_one("SELECT user_id FROM users WHERE email = ?", (email,))
    if existing:
        return {"error": "email already registered"}, 409

    user_id = _make_user_id()
    salt = secrets.token_hex(8)
    password_hash = _hash_password(password, salt)
    user = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "subscription_tier": "free",
        "created_at": _now_iso(),
    }
    execute(
        """
        INSERT INTO users (user_id, name, email, password_hash, subscription_tier, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, name, email, password_hash, "free", user["created_at"]),
    )

    access_token = build_access_token(user_id)
    refresh_token = build_refresh_token(user_id)
    execute(
        """
        INSERT INTO refresh_tokens (token, user_id, expires_at, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (refresh_token, user_id, str(datetime.now(timezone.utc).timestamp() + 60 * 60 * 24 * 30), _now_iso()),
    )
    return {
        "user_id": user_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "profile": user,
    }, 200


def login(payload: dict) -> Tuple[dict, int]:
    email = str(payload.get("email", "")).strip()
    password = str(payload.get("password", "")).strip()
    if not email or not password:
        return {"error": "email and password are required"}, 400

    user = fetch_one("SELECT * FROM users WHERE email = ?", (email,))
    if not user:
        return {"error": "user not found"}, 404
    if not _verify_password(password, user.get("password_hash", "")):
        return {"error": "invalid credentials"}, 401

    access_token = build_access_token(user["user_id"])
    refresh_token = build_refresh_token(user["user_id"])
    execute(
        """
        INSERT INTO refresh_tokens (token, user_id, expires_at, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (refresh_token, user["user_id"], str(datetime.now(timezone.utc).timestamp() + 60 * 60 * 24 * 30), _now_iso()),
    )
    return {
        "user_id": user["user_id"],
        "access_token": access_token,
        "refresh_token": refresh_token,
        "profile": {
            "user_id": user["user_id"],
            "name": user["name"],
            "email": user["email"],
            "subscription_tier": user["subscription_tier"],
        },
    }, 200


def profile(user_id: str) -> Tuple[dict, int]:
    user = fetch_one("SELECT user_id, name, email, subscription_tier FROM users WHERE user_id = ?", (user_id,))
    if not user:
        return {"error": "user not found"}, 404
    return {"profile": user}, 200


def subscription(user_id: str) -> Tuple[dict, int]:
    user = fetch_one("SELECT user_id, subscription_tier FROM users WHERE user_id = ?", (user_id,))
    if not user:
        return {"error": "user not found"}, 404
    return {
        "user_id": user["user_id"],
        "subscription_tier": user.get("subscription_tier", "free"),
    }, 200


def refresh_session(refresh_token: str) -> Tuple[dict, int]:
    if not refresh_token:
        return {"error": "refresh_token is required"}, 400

    payload, err = decode(refresh_token)
    if err or not payload or payload.get("typ") != "refresh":
        return {"error": "invalid refresh token"}, 401

    token_row = fetch_one("SELECT user_id, expires_at FROM refresh_tokens WHERE token = ?", (refresh_token,))
    if not token_row:
        return {"error": "refresh token not found"}, 401

    access_token = build_access_token(token_row["user_id"])
    new_refresh = build_refresh_token(token_row["user_id"])

    execute("DELETE FROM refresh_tokens WHERE token = ?", (refresh_token,))
    execute(
        """
        INSERT INTO refresh_tokens (token, user_id, expires_at, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (new_refresh, token_row["user_id"], str(datetime.now(timezone.utc).timestamp() + 60 * 60 * 24 * 30), _now_iso()),
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh,
    }, 200
