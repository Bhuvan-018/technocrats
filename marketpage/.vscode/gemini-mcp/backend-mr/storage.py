import threading
from datetime import datetime, timezone
from typing import Dict, List


class InMemoryStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.users: Dict[str, dict] = {}
        self.orders: Dict[str, dict] = {}
        self.transactions: List[dict] = []
        self.portfolio: Dict[str, Dict[str, dict]] = {}
        self.payments: Dict[str, dict] = {}

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create_user(self, user: dict) -> dict:
        with self._lock:
            self.users[user["user_id"]] = user
        return user

    def get_user(self, user_id: str) -> dict | None:
        return self.users.get(user_id)

    def upsert_order(self, order: dict) -> dict:
        with self._lock:
            self.orders[order["order_id"]] = order
        return order

    def get_order(self, order_id: str) -> dict | None:
        return self.orders.get(order_id)

    def add_transaction(self, txn: dict) -> None:
        with self._lock:
            self.transactions.append(txn)

    def get_transactions(self, user_id: str | None = None) -> List[dict]:
        if not user_id:
            return list(self.transactions)
        return [t for t in self.transactions if t.get("user_id") == user_id]

    def upsert_position(self, user_id: str, ticker: str, position: dict) -> None:
        with self._lock:
            if user_id not in self.portfolio:
                self.portfolio[user_id] = {}
            self.portfolio[user_id][ticker] = position

    def get_portfolio(self, user_id: str) -> List[dict]:
        return list(self.portfolio.get(user_id, {}).values())

    def add_payment(self, payment: dict) -> dict:
        with self._lock:
            self.payments[payment["payment_id"]] = payment
        return payment

    def get_payment(self, payment_id: str) -> dict | None:
        return self.payments.get(payment_id)


STORE = InMemoryStore()
