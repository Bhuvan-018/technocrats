const BROKERAGE_API = import.meta.env.VITE_BROKERAGE_API || 'http://127.0.0.1:9000';
const PREDICTOR_API = import.meta.env.VITE_PREDICTOR_API || 'http://127.0.0.1:8000';

export async function brokerageFetch(path: string, options: RequestInit = {}) {
  const token = localStorage.getItem('access_token');

  const response = await fetch(`${BROKERAGE_API}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.message || 'Request failed');
  }

  return response.json();
}

export async function predictorFetch(path: string, options: RequestInit = {}) {
  const response = await fetch(`${PREDICTOR_API}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.message || 'Request failed');
  }

  return response.json();
}

function mapAuthResponse(raw: any) {
  if (!raw) {
    return raw;
  }
  if (raw.user) {
    return raw;
  }
  if (raw.profile) {
    return {
      access_token: raw.access_token,
      refresh_token: raw.refresh_token,
      user: {
        id: raw.profile.user_id || raw.profile.id,
        email: raw.profile.email,
        name: raw.profile.name,
        subscriptionTier: raw.profile.subscription_tier || raw.profile.subscriptionTier,
        subscriptionExpiry: raw.profile.subscription_expiry || raw.profile.subscriptionExpiry,
      },
    };
  }
  return raw;
}

function mapPortfolio(raw: any) {
  if (!raw) return raw;
  if (raw.totalValue !== undefined) return raw;

  const holdings = (raw.portfolio || raw.holdings || []).map((item: any) => {
    const quantity = Number(item.quantity ?? 0);
    const avgPrice = Number(item.avg_buy_price ?? item.avgPrice ?? 0);
    const currentPrice = Number(item.current_price ?? item.currentPrice ?? 0);
    const gainLoss = Number(item.pnl ?? item.gainLoss ?? (currentPrice - avgPrice) * quantity);
    const gainLossPercent = avgPrice > 0 ? (gainLoss / (avgPrice * quantity)) * 100 : 0;
    return {
      symbol: item.ticker || item.symbol,
      name: item.company || item.name,
      quantity,
      avgPrice,
      currentPrice,
      gainLoss,
      gainLossPercent,
    };
  });

  const totalInvestment = holdings.reduce((sum: number, h: any) => sum + h.avgPrice * h.quantity, 0);
  const totalValue = holdings.reduce((sum: number, h: any) => sum + h.currentPrice * h.quantity, 0);
  const totalGainLoss = holdings.reduce((sum: number, h: any) => sum + h.gainLoss, 0);

  return {
    totalValue,
    totalInvestment,
    totalGainLoss,
    holdings,
  };
}

function mapPrediction(raw: any, days?: number) {
  if (!raw || raw.predictions === undefined) return raw;
  const horizonOrder = ['10m', '30m', '1h'];
  const closes = horizonOrder
    .map((h) => raw.predictions?.[h]?.close)
    .filter((v) => typeof v === 'number');
  const length = Math.max(1, Math.min(days || closes.length || 1, 30));
  const filled = Array.from({ length }, (_, i) => closes[i] ?? closes[closes.length - 1] ?? raw.current_price ?? 0);
  const dates = Array.from({ length }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() + i + 1);
    return d.toISOString();
  });
  return {
    symbol: raw.ticker || raw.symbol,
    predictions: filled,
    dates,
    confidence: 0.6,
  };
}

function mapTrust(raw: any) {
  if (!raw) return raw;
  const accuracy = typeof raw.directional_accuracy === 'number' ? raw.directional_accuracy : 0.5;
  return {
    accuracy,
    consistency: accuracy,
    reliability: accuracy,
    overallTrust: accuracy,
  };
}

function mapExplainability(raw: any) {
  if (!raw) return raw;
  const features = raw.top_features || raw.factors || [];
  const max = Math.max(1, ...features.map((f: any) => Math.abs(Number(f.importance ?? f.impact ?? 0))));
  return {
    factors: features.map((f: any) => ({
      name: f.feature || f.name,
      impact: Math.abs(Number(f.importance ?? f.impact ?? 0)) / max,
      description: f.description || 'Relative importance in the model output.',
    })),
  };
}

function mapBacktest(raw: any) {
  if (!raw) return raw;
  const rows = raw.rows || [];
  return {
    dates: rows.map((r: any) => r.date),
    predicted: rows.map((r: any) => r.predicted_close ?? r.predicted ?? 0),
    actual: rows.map((r: any) => r.actual_close ?? r.actual ?? 0),
    accuracy: 0.5,
    profitability: 0.5,
  };
}

export const authAPI = {
  signup: (data: { email: string; password: string; name: string }) =>
    brokerageFetch('/api/auth/signup', {
      method: 'POST',
      body: JSON.stringify(data),
    }).then(mapAuthResponse),

  login: (data: { email: string; password: string }) =>
    brokerageFetch('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    }).then(mapAuthResponse),

  refresh: () =>
    brokerageFetch('/api/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: localStorage.getItem('refresh_token') || '' }),
    }),
};

export const marketAPI = {
  getStatus: () => brokerageFetch('/api/market-status'),
  getIndices: () => brokerageFetch('/api/indices'),
  getCompanies: () => brokerageFetch('/api/companies'),
  getOilPrice: () => brokerageFetch('/api/oil-price'),
};

export const watchlistAPI = {
  get: () => brokerageFetch('/api/watchlist'),
  add: (symbol: string) =>
    brokerageFetch('/api/watchlist/add', {
      method: 'POST',
      body: JSON.stringify({ symbol }),
    }),
  remove: (symbol: string) =>
    brokerageFetch('/api/watchlist/remove', {
      method: 'POST',
      body: JSON.stringify({ symbol }),
    }),
};

export const portfolioAPI = {
  get: () => brokerageFetch('/api/trade/portfolio').then(mapPortfolio),
};

export const subscriptionAPI = {
  createOrder: (plan: string) =>
    brokerageFetch('/api/payment/create-order', {
      method: 'POST',
      body: JSON.stringify({ plan }),
    }),
  verify: (data: { orderId: string; paymentId: string; signature: string }) =>
    brokerageFetch('/api/payment/verify', {
      method: 'POST',
      body: JSON.stringify({ payment_id: data.paymentId || data.orderId || '' }),
    }),
  activate: (plan: string) =>
    brokerageFetch('/api/subscription/activate', {
      method: 'POST',
      body: JSON.stringify({ tier: plan }),
    }),
};

export const predictorAPI = {
  predict: (data: { symbol: string; days?: number }) =>
    predictorFetch('/api/predict', {
      method: 'POST',
      body: JSON.stringify({ ticker: data.symbol, allow_simulation: true }),
    }).then((raw) => mapPrediction(raw, data.days)),
  getMarketStatus: () => predictorFetch('/api/market-status'),
  getCompanies: () => predictorFetch('/api/companies'),
  getTrust: (symbol: string) =>
    predictorFetch(`/api/analytics/trust?ticker=${encodeURIComponent(symbol)}`).then(mapTrust),
  getExplainability: (symbol: string) =>
    predictorFetch(`/api/analytics/explainability?ticker=${encodeURIComponent(symbol)}`).then(mapExplainability),
  getBacktest: (symbol: string) =>
    predictorFetch(`/api/analytics/backtest?ticker=${encodeURIComponent(symbol)}`).then(mapBacktest),
  getChart: (symbol: string) => predictorFetch(`/api/chart?ticker=${encodeURIComponent(symbol)}`),
};
