import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import Tuple


def _norm_base_url(url: str) -> str:
    return url.strip().rstrip("/")


def _required_config_missing(request_base_url: str | None = None) -> list[str]:
    missing: list[str] = []
    if not os.environ.get("PAYTM_MONEY_CLIENT_ID", "").strip():
        missing.append("PAYTM_MONEY_CLIENT_ID")
    if not os.environ.get("PAYTM_MONEY_API_KEY", "").strip():
        missing.append("PAYTM_MONEY_API_KEY")
    if not _resolve_base_url(request_base_url):
        missing.append("PUBLIC_BASE_URL")
    return missing


def _resolve_base_url(request_base_url: str | None = None) -> str:
    configured = _norm_base_url(os.environ.get("PUBLIC_BASE_URL", ""))
    if configured:
        return configured
    if request_base_url:
        return _norm_base_url(request_base_url)
    return ""


def build_callback_url(request_base_url: str | None = None) -> str:
    callback_path = os.environ.get("PAYTM_MONEY_CALLBACK_PATH", "/api/broker/paytm/callback").strip() or "/api/broker/paytm/callback"
    if not callback_path.startswith("/"):
        callback_path = "/" + callback_path
    base_url = _resolve_base_url(request_base_url)
    if not base_url:
        return ""
    return f"{base_url}{callback_path}"


def config_snapshot(request_base_url: str | None = None) -> dict:
    missing = _required_config_missing(request_base_url)
    callback_url = build_callback_url(request_base_url)
    return {
        "provider": "paytm_money",
        "configured": len(missing) == 0,
        "missing": missing,
        "api_base_url": os.environ.get("PAYTM_MONEY_API_BASE_URL", "https://developer.paytmmoney.com"),
        "callback_url": callback_url,
        "auth_base_url": os.environ.get("PAYTM_MONEY_AUTH_URL", "https://login.paytmmoney.com/authorize"),
        "token_url": os.environ.get("PAYTM_MONEY_TOKEN_URL", ""),
        "scopes": os.environ.get("PAYTM_MONEY_SCOPES", "orders holdings profile"),
        "has_access_token": bool(os.environ.get("PAYTM_MONEY_ACCESS_TOKEN", "").strip()),
        "note": "Set PUBLIC_BASE_URL to your deployed or tunnel URL so Paytm can call the callback URL.",
    }


def _safe_path(path: str) -> str:
    cleaned = (path or "").strip()
    if not cleaned.startswith("/"):
        raise ValueError("path must start with '/'")
    lowered = cleaned.lower()
    if lowered.startswith("//") or lowered.startswith("/http://") or lowered.startswith("/https://"):
        raise ValueError("absolute URLs are not allowed in path")
    return cleaned


def _resolve_token(jwt_token: str | None) -> str:
    token = (jwt_token or "").strip() or os.environ.get("PAYTM_MONEY_ACCESS_TOKEN", "").strip()
    return token


def call_paytm_api(method: str, path: str, query: dict | None = None, body: dict | None = None, jwt_token: str | None = None) -> Tuple[dict, int]:
    token = _resolve_token(jwt_token)
    if not token:
        return {"error": "missing jwt token", "hint": "Pass jwt_token in body/header or set PAYTM_MONEY_ACCESS_TOKEN"}, 401

    api_base = os.environ.get("PAYTM_MONEY_API_BASE_URL", "https://developer.paytmmoney.com").strip().rstrip("/")
    try:
        safe_path = _safe_path(path)
    except ValueError as exc:
        return {"error": str(exc)}, 400

    query = query or {}
    body = body or {}
    q = urllib.parse.urlencode({k: v for k, v in query.items() if v is not None and v != ""})
    url = f"{api_base}{safe_path}"
    if q:
        url = f"{url}?{q}"

    payload_bytes = None
    normalized_method = (method or "GET").upper()
    if normalized_method in ("POST", "PUT", "PATCH"):
        payload_bytes = json.dumps(body).encode("utf-8")

    headers = {
        "x-jwt-token": token,
        "Content-Type": "application/json",
    }
    api_key = os.environ.get("PAYTM_MONEY_API_KEY", "").strip()
    if api_key:
        headers["x-api-key"] = api_key

    req = urllib.request.Request(url, data=payload_bytes, headers=headers, method=normalized_method)
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = resp.read().decode("utf-8")
            content_type = (resp.headers.get("Content-Type") or "").lower()
            if "application/json" in content_type:
                parsed = json.loads(raw) if raw else {}
            else:
                parsed = {"raw": raw}
            return {
                "upstream_status": resp.status,
                "upstream_path": safe_path,
                "result": parsed,
            }, 200
    except urllib.error.HTTPError as exc:
        err_raw = exc.read().decode("utf-8", errors="ignore")
        try:
            err_json = json.loads(err_raw) if err_raw else {}
        except Exception:
            err_json = {"raw": err_raw}
        return {
            "error": "paytm api error",
            "upstream_status": exc.code,
            "upstream_path": safe_path,
            "details": err_json,
        }, 502
    except Exception as exc:
        return {"error": "paytm call failed", "details": str(exc)}, 502


def logout_session(jwt_token: str | None = None) -> Tuple[dict, int]:
    # Per Paytm docs: DELETE /accounts/v1/logout with x-jwt-token header.
    return call_paytm_api("DELETE", "/accounts/v1/logout", jwt_token=jwt_token)


def passthrough(payload: dict) -> Tuple[dict, int]:
    method = str(payload.get("method", "GET")).upper()
    path = str(payload.get("path", "")).strip()
    query = payload.get("query") or {}
    body = payload.get("body") or {}
    jwt_token = str(payload.get("jwt_token", "") or "").strip() or None

    if method not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        return {"error": "unsupported method"}, 400
    if not path:
        return {"error": "path is required"}, 400
    if not isinstance(query, dict):
        return {"error": "query must be an object"}, 400
    if not isinstance(body, dict):
        return {"error": "body must be an object"}, 400

    return call_paytm_api(method=method, path=path, query=query, body=body, jwt_token=jwt_token)


def build_connect_payload(user_id: str, request_base_url: str | None = None) -> Tuple[dict, int]:
    snapshot = config_snapshot(request_base_url)
    if not snapshot["configured"]:
        return {
            "error": "paytm broker is not configured",
            "config": snapshot,
        }, 400

    state = secrets.token_urlsafe(24)
    params = {
        "response_type": "code",
        "client_id": os.environ.get("PAYTM_MONEY_CLIENT_ID", "").strip(),
        "redirect_uri": snapshot["callback_url"],
        "scope": os.environ.get("PAYTM_MONEY_SCOPES", "orders holdings profile"),
        "state": state,
    }
    if user_id:
        params["login_hint"] = user_id
    auth_base = os.environ.get("PAYTM_MONEY_AUTH_URL", "https://login.paytmmoney.com/authorize")
    connect_url = f"{auth_base}?{urllib.parse.urlencode(params)}"
    return {
        "provider": "paytm_money",
        "connect_url": connect_url,
        "state": state,
        "callback_url": snapshot["callback_url"],
    }, 200


def handle_callback(query: dict, request_base_url: str | None = None) -> Tuple[dict, int]:
    error = (query.get("error", [""])[0] or "").strip()
    if error:
        return {"error": error, "description": (query.get("error_description", [""])[0] or "").strip()}, 400

    code = (query.get("code", [""])[0] or "").strip()
    state = (query.get("state", [""])[0] or "").strip()
    if not code:
        return {"error": "code is required"}, 400

    token_url = os.environ.get("PAYTM_MONEY_TOKEN_URL", "").strip()
    client_id = os.environ.get("PAYTM_MONEY_CLIENT_ID", "").strip()
    client_secret = os.environ.get("PAYTM_MONEY_CLIENT_SECRET", "").strip()
    callback_url = build_callback_url(request_base_url)

    if token_url and client_id and client_secret and callback_url:
        data = urllib.parse.urlencode(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": callback_url,
                "client_id": client_id,
                "client_secret": client_secret,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            token_url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                token_payload = json.loads(resp.read().decode("utf-8"))
            return {
                "provider": "paytm_money",
                "state": state,
                "code_received": True,
                "token": token_payload,
                "next_step": "Store access token securely and set PAYTM_MONEY_ACCESS_TOKEN in backend env.",
            }, 200
        except Exception as exc:
            return {
                "provider": "paytm_money",
                "state": state,
                "code_received": True,
                "token_exchange": "failed",
                "error": str(exc),
                "next_step": "Set PAYTM_MONEY_TOKEN_URL/PAYTM_MONEY_CLIENT_SECRET or exchange code manually.",
            }, 502

    return {
        "provider": "paytm_money",
        "state": state,
        "code_received": True,
        "authorization_code": code,
        "next_step": "Exchange this code for access token and set PAYTM_MONEY_ACCESS_TOKEN in backend env.",
    }, 200


def place_order(payload: dict) -> Tuple[str, str | None, str | None]:
    client_id = os.environ.get("PAYTM_MONEY_CLIENT_ID", "").strip()
    api_key = os.environ.get("PAYTM_MONEY_API_KEY", "").strip()
    access_token = os.environ.get("PAYTM_MONEY_ACCESS_TOKEN", "").strip()

    if not client_id or not api_key:
        return "ERROR", None, "missing PAYTM_MONEY_CLIENT_ID or PAYTM_MONEY_API_KEY"
    if not access_token:
        return "ERROR", None, "missing PAYTM_MONEY_ACCESS_TOKEN; complete /api/broker/paytm/connect flow"

    # This backend keeps trade-book as system-of-record and only creates a provider reference here.
    return "PENDING", f"PAYTM-{payload.get('order_id')}", None
