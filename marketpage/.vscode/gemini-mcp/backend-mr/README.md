# Market Brokerage Backend (Local)

Minimal local backend for brokerage UI wiring. Storage is in-memory only.

## Run

```powershell
python api_server.py --host 127.0.0.1 --port 9000
```

## Dependencies
- `pip install -r requirements.txt`

## Migrations (Alembic)
Set `DATABASE_URL`, then run:
```powershell
alembic -c alembic.ini upgrade head
```

## Market Data
Optional env:
- `MARKET_TICKERS` = comma-separated tickers (e.g. `RELIANCE.NS,INFY.NS,TCS.NS`)
If not set, a small default set is used.

## Persistence
- Production: Postgres using `DATABASE_URL` (e.g. `postgresql://user:pass@host:5432/db`)
- Local fallback: SQLite at `d:\youngtechnocrats\market_page\.vscode\gemini-mcp\backend-mr\data\brokerage.db`
- Tables: users, refresh_tokens, orders, transactions, portfolio, payments, market_cache
Requires a Postgres driver:
- `psycopg` (recommended) or `psycopg2`

## Auth
- JWT access + refresh tokens.
- `POST /api/auth/refresh` rotates refresh tokens.
- Use `Authorization: Bearer <access_token>` for protected endpoints.

## Endpoints

Auth/User:
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET /api/user/profile?user_id=...`
- `GET /api/user/subscription?user_id=...`

Brokerage:
- `POST /api/trade/buy`
- `POST /api/trade/sell`
- `GET /api/trade/dashboard?user_id=...`
- `GET /api/trade/portfolio?user_id=...`
- `GET /api/trade/history?user_id=...`
- `GET /api/trade/order-status?id=...`

Market Data:
- `GET /api/companies`
- `GET /api/market-status`
- `GET /api/chart?ticker=...&period=...&interval=...`
- `GET /api/oil-price`

Payments:
- `POST /api/payment/create-order`
- `POST /api/payment/verify`
- `POST /api/subscription/activate`

Notes:
- No sample data is seeded.
- `yfinance` is optional; if unavailable or network fails, market data endpoints return empty data.
- Broker and payment providers are gated by env vars:
  - `BROKER_PROVIDER` = `paper` (default), `zerodha`, `upstox`
  - `PAYMENT_PROVIDER` = `local` (default), `razorpay`, `paytm`
- Razorpay keys: `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`

Paytm Money broker setup:
 - `PAYTM_MONEY_API_BASE_URL=https://developer.paytmmoney.com`

Paytm broker endpoints:
 - `DELETE /api/broker/paytm/logout` (maps to Paytm docs: `/accounts/v1/logout`)
 - `POST /api/broker/paytm/request` (generic wrapper for Paytm docs endpoints)

 Example generic request body:
 ```json
 {
   "method": "GET",
   "path": "/orders/v1/order-book",
   "query": {},
   "body": {},
   "jwt_token": "optional-if-not-in-env-or-bearer"
 }
 ```
