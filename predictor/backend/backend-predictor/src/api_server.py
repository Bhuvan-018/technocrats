import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.backend_service import (
    BackendServiceError,
    backtest_payload,
    chart_payload,
    explainability_payload,
    list_companies,
    market_status_payload,
    predict_payload,
    trust_metrics_payload,
)


class APIServerHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Client-Info, Apikey")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _normalize_path(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "":
            path = "/"
        if path.startswith("/api"):
            path = path[4:] or "/"
        if path == "":
            path = "/"
        return path, parse_qs(parsed.query)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Client-Info, Apikey")
        self.end_headers()

    def do_GET(self):
        path, query = self._normalize_path()
        try:
            if path == "/health":
                self._send_json({"status": "ok", "build": "predictor-backend-2026-03-12"})
                return
            if path == "/debug/versions":
                try:
                    import keras
                    import tensorflow as tf
                    payload = {
                        "keras": getattr(keras, "__version__", "unknown"),
                        "tensorflow": getattr(tf, "__version__", "unknown"),
                    }
                except Exception as e:
                    payload = {"error": f"version_check_failed: {e}"}
                self._send_json(payload)
                return
            if path == "/market-status":
                self._send_json(market_status_payload())
                return
            if path == "/companies":
                self._send_json({"companies": list_companies()})
                return
            if path == "/analytics/trust":
                ticker = (query.get("ticker", [""])[0] or "").upper()
                self._send_json(trust_metrics_payload(ticker))
                return
            if path == "/analytics/explainability":
                ticker = (query.get("ticker", [""])[0] or "").upper()
                self._send_json(explainability_payload(ticker))
                return
            if path == "/analytics/backtest":
                ticker = (query.get("ticker", [""])[0] or "").upper()
                limit_raw = query.get("limit", ["10"])[0]
                horizon = query.get("horizon", ["10m"])[0]
                try:
                    limit = max(1, int(limit_raw))
                except ValueError:
                    limit = 10
                self._send_json(backtest_payload(ticker, limit=limit, horizon=horizon))
                return
            if path == "/chart":
                ticker = (query.get("ticker", [""])[0] or "").upper()
                period = query.get("period", ["2d"])[0]
                interval = query.get("interval", ["5m"])[0]
                self._send_json(chart_payload(ticker=ticker, period=period, interval=interval))
                return
            self._send_json({"error": "Endpoint not found"}, status=404)
        except BackendServiceError as e:
            self._send_json({"error": str(e)}, status=400)
        except Exception as e:
            self._send_json({"error": f"Internal server error: {e}"}, status=500)

    def do_POST(self):
        path, _ = self._normalize_path()
        try:
            if path != "/predict":
                self._send_json({"error": "Endpoint not found"}, status=404)
                return

            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                body = json.loads(raw_body.decode("utf-8"))
            except Exception:
                self._send_json({"error": "Invalid JSON body"}, status=400)
                return

            ticker = str(body.get("ticker", "")).upper().strip()
            allow_simulation = bool(body.get("allow_simulation", True))
            payload = predict_payload(ticker=ticker, allow_simulation=allow_simulation)
            self._send_json(payload, status=200)
        except BackendServiceError as e:
            self._send_json({"error": str(e)}, status=400)
        except Exception as e:
            self._send_json({"error": f"Internal server error: {e}"}, status=500)


def run_server(host: str = "127.0.0.1", port: int = 8000):
    server = ThreadingHTTPServer((host, port), APIServerHandler)
    print(f"Backend API server running on http://{host}:{port}")
    print("Endpoints: /health, /market-status, /companies, /predict, /analytics/*, /chart")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run local backend API server for frontend integration")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)
