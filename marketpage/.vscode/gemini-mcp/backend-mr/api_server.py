import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

from services.market_data_service import chart, companies, get_indices, market_status, oil_price
from services.angelone_broker_service import (
    build_connect_payload as angel_build_connect_payload,
    config_snapshot as angel_config_snapshot,
    handle_callback as angel_handle_callback,
    logout_session as angel_logout_session,
    passthrough as angel_passthrough,
)
from db import DATABASE_URL, USE_POSTGRES, init_db
from jwt_utils import decode
from services.payment_service import activate_subscription, create_order, verify
from services.trade_service import dashboard, history, order_status, place_order, portfolio
from services.user_service import login, profile, refresh_session, signup, subscription
from services.watchlist_service import add_watchlist, list_watchlist, remove_watchlist


class BrokerageHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-User-Id")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _parse_path(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path.startswith("/api"):
            path = path[4:] or "/"
        return path, parse_qs(parsed.query)

    def _read_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return {}
        raw = self.rfile.read(content_length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def _request_base_url(self) -> str:
        proto = (self.headers.get("X-Forwarded-Proto") or "http").split(",")[0].strip()
        host = (self.headers.get("X-Forwarded-Host") or self.headers.get("Host") or "").split(",")[0].strip()
        if not host:
            return ""
        return f"{proto}://{host}"

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-User-Id")
        self.end_headers()

    def do_GET(self):
        path, query = self._parse_path()
        if path == "/health":
            self._send_json({"status": "ok"})
            return
        if path == "/db-health":
            self._send_json(
                {
                    "status": "ok",
                    "db": "postgres" if USE_POSTGRES else "sqlite",
                    "database_url_set": bool(DATABASE_URL),
                }
            )
            return
        if path == "/companies":
            self._send_json(companies())
            return
        if path == "/indices":
            self._send_json(get_indices())
            return
        if path == "/market-status":
            self._send_json(market_status())
            return
        if path == "/chart":
            ticker = (query.get("ticker", [""])[0] or "").strip()
            period = query.get("period", ["1d"])[0]
            interval = query.get("interval", ["5m"])[0]
            self._send_json(chart(ticker, period=period, interval=interval))
            return
        if path == "/oil-price":
            self._send_json(oil_price())
            return
        if path == "/user/profile":
            user_id = self._get_user_id(query)
            if not user_id:
                self._send_json({"error": "auth required"}, 401)
                return
            payload, status = profile(user_id)
            self._send_json(payload, status)
            return
        if path == "/user/subscription":
            user_id = self._get_user_id(query)
            if not user_id:
                self._send_json({"error": "auth required"}, 401)
                return
            payload, status = subscription(user_id)
            self._send_json(payload, status)
            return
        if path == "/trade/portfolio":
            user_id = self._get_user_id(query)
            if not user_id:
                self._send_json({"error": "auth required"}, 401)
                return
            payload, status = portfolio(user_id)
            self._send_json(payload, status)
            return
        if path == "/trade/dashboard":
            user_id = self._get_user_id(query)
            if not user_id:
                self._send_json({"error": "auth required"}, 401)
                return
            payload, status = dashboard(user_id)
            self._send_json(payload, status)
            return
        if path == "/trade/history":
            user_id = self._get_user_id(query)
            if not user_id:
                self._send_json({"error": "auth required"}, 401)
                return
            payload, status = history(user_id)
            self._send_json(payload, status)
            return
        if path == "/trade/list":
            user_id = self._get_user_id(query)
            if not user_id:
                self._send_json({"error": "auth required"}, 401)
                return
            payload, status = history(user_id)
            self._send_json(payload, status)
            return
        if path == "/trade/order-status":
            order_id = (query.get("id", [""])[0] or "").strip()
            payload, status = order_status(order_id)
            self._send_json(payload, status)
            return
        if path == "/watchlist":
            user_id = self._get_user_id(query)
            if not user_id:
                self._send_json({"error": "auth required"}, 401)
                return
            payload, status = list_watchlist(user_id)
            self._send_json(payload, status)
            return
        if path == "/broker/angelone/config":
            self._send_json(angel_config_snapshot())
            return
        if path == "/broker/angelone/connect":
            user_id = self._get_user_id(query)
            payload, status = angel_build_connect_payload(user_id=user_id)
            self._send_json(payload, status)
            return
        if path == "/broker/angelone/callback":
            payload, status = angel_handle_callback(query)
            self._send_json(payload, status)
            return
        if path == "/broker/paytm/config":
            payload = angel_config_snapshot()
            payload["note"] = "paytm endpoints are deprecated; use /broker/angelone/*"
            self._send_json(payload)
            return
        if path == "/broker/paytm/connect":
            user_id = self._get_user_id(query)
            payload, status = angel_build_connect_payload(user_id=user_id)
            payload["note"] = "paytm endpoints are deprecated; use /broker/angelone/*"
            self._send_json(payload, status)
            return
        if path == "/broker/paytm/callback":
            payload, status = angel_handle_callback(query)
            payload["note"] = "paytm endpoints are deprecated; use /broker/angelone/*"
            self._send_json(payload, status)
            return

        self._send_json({"error": "Endpoint not found"}, 404)

    def do_POST(self):
        path, _ = self._parse_path()
        body = self._read_json()

        if path == "/auth/login":
            payload, status = login(body)
            self._send_json(payload, status)
            return
        if path == "/auth/signup":
            payload, status = signup(body)
            self._send_json(payload, status)
            return
        if path == "/auth/refresh":
            payload, status = refresh_session(str(body.get("refresh_token", "")))
            self._send_json(payload, status)
            return
        if path == "/trade/buy":
            payload, status = place_order(self._inject_user(body), "BUY")
            self._send_json(payload, status)
            return
        if path == "/trade/sell":
            payload, status = place_order(self._inject_user(body), "SELL")
            self._send_json(payload, status)
            return
        if path == "/trade/place":
            side = str(body.get("type") or body.get("side") or "").upper()
            if side not in ("BUY", "SELL"):
                self._send_json({"error": "type must be BUY or SELL"}, 400)
                return
            payload, status = place_order(self._inject_user(body), side)
            self._send_json(payload, status)
            return
        if path == "/payment/create-order":
            payload, status = create_order(body)
            self._send_json(payload, status)
            return
        if path == "/payment/verify":
            payload, status = verify(body)
            self._send_json(payload, status)
            return
        if path == "/subscription/activate":
            payload, status = activate_subscription(body)
            self._send_json(payload, status)
            return
        if path == "/watchlist/add":
            user_id = self._get_user_id({})
            if not user_id:
                self._send_json({"error": "auth required"}, 401)
                return
            symbol = str(body.get("symbol") or body.get("ticker") or "").strip()
            payload, status = add_watchlist(user_id, symbol)
            self._send_json(payload, status)
            return
        if path == "/watchlist/remove":
            user_id = self._get_user_id({})
            if not user_id:
                self._send_json({"error": "auth required"}, 401)
                return
            symbol = str(body.get("symbol") or body.get("ticker") or "").strip()
            payload, status = remove_watchlist(user_id, symbol)
            self._send_json(payload, status)
            return
        if path == "/broker/angelone/request":
            payload, status = angel_passthrough(body)
            self._send_json(payload, status)
            return
        if path == "/broker/paytm/request":
            payload, status = angel_passthrough(body)
            payload["note"] = "paytm endpoints are deprecated; use /broker/angelone/*"
            self._send_json(payload, status)
            return

        self._send_json({"error": "Endpoint not found"}, 404)

    def do_DELETE(self):
        path, _ = self._parse_path()
        if path == "/broker/angelone/logout":
            payload, status = angel_logout_session()
            self._send_json(payload, status)
            return
        if path == "/broker/paytm/logout":
            payload, status = angel_logout_session()
            payload["note"] = "paytm endpoints are deprecated; use /broker/angelone/*"
            self._send_json(payload, status)
            return

        self._send_json({"error": "Endpoint not found"}, 404)

    def _get_user_id(self, query) -> str:
        user_id = (query.get("user_id", [""])[0] or self.headers.get("X-User-Id", "")).strip()
        if user_id:
            return user_id
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1].strip()
            payload, err = decode(token)
            if not err and payload and payload.get("sub"):
                return str(payload.get("sub"))
        return ""

    def _inject_user(self, body: dict) -> dict:
        if body.get("user_id"):
            return body
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1].strip()
            payload, err = decode(token)
            if not err and payload and payload.get("sub"):
                body["user_id"] = payload.get("sub")
        return body


def run(host: str = "127.0.0.1", port: int = 9000) -> None:
    load_dotenv()
    init_db()
    server = ThreadingHTTPServer((host, port), BrokerageHandler)
    print(f"Brokerage backend running on http://{host}:{port}")
    print("Endpoints: /api/auth/* /api/user/* /api/trade/* /api/market-* /api/payment/*")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Market brokerage backend server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()
    run(host=args.host, port=args.port)
