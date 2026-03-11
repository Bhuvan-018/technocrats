# STOCKY Chatbot Backend

This service proxies RapidAPI Yahoo Finance endpoints (yh-finance.p.rapidapi.com) for STOCKY.

## Setup
1. Set env vars:
   - `RAPIDAPI_KEY`
   - `RAPIDAPI_HOST` (optional, defaults to `yh-finance.p.rapidapi.com`)

2. Run:
```powershell
python api_server.py --host 127.0.0.1 --port 7000
```

## Endpoints
- `GET /health`
- `GET /ping` (RapidAPI ping)
- `POST /chat` → combines recommendations, profile, insights
- `POST /stock/recommendations` → `/stock/v2/get-recommendations`
- `POST /stock/profile` → `/stock/v3/get-profile`
- `POST /stock/insights` → `/stock/v2/get-insights`
- `POST /stock/quote` → `/market/v2/get-quotes`
- `POST /stock/chart` → `/stock/v3/get-chart`

## Notes
- Never commit API keys.
- The service returns RapidAPI responses directly.
