const http = require('http');
const { parse } = require('url');

const PORT = process.env.MOCK_API_PORT ? Number(process.env.MOCK_API_PORT) : 9050;
const PRICE_SOURCE_URL = process.env.PRICE_SOURCE_URL || 'http://127.0.0.1:9000/api/companies';

const nowIso = () => new Date().toISOString();
const randId = (prefix) => `${prefix}${Math.random().toString(16).slice(2, 8).toUpperCase()}`;

const state = {
  indices: [
    { name: 'NIFTY 50', value: 24210.5, prevClose: 24050.0 },
    { name: 'SENSEX', value: 78150.25, prevClose: 77600.0 },
  ],
  oil: { price: 78.6, prevClose: 79.1 },
  companyPrices: {
    ITC: 432.5,
    SBIN: 618.0,
    WIPRO: 492.0,
  },
  holdings: [
    { ticker: 'ITC', company: 'ITC Ltd', quantity: 8, avg_buy_price: 432.5, current_price: 432.5 },
    { ticker: 'SBIN', company: 'State Bank of India', quantity: 3, avg_buy_price: 618.0, current_price: 618.0 },
    { ticker: 'WIPRO', company: 'Wipro', quantity: 4, avg_buy_price: 492.0, current_price: 492.0 },
  ],
  orders: [],
  transactions: [],
};

const normalizeSymbol = (symbol = '') => symbol.replace('.NS', '').replace('-EQ', '').toUpperCase();

const refreshCompanyPrices = async () => {
  try {
    const res = await fetch(PRICE_SOURCE_URL, { method: 'GET' });
    if (!res.ok) return;
    const data = await res.json();
    if (!Array.isArray(data)) return;
    data.forEach((row) => {
      const symbol = normalizeSymbol(row.symbol || row.ticker || '');
      const price = Number(row.price || row.last_price || row.current_price);
      if (!symbol || Number.isNaN(price)) return;
      state.companyPrices[symbol] = price;
    });

    state.holdings = state.holdings.map((h) => {
      const live = state.companyPrices[h.ticker];
      if (!live || Number.isNaN(live)) return h;
      const shouldSyncAvg = Math.abs(h.avg_buy_price - h.current_price) < 0.01;
      return {
        ...h,
        current_price: live,
        avg_buy_price: shouldSyncAvg ? live : h.avg_buy_price,
      };
    });
  } catch {
    // Keep previous prices if source is unavailable.
  }
};

const jitter = (value, pct) => {
  const delta = (Math.random() * 2 - 1) * pct;
  return Number((value * (1 + delta)).toFixed(2));
};

const updateMarket = () => {
  const indexPct = 0.00015;
  const meanRevert = 0.05;
  const oilPct = 0.0005;
  const holdingPct = 0.001;

  state.indices = state.indices.map((idx) => {
    let next = jitter(idx.value, indexPct);
    next = Number((next + (idx.prevClose - next) * meanRevert).toFixed(2));
    const change = Number((next - idx.prevClose).toFixed(2));
    const changePercent = Number(((change / idx.prevClose) * 100).toFixed(2));
    return { ...idx, value: next, change, changePercent };
  });
  const oilNext = jitter(state.oil.price, oilPct);
  state.oil = {
    ...state.oil,
    price: oilNext,
    change: Number((oilNext - state.oil.prevClose).toFixed(2)),
    changePercent: Number((((oilNext - state.oil.prevClose) / state.oil.prevClose) * 100).toFixed(2)),
  };

  state.holdings = state.holdings.map((h) => {
    const base = state.companyPrices[h.ticker] ?? h.current_price;
    const current = jitter(base, holdingPct);
    state.companyPrices[h.ticker] = current;
    const pnl = Number(((current - h.avg_buy_price) * h.quantity).toFixed(2));
    return { ...h, current_price: current, pnl };
  });
};

const dashboardPayload = () => {
  updateMarket();
  const totalValue = state.holdings.reduce((sum, h) => sum + h.current_price * h.quantity, 0);
  const totalPnl = state.holdings.reduce((sum, h) => sum + (h.pnl || 0), 0);
  return {
    summary: {
      total_value: Number(totalValue.toFixed(2)),
      total_pnl: Number(totalPnl.toFixed(2)),
      holdings_count: state.holdings.length,
      open_orders_count: state.orders.filter((o) => o.status === 'OPEN').length,
    },
    holdings: state.holdings,
    recent_orders: state.orders.slice(-5).reverse(),
    recent_transactions: state.transactions.slice(-5).reverse(),
  };
};

const portfolioPayload = () => {
  updateMarket();
  const totalValue = state.holdings.reduce((sum, h) => sum + h.current_price * h.quantity, 0);
  const totalInvestment = state.holdings.reduce((sum, h) => sum + h.avg_buy_price * h.quantity, 0);
  const totalGainLoss = Number((totalValue - totalInvestment).toFixed(2));
  return {
    totalValue: Number(totalValue.toFixed(2)),
    totalInvestment: Number(totalInvestment.toFixed(2)),
    totalGainLoss,
    holdings: state.holdings.map((h) => ({
      symbol: h.ticker,
      name: h.company,
      quantity: h.quantity,
      avgPrice: h.avg_buy_price,
      currentPrice: h.current_price,
      gainLoss: Number(((h.current_price - h.avg_buy_price) * h.quantity).toFixed(2)),
    })),
  };
};

const parseBody = (req) => new Promise((resolve) => {
  let data = '';
  req.on('data', (chunk) => (data += chunk));
  req.on('end', () => {
    if (!data) return resolve({});
    try {
      resolve(JSON.parse(data));
    } catch {
      resolve({});
    }
  });
});

const send = (res, status, body) => {
  res.writeHead(status, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-User-Id',
  });
  res.end(JSON.stringify(body));
};

const server = http.createServer(async (req, res) => {
  const { pathname, query } = parse(req.url, true);
  if (req.method === 'OPTIONS') {
    return send(res, 200, { ok: true });
  }

  if (req.method === 'GET' && pathname === '/api/health') {
    return send(res, 200, { status: 'ok', source: 'mock' });
  }

  if (req.method === 'GET' && pathname === '/api/market-status') {
    return send(res, 200, {
      is_open: true,
      session_start: '09:15',
      session_end: '15:30',
      current_time_ist: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
    });
  }

  if (req.method === 'GET' && pathname === '/api/indices') {
    updateMarket();
    return send(res, 200, state.indices.map((idx) => ({
      name: idx.name,
      value: idx.value,
      change: idx.change ?? Number((idx.value - idx.prevClose).toFixed(2)),
      changePercent: idx.changePercent ?? Number((((idx.value - idx.prevClose) / idx.prevClose) * 100).toFixed(2)),
    })));
  }

  if (req.method === 'GET' && pathname === '/api/oil-price') {
    updateMarket();
    return send(res, 200, {
      price: state.oil.price,
      change: state.oil.change ?? Number((state.oil.price - state.oil.prevClose).toFixed(2)),
      changePercent: state.oil.changePercent ?? Number((((state.oil.price - state.oil.prevClose) / state.oil.prevClose) * 100).toFixed(2)),
    });
  }

  if (req.method === 'GET' && pathname === '/api/trade/dashboard') {
    return send(res, 200, dashboardPayload());
  }

  if (req.method === 'GET' && pathname === '/api/trade/portfolio') {
    return send(res, 200, portfolioPayload());
  }

  if (req.method === 'GET' && pathname === '/api/trade/history') {
    const rows = state.transactions.length ? state.transactions : [
      { transaction_id: randId('TXN'), order_id: randId('ORD'), ticker: 'ITC', side: 'BUY', quantity: 4, price: 422, status: 'EXECUTED', timestamp: nowIso() },
      { transaction_id: randId('TXN'), order_id: randId('ORD'), ticker: 'SBIN', side: 'BUY', quantity: 2, price: 612, status: 'EXECUTED', timestamp: nowIso() },
      { transaction_id: randId('TXN'), order_id: randId('ORD'), ticker: 'WIPRO', side: 'SELL', quantity: 1, price: 488, status: 'EXECUTED', timestamp: nowIso() },
    ];
    return send(res, 200, { user_id: 'U-DEMO', transactions: rows });
  }

  if (req.method === 'GET' && pathname === '/api/trade/order-status') {
    const orderId = query?.id || '';
    const order = state.orders.find((o) => o.order_id === orderId);
    if (!order) {
      return send(res, 404, { message: 'Order not found' });
    }
    return send(res, 200, order);
  }

  if (req.method === 'POST' && pathname === '/api/trade/place') {
    const body = await parseBody(req);
    const ticker = String(body.ticker || body.symbol || '').toUpperCase();
    const qty = Number(body.quantity || 0);
    const price = Number(body.price || 0) || state.companyPrices[ticker] || jitter(1500, 0.01);
    const side = String(body.type || body.side || 'BUY').toUpperCase();
    if (!ticker || qty <= 0) {
      return send(res, 400, { message: 'ticker and quantity are required' });
    }

    const order = {
      order_id: randId('ORD'),
      ticker,
      company: body.company || ticker,
      side,
      quantity: qty,
      price,
      status: 'EXECUTED',
      timestamp: nowIso(),
      filled_quantity: qty,
    };
    state.orders.push(order);
    state.transactions.push({
      transaction_id: randId('TXN'),
      order_id: order.order_id,
      ticker,
      side,
      quantity: qty,
      price,
      status: 'EXECUTED',
      timestamp: order.timestamp,
    });

    const holding = state.holdings.find((h) => h.ticker === ticker);
    if (side === 'BUY') {
      if (holding) {
        const totalCost = holding.avg_buy_price * holding.quantity + price * qty;
        const newQty = holding.quantity + qty;
        holding.quantity = newQty;
        holding.avg_buy_price = Number((totalCost / newQty).toFixed(2));
        holding.current_price = price;
      } else {
        state.holdings.push({
          ticker,
          company: body.company || ticker,
          quantity: qty,
          avg_buy_price: price,
          current_price: price,
        });
      }
    } else if (holding) {
      holding.quantity = Math.max(0, holding.quantity - qty);
      holding.current_price = price;
    }

    return send(res, 200, { order });
  }

  if (req.method === 'GET' && pathname === '/api/broker/paytm/config') {
    return send(res, 200, {
      configured: true,
      has_access_token: true,
      provider: 'mock',
    });
  }

  if (req.method === 'GET' && pathname === '/api/watchlist') {
    return send(res, 200, {
      user_id: 'U-DEMO',
      symbols: [
        { symbol: 'RELIANCE', name: 'Reliance Industries' },
        { symbol: 'HDFCBANK', name: 'HDFC Bank' },
        { symbol: 'INFY', name: 'Infosys' },
      ],
    });
  }

  if (req.method === 'POST' && pathname === '/api/watchlist/add') {
    const body = await parseBody(req);
    return send(res, 200, { success: true, symbol: body.symbol || body.ticker || '' });
  }

  if (req.method === 'POST' && pathname === '/api/watchlist/remove') {
    const body = await parseBody(req);
    return send(res, 200, { success: true, symbol: body.symbol || body.ticker || '' });
  }

  if (req.method === 'GET' && pathname === '/api/broker/paytm/connect') {
    return send(res, 200, { configured: true, has_access_token: true });
  }

  if (req.method === 'DELETE' && pathname === '/api/broker/paytm/logout') {
    return send(res, 200, { success: true, has_access_token: false });
  }

  return send(res, 404, { message: 'Endpoint not found' });
});

server.listen(PORT, () => {
  console.log(`Mock API running on http://127.0.0.1:${PORT}`);
});

setInterval(() => {
  updateMarket();
}, 1000);

refreshCompanyPrices();
setInterval(() => {
  refreshCompanyPrices();
}, 30000);
