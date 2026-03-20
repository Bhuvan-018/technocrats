const http = require('http');
const { parse } = require('url');

const PORT = process.env.NEWS_MOCK_PORT ? Number(process.env.NEWS_MOCK_PORT) : 9060;

const nowIso = (offsetMinutes = 0) => new Date(Date.now() - offsetMinutes * 60000).toISOString();

const articles = [
  {
    id: 'news-001',
    headline: 'RBI holds rates steady as inflation cools',
    summary:
      'The Reserve Bank kept policy rates unchanged, citing improved inflation trends and stable growth outlook.',
    impact: 'neutral',
    is_trending: true,
    source: 'Reuters',
    related_stocks: ['SBIN', 'HDFCBANK'],
    published_at: nowIso(15),
  },
  {
    id: 'news-002',
    headline: 'Nifty ends higher led by banking stocks',
    summary:
      'Banking and financial shares lifted Nifty as investors priced in steady macro data and strong credit growth.',
    impact: 'positive',
    is_trending: false,
    source: 'Economic Times',
    related_stocks: ['ICICIBANK', 'KOTAKBANK'],
    published_at: nowIso(50),
  },
  {
    id: 'news-003',
    headline: 'Crude prices slip on higher inventories',
    summary:
      'Oil prices edged lower after inventory data signaled softening demand across key regions.',
    impact: 'negative',
    is_trending: false,
    source: 'Bloomberg',
    related_stocks: ['BPCL', 'IOC'],
    published_at: nowIso(120),
  },
  {
    id: 'news-004',
    headline: 'IT services bookings improve on large deal wins',
    summary:
      'Top IT firms reported improved order intake, supported by cloud modernization and cost-optimization projects.',
    impact: 'positive',
    is_trending: true,
    source: 'Mint',
    related_stocks: ['INFY', 'TCS', 'WIPRO'],
    published_at: nowIso(5),
  },
  {
    id: 'news-005',
    headline: 'Auto sales steady despite higher fuel costs',
    summary:
      'Passenger vehicle sales remained steady as demand in urban centers offset rising fuel prices.',
    impact: 'neutral',
    is_trending: false,
    source: 'Business Standard',
    related_stocks: ['MARUTI', 'TATAMOTORS'],
    published_at: nowIso(90),
  },
];

const send = (res, status, body) => {
  res.writeHead(status, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  });
  res.end(JSON.stringify(body));
};

const server = http.createServer((req, res) => {
  const { pathname } = parse(req.url, true);
  if (req.method === 'OPTIONS') {
    return send(res, 200, { ok: true });
  }

  if (req.method === 'GET' && pathname === '/api/health') {
    return send(res, 200, { status: 'ok', source: 'news-mock' });
  }

  if (req.method === 'GET' && pathname === '/api/news') {
    return send(res, 200, articles);
  }

  return send(res, 404, { error: 'Endpoint not found' });
});

server.listen(PORT, () => {
  console.log(`News mock API running on http://127.0.0.1:${PORT}`);
});
