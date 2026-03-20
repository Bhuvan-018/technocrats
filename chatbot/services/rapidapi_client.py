import json
import os
from dataclasses import dataclass
from typing import Any, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass
class RapidAPIConfig:
    host: str
    key: str


def load_config() -> RapidAPIConfig:
    host = os.environ.get("RAPIDAPI_HOST", "chatgpt-42.p.rapidapi.com").strip()
    key = os.environ.get("RAPIDAPI_KEY", "909e2e0691msh699f5f24498ee36p127bd0jsne163c06864f9").strip()
    return RapidAPIConfig(host=host, key=key)


def load_chat_config() -> RapidAPIConfig:
    host = os.environ.get("RAPIDAPI_CHAT_HOST", "").strip()
    key = os.environ.get("RAPIDAPI_CHAT_KEY", "").strip()
    if host:
        return RapidAPIConfig(host=host, key=key or os.environ.get("RAPIDAPI_KEY", "").strip())
    return load_config()


def request_json(
    config: RapidAPIConfig,
    path: str,
    method: str = "GET",
    payload: dict | None = None,
    params: dict | None = None,
    timeout: int = 20,
) -> Tuple[Any, int]:
    if not config.key:
        return {"error": "RAPIDAPI_KEY not set"}, 500

    url = f"https://{config.host}{path}"
    if params:
        query = urlencode({k: v for k, v in params.items() if v is not None})
        if query:
            url = f"{url}?{query}"
    headers = {
        "X-RapidAPI-Key": config.key,
        "X-RapidAPI-Host": config.host,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "STOCKY/1.0",
    }
    data = None
    if payload is not None and method.upper() != "GET":
        data = json.dumps(payload).encode("utf-8")

    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            status = resp.status
    except HTTPError as exc:
        try:
            body = exc.read()
        except Exception:
            body = b""
        return _decode_body(body, fallback="RapidAPI error"), exc.code
    except URLError as exc:
        return {"error": f"RapidAPI connection failed: {exc.reason}"}, 502

    return _decode_body(body), status


def _decode_body(body: bytes, fallback: str | None = None) -> Any:
    if not body:
        return {} if fallback is None else {"error": fallback}
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        if fallback is None:
            return {"raw": body.decode("utf-8", errors="ignore")}
        return {"error": fallback, "raw": body.decode("utf-8", errors="ignore")}
