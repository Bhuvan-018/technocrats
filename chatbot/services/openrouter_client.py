import json
import os
from dataclasses import dataclass
from typing import Any, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class OpenRouterConfig:
    api_key: str
    model: str
    referer: str | None
    title: str | None


def load_openrouter_config() -> OpenRouterConfig | None:
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return None
    model = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
    referer = os.environ.get("OPENROUTER_REFERER", "").strip() or None
    title = os.environ.get("OPENROUTER_TITLE", "").strip() or None
    return OpenRouterConfig(api_key=api_key, model=model, referer=referer, title=title)


def request_openrouter(
    config: OpenRouterConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.9,
    max_tokens: int = 256,
    timeout: int = 60,
) -> Tuple[Any, int]:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if config.referer:
        headers["HTTP-Referer"] = config.referer
    if config.title:
        headers["X-Title"] = config.title

    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = json.dumps(payload).encode("utf-8")

    req = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            status = resp.status
    except HTTPError as exc:
        try:
            body = exc.read()
        except Exception:
            body = b""
        return _decode_body(body, fallback="OpenRouter error"), exc.code
    except URLError as exc:
        return {"error": f"OpenRouter connection failed: {exc.reason}"}, 502

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
