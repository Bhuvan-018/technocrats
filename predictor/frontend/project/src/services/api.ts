const BACKEND_BASE = (import.meta.env.VITE_BACKEND_URL || '').replace(/\/$/, '');
const SUPABASE_BASE = `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/api`;
const API_BASE = BACKEND_BASE ? `${BACKEND_BASE}/api` : SUPABASE_BASE;
const USING_SUPABASE = !BACKEND_BASE;

const headers: Record<string, string> = {
  'Content-Type': 'application/json',
};

if (USING_SUPABASE) {
  headers['Authorization'] = `Bearer ${import.meta.env.VITE_SUPABASE_ANON_KEY}`;
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = (data && (data.error || data.message)) || `Request failed (${response.status})`;
    throw new Error(message);
  }
  return data as T;
}

export interface Company {
  ticker: string;
  name: string;
}

export interface MarketStatus {
  is_open: boolean;
  current_time_ist: string;
  session_start: string;
  session_end: string;
  mode: string;
}

export interface PredictionHorizon {
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  confidence_low: number;
  confidence_high: number;
}

export interface PredictionResponse {
  ticker: string;
  name: string;
  market_status: {
    is_open: boolean;
    mode: string;
  };
  current_price: number;
  last_candle_time: string;
  predictions: {
    '10m': PredictionHorizon;
    '30m': PredictionHorizon;
    '1h': PredictionHorizon;
  };
}

export interface TrustMetrics {
  directional_accuracy: number;
  mean_absolute_error: number;
  window_days: number;
  sample_count: number;
}

export interface Feature {
  feature: string;
  importance: number;
}

export interface CoreIndicators {
  RSI?: number;
  SMA20?: number;
  ATR?: number;
}

export interface BacktestRow {
  date: string;
  horizon?: string;
  predicted_close: number;
  actual_close: number;
  error: number;
}

export interface ChartPoint {
  time: string;
  close: number;
}

export async function checkHealth() {
  return requestJson<{ status: string }>(`${API_BASE}/health`, { headers });
}

export async function getMarketStatus(): Promise<MarketStatus> {
  return requestJson<MarketStatus>(`${API_BASE}/market-status`, { headers });
}

export async function getCompanies(): Promise<Company[]> {
  const data = await requestJson<{ companies: Company[] }>(`${API_BASE}/companies`, { headers });
  return data.companies;
}

export async function getPrediction(ticker: string, allowSimulation = true): Promise<PredictionResponse> {
  return requestJson<PredictionResponse>(`${API_BASE}/predict`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ ticker, allow_simulation: allowSimulation }),
  });
}

export async function getTrustMetrics(ticker: string): Promise<TrustMetrics> {
  return requestJson<TrustMetrics>(`${API_BASE}/analytics/trust?ticker=${ticker}`, { headers });
}

export async function getExplainability(ticker: string): Promise<{ top_features: Feature[]; core_indicators?: CoreIndicators }> {
  return requestJson<{ top_features: Feature[]; core_indicators?: CoreIndicators }>(
    `${API_BASE}/analytics/explainability?ticker=${ticker}`,
    { headers }
  );
}

export async function getBacktest(ticker: string, limit = 10, horizon = '10m'): Promise<{ rows: BacktestRow[] }> {
  return requestJson<{ rows: BacktestRow[] }>(
    `${API_BASE}/analytics/backtest?ticker=${ticker}&limit=${limit}&horizon=${horizon}`,
    { headers }
  );
}

export async function getChartData(ticker: string, period = '2d', interval = '5m'): Promise<{ points: ChartPoint[] }> {
  return requestJson<{ points: ChartPoint[] }>(`${API_BASE}/chart?ticker=${ticker}&period=${period}&interval=${interval}`, { headers });
}
