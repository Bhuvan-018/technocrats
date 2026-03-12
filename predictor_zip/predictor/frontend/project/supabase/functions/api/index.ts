import { createClient } from 'npm:@supabase/supabase-js@2.57.4';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Client-Info, Apikey',
};

const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const supabase = createClient(supabaseUrl, supabaseKey);

function isMarketOpen(): { is_open: boolean; mode: string } {
  const now = new Date();
  const istOffset = 5.5 * 60 * 60 * 1000;
  const istTime = new Date(now.getTime() + istOffset);

  const day = istTime.getUTCDay();
  const hours = istTime.getUTCHours();
  const minutes = istTime.getUTCMinutes();
  const totalMinutes = hours * 60 + minutes;

  const marketStart = 9 * 60 + 15;
  const marketEnd = 15 * 60 + 30;

  const isWeekday = day >= 1 && day <= 5;
  const isDuringHours = totalMinutes >= marketStart && totalMinutes <= marketEnd;

  const is_open = isWeekday && isDuringHours;

  return {
    is_open,
    mode: is_open ? 'live' : 'simulation',
  };
}

function getCurrentISTTime(): string {
  const now = new Date();
  const istOffset = 5.5 * 60 * 60 * 1000;
  const istTime = new Date(now.getTime() + istOffset);
  return istTime.toISOString();
}

function generateMockPrediction(ticker: string, currentPrice: number, horizon: string) {
  const variance = horizon === '10m' ? 0.003 : horizon === '30m' ? 0.008 : 0.015;
  const change = (Math.random() - 0.5) * variance * currentPrice;

  const predictedClose = currentPrice + change;
  const predictedHigh = predictedClose + Math.abs(change) * 0.5;
  const predictedLow = predictedClose - Math.abs(change) * 0.5;
  const predictedOpen = currentPrice + change * 0.3;

  const baseVolume = 1000000;
  const volumeVariance = Math.random() * 500000;

  return {
    open: Number(predictedOpen.toFixed(2)),
    high: Number(predictedHigh.toFixed(2)),
    low: Number(predictedLow.toFixed(2)),
    close: Number(predictedClose.toFixed(2)),
    volume: Math.floor(baseVolume + volumeVariance),
    confidence_low: Number((predictedClose - Math.abs(change) * 0.7).toFixed(2)),
    confidence_high: Number((predictedClose + Math.abs(change) * 0.7).toFixed(2)),
  };
}

async function handleHealth() {
  return { status: 'ok' };
}

async function handleMarketStatus() {
  const marketStatus = isMarketOpen();
  return {
    is_open: marketStatus.is_open,
    current_time_ist: getCurrentISTTime(),
    session_start: '09:15',
    session_end: '15:30',
    mode: marketStatus.mode,
  };
}

async function handleCompanies() {
  const { data, error } = await supabase
    .from('companies')
    .select('ticker, name')
    .order('name');

  if (error) throw error;

  return { companies: data || [] };
}

async function handlePredict(body: any) {
  const { ticker, allow_simulation = true } = body;

  if (!ticker) {
    throw new Error('Ticker is required');
  }

  const { data: company } = await supabase
    .from('companies')
    .select('ticker, name')
    .eq('ticker', ticker)
    .maybeSingle();

  if (!company) {
    throw new Error('Company not found');
  }

  const marketStatus = isMarketOpen();

  if (!marketStatus.is_open && !allow_simulation) {
    throw new Error('Market is closed and simulation is not allowed');
  }

  const basePrice = 1000 + Math.random() * 2000;
  const currentPrice = Number(basePrice.toFixed(2));

  const predictions = {
    '10m': generateMockPrediction(ticker, currentPrice, '10m'),
    '30m': generateMockPrediction(ticker, currentPrice, '30m'),
    '1h': generateMockPrediction(ticker, currentPrice, '1h'),
  };

  return {
    ticker: company.ticker,
    name: company.name,
    market_status: {
      is_open: marketStatus.is_open,
      mode: marketStatus.mode,
    },
    current_price: currentPrice,
    last_candle_time: getCurrentISTTime(),
    predictions,
  };
}

async function handleTrust(ticker: string) {
  if (!ticker) {
    throw new Error('Ticker is required');
  }

  const directionalAccuracy = 0.65 + Math.random() * 0.2;
  const mae = 5 + Math.random() * 15;

  return {
    directional_accuracy: Number(directionalAccuracy.toFixed(3)),
    mean_absolute_error: Number(mae.toFixed(2)),
    window_days: 30,
    sample_count: 500 + Math.floor(Math.random() * 500),
  };
}

async function handleExplainability(ticker: string) {
  if (!ticker) {
    throw new Error('Ticker is required');
  }

  const features = [
    { feature: 'Moving Average (20)', importance: 0.85 + Math.random() * 0.1 },
    { feature: 'RSI', importance: 0.70 + Math.random() * 0.1 },
    { feature: 'MACD', importance: 0.65 + Math.random() * 0.1 },
    { feature: 'Volume Trend', importance: 0.55 + Math.random() * 0.1 },
    { feature: 'Bollinger Bands', importance: 0.45 + Math.random() * 0.1 },
    { feature: 'Stochastic', importance: 0.35 + Math.random() * 0.1 },
  ];

  features.sort((a, b) => b.importance - a.importance);

  return {
    top_features: features.map(f => ({
      feature: f.feature,
      importance: Number(f.importance.toFixed(3)),
    })),
  };
}

async function handleBacktest(ticker: string, limit: number = 10) {
  if (!ticker) {
    throw new Error('Ticker is required');
  }

  const rows = [];
  const now = new Date();

  for (let i = 0; i < limit; i++) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);

    const basePrice = 1000 + Math.random() * 2000;
    const error = (Math.random() - 0.5) * 40;

    rows.push({
      date: date.toISOString(),
      predicted_close: Number((basePrice + error).toFixed(2)),
      actual_close: Number(basePrice.toFixed(2)),
      error: Number(error.toFixed(2)),
    });
  }

  return { rows };
}

async function handleChart(ticker: string, period: string = '1d', interval: string = '5m') {
  if (!ticker) {
    throw new Error('Ticker is required');
  }

  const points = [];
  const now = new Date();
  const basePrice = 1000 + Math.random() * 2000;

  let numPoints = 78;
  if (interval === '1m') numPoints = 390;
  else if (interval === '15m') numPoints = 26;

  for (let i = numPoints - 1; i >= 0; i--) {
    const time = new Date(now);
    const minutesAgo = i * (interval === '1m' ? 1 : interval === '5m' ? 5 : 15);
    time.setMinutes(time.getMinutes() - minutesAgo);

    const variance = (Math.random() - 0.5) * 50;
    const close = basePrice + variance + (i * 0.5);

    points.push({
      time: time.toISOString(),
      close: Number(close.toFixed(2)),
    });
  }

  return { points };
}

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    const url = new URL(req.url);
    const path = url.pathname.replace('/api', '');

    let result;

    if (path === '/health') {
      result = await handleHealth();
    } else if (path === '/market-status') {
      result = await handleMarketStatus();
    } else if (path === '/companies') {
      result = await handleCompanies();
    } else if (path === '/predict') {
      const body = await req.json();
      result = await handlePredict(body);
    } else if (path === '/analytics/trust') {
      const ticker = url.searchParams.get('ticker') || '';
      result = await handleTrust(ticker);
    } else if (path === '/analytics/explainability') {
      const ticker = url.searchParams.get('ticker') || '';
      result = await handleExplainability(ticker);
    } else if (path === '/analytics/backtest') {
      const ticker = url.searchParams.get('ticker') || '';
      const limit = parseInt(url.searchParams.get('limit') || '10');
      result = await handleBacktest(ticker, limit);
    } else if (path === '/chart') {
      const ticker = url.searchParams.get('ticker') || '';
      const period = url.searchParams.get('period') || '1d';
      const interval = url.searchParams.get('interval') || '5m';
      result = await handleChart(ticker, period, interval);
    } else {
      throw new Error('Endpoint not found');
    }

    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Internal server error';
    return new Response(JSON.stringify({ error: message }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
