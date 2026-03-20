import argparse
import json
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency
    load_dotenv = None

from services.openrouter_client import load_openrouter_config, request_openrouter
from services.rapidapi_client import load_chat_config, load_config, request_json

if load_dotenv is not None:
    load_dotenv(Path(__file__).resolve().parent / ".env")


class StockyHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return {}
        raw = self.rfile.read(content_length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/health":
            self._send_json({"status": "ok", "name": "STOCKY"})
            return
        if path == "/ping":
            payload, status = request_json(
                load_config(),
                "/market/v2/get-quotes",
                method="GET",
                params={"symbols": "AAPL", "region": "US"},
            )
            self._send_json(payload, status)
            return
        self._send_json({"error": "Endpoint not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        body = self._read_json()
        config = load_config()
        openrouter_config = load_openrouter_config()

        if path == "/chat":
            try:
                chat_config = load_chat_config()
                messages = body.get("messages")
                if not isinstance(messages, list) or not messages:
                    question = str(body.get("question") or body.get("prompt") or "hello").strip()
                    messages = [{"role": "user", "content": question or "hello"}]

                stock = str(body.get("stock") or body.get("symbol") or "").upper()
                period = str(body.get("period") or "1mo")
                conversation_id = str(body.get("conversation_id") or "")

                if "yahoo-finance160" in chat_config.host:
                    payload, status = request_json(
                        chat_config,
                        "/finbot",
                        method="POST",
                        payload={
                            "messages": messages,
                            "stock": stock or "TSLA",
                            "conversation_id": conversation_id,
                            "period": period,
                        },
                        timeout=90,
                    )
                elif openrouter_config is not None:
                    payload, status = request_openrouter(
                        openrouter_config,
                        messages=messages,
                        temperature=float(body.get("temperature") or 0.9),
                        max_tokens=int(body.get("max_tokens") or 256),
                        timeout=90,
                    )
                elif "cheapest-gpt-4-turbo-gpt-4-vision-chatgpt-openai-ai-api" in chat_config.host:
                    payload, status = request_json(
                        chat_config,
                        "/v1/chat/completions",
                        method="POST",
                        payload={
                            "messages": messages,
                            "model": str(body.get("model") or "gpt-4o"),
                            "max_tokens": int(body.get("max_tokens") or 256),
                            "temperature": float(body.get("temperature") or 0.9),
                        },
                        timeout=90,
                    )
                else:
                    payload, status = request_json(
                        chat_config,
                        "/conversationgpt4-2",
                        method="POST",
                        payload={
                            "messages": messages,
                            "system_prompt": str(body.get("system_prompt") or ""),
                            "temperature": float(body.get("temperature") or 0.9),
                            "top_k": int(body.get("top_k") or 5),
                            "top_p": float(body.get("top_p") or 0.9),
                            "max_tokens": int(body.get("max_tokens") or 256),
                            "web_access": bool(body.get("web_access") if body.get("web_access") is not None else False),
                        },
                        timeout=90,
                    )

                answer = (
                    payload.get("result")
                    or payload.get("answer")
                    or payload.get("response")
                    or payload.get("message")
                    or payload.get("content")
                )

                if not answer and isinstance(payload, dict):
                    choices = payload.get("choices") or []
                    if choices:
                        msg = choices[0].get("message") or {}
                        answer = msg.get("content")

                if isinstance(answer, dict):
                    answer = answer.get("content") or answer.get("text") or json.dumps(answer)

                if not answer:
                    answer = "No response from RapidAPI model."

                self._send_json({"answer": str(answer), "raw": payload}, status)
            except Exception as exc:
                self._send_json({"error": f"chat request failed: {exc}"}, 500)
            return

        if path == "/stock/recommendations":
            symbol = str(body.get("stock") or body.get("symbol") or "").upper()
            payload, status = request_json(
                config,
                "/stock/v2/get-recommendations",
                method="GET",
                params={"symbol": symbol},
            )
            self._send_json(payload, status)
            return

        if path == "/stock/profile":
            symbol = str(body.get("stock") or body.get("symbol") or "").upper()
            payload, status = request_json(
                config,
                "/stock/v3/get-profile",
                method="GET",
                params={"symbol": symbol, "region": "US"},
            )
            self._send_json(payload, status)
            return

        if path == "/stock/insights":
            symbol = str(body.get("stock") or body.get("symbol") or "").upper()
            payload, status = request_json(
                config,
                "/stock/v2/get-insights",
                method="GET",
                params={"symbol": symbol},
            )
            self._send_json(payload, status)
            return

        if path == "/stock/quote":
            symbols = body.get("symbols") or body.get("symbol") or ""
            if isinstance(symbols, list):
                symbols = ",".join(symbols)
            payload, status = request_json(
                config,
                "/market/v2/get-quotes",
                method="GET",
                params={"symbols": symbols, "region": body.get("region", "US")},
            )
            self._send_json(payload, status)
            return

        if path == "/stock/chart":
            symbol = str(body.get("stock") or body.get("symbol") or "").upper()
            payload, status = request_json(
                config,
                "/stock/v3/get-chart",
                method="GET",
                params={
                    "symbol": symbol,
                    "interval": body.get("interval", "1d"),
                    "range": body.get("range", "1mo"),
                    "region": body.get("region", "US"),
                },
            )
            self._send_json(payload, status)
            return

        self._send_json({"error": "Endpoint not found"}, 404)


def run(host: str = "127.0.0.1", port: int = 7000) -> None:
    server = ThreadingHTTPServer((host, port), StockyHandler)
    print(f"STOCKY backend running on http://{host}:{port}")
    print("Endpoints: /health, /ping, /chat, /stock/*")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="STOCKY chatbot backend")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7000)
    args = parser.parse_args()
    run(host=args.host, port=args.port)
