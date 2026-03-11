import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from services.rapidapi_client import load_config, request_json


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

        if path == "/chat":
            symbol = str(body.get("stock") or body.get("symbol") or "AAPL").upper()
            messages = body.get("messages") or []
            question = ""
            if messages and isinstance(messages, list):
                question = str(messages[-1].get("content") or "").strip()

            quote_payload, _ = request_json(
                config,
                "/market/v2/get-quotes",
                method="GET",
                params={"symbols": symbol, "region": "US"},
            )
            rec_payload, _ = request_json(
                config,
                "/stock/v2/get-recommendations",
                method="GET",
                params={"symbol": symbol},
            )
            profile_payload, _ = request_json(
                config,
                "/stock/v3/get-profile",
                method="GET",
                params={"symbol": symbol, "region": "US"},
            )
            insights_payload, _ = request_json(
                config,
                "/stock/v2/get-insights",
                method="GET",
                params={"symbol": symbol},
            )

            summary_parts = []
            if question:
                summary_parts.append(f"Question: {question}")

            quote_result = (
                quote_payload.get("quoteResponse", {})
                .get("result", [])
            )
            if quote_result:
                first = quote_result[0]
                name = first.get("shortName") or first.get("longName")
                price = first.get("regularMarketPrice")
                change = first.get("regularMarketChange")
                change_pct = first.get("regularMarketChangePercent")
                if name:
                    summary_parts.append(f"Name: {name}.")
                if price is not None:
                    change_str = ""
                    if change is not None and change_pct is not None:
                        sign = "+" if change >= 0 else ""
                        change_str = f" ({sign}{change:.2f}, {sign}{change_pct:.2f}%)"
                    summary_parts.append(f"Price: {price:.2f}{change_str}.")

            recs = (
                rec_payload.get("finance", {})
                .get("result", [{}])[0]
                .get("recommendedSymbols", [])
            )
            if recs:
                top = ", ".join([r.get("symbol", "") for r in recs[:5] if r.get("symbol")])
                if top:
                    summary_parts.append(f"Related tickers: {top}.")

            company_name = (
                profile_payload.get("quoteSummary", {})
                .get("result", [{}])[0]
                .get("price", {})
                .get("longName")
            )
            if company_name:
                summary_parts.append(f"Company: {company_name}.")

            insight = (
                insights_payload.get("finance", {})
                .get("result", {})
                .get("instrumentInfo", {})
                .get("summary")
            )
            if insight:
                summary_parts.append(f"Insight: {insight}")

            if len(summary_parts) == 1 and question:
                summary_parts.append("No additional insights available right now.")
            answer = " ".join(summary_parts) if summary_parts else "No insights available right now."
            self._send_json({"answer": answer, "symbol": symbol})
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
