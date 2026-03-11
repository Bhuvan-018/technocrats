import { useEffect, useState } from 'react';
import { AlertCircle, RefreshCw, TrendingDown, TrendingUp } from 'lucide-react';
import { brokerageFetch, marketAPI } from '../services/api';

type DashboardSummary = {
  total_value: number;
  total_pnl: number;
  holdings_count: number;
  open_orders_count: number;
};

type DashboardHolding = {
  ticker: string;
  company: string;
  quantity: number;
  avg_buy_price: number;
  current_price: number;
  pnl: number;
};

type DashboardOrder = {
  order_id: string;
  ticker: string;
  side: string;
  quantity: number;
  price: number;
  status: string;
  timestamp: string;
};

type DashboardTxn = {
  transaction_id: string;
  ticker: string;
  side: string;
  quantity: number;
  price: number;
  timestamp: string;
};

type DashboardPayload = {
  summary: DashboardSummary;
  holdings: DashboardHolding[];
  recent_orders: DashboardOrder[];
  recent_transactions: DashboardTxn[];
};

type BrokerConfig = {
  configured: boolean;
  has_access_token: boolean;
  missing_env_keys?: string[];
};

type MarketStatus = {
  is_open: boolean;
};

type OilPrice = {
  price: number;
  change: number;
  changePercent: number;
};

export function Home() {
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);
  const [marketStatus, setMarketStatus] = useState<MarketStatus | null>(null);
  const [indices, setIndices] = useState<any[]>([]);
  const [oilPrice, setOilPrice] = useState<OilPrice | null>(null);
  const [brokerConfig, setBrokerConfig] = useState<BrokerConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setError(null);
      const results = await Promise.allSettled([
        brokerageFetch('/api/trade/dashboard'),
        marketAPI.getStatus(),
        marketAPI.getIndices(),
        marketAPI.getOilPrice(),
        brokerageFetch('/api/broker/paytm/config'),
      ]);

      const [dashboardResult, marketStatusResult, indicesResult, oilPriceResult, brokerResult] = results;

      if (dashboardResult.status === 'fulfilled') {
        setDashboard(dashboardResult.value as DashboardPayload);
      } else {
        setDashboard(null);
      }
      if (marketStatusResult.status === 'fulfilled') {
        setMarketStatus(marketStatusResult.value as MarketStatus);
      }
      if (indicesResult.status === 'fulfilled') {
        setIndices(indicesResult.value as any[]);
      }
      if (oilPriceResult.status === 'fulfilled') {
        setOilPrice(oilPriceResult.value as OilPrice);
      }
      if (brokerResult.status === 'fulfilled') {
        setBrokerConfig(brokerResult.value as BrokerConfig);
      }

      if (
        dashboardResult.status === 'rejected' &&
        marketStatusResult.status === 'rejected' &&
        indicesResult.status === 'rejected'
      ) {
        setError('Failed to load dashboard data');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(value || 0);

  const formatDate = (timestamp: string) =>
    new Date(timestamp).toLocaleString('en-IN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Trading Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Market status:{' '}
            <span className={`font-semibold ${marketStatus?.is_open ? 'text-green-600' : 'text-red-600'}`}>
              {marketStatus?.is_open ? 'OPEN' : 'CLOSED'}
            </span>
          </p>
        </div>
        <button
          onClick={loadData}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="text-sm text-gray-600">Portfolio Value</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(dashboard.summary.total_value)}</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="text-sm text-gray-600">Total P&L</div>
            <div className={`text-2xl font-bold mt-1 ${dashboard.summary.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {dashboard.summary.total_pnl >= 0 ? '+' : ''}
              {formatCurrency(dashboard.summary.total_pnl)}
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="text-sm text-gray-600">Holdings</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{dashboard.summary.holdings_count}</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="text-sm text-gray-600">Open Orders</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{dashboard.summary.open_orders_count}</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <div className="text-sm text-gray-600">Broker</div>
            <div className={`text-lg font-semibold mt-1 ${brokerConfig?.has_access_token ? 'text-green-600' : 'text-red-600'}`}>
              {brokerConfig?.has_access_token ? 'Connected' : 'Not Connected'}
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Market Snapshot</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {indices.map((index) => {
                const positive = Number(index.change || 0) >= 0;
                return (
                  <div key={index.name} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                      <span>{index.name}</span>
                      {positive ? <TrendingUp className="w-4 h-4 text-green-600" /> : <TrendingDown className="w-4 h-4 text-red-600" />}
                    </div>
                    <div className="text-xl font-bold text-gray-900">{Number(index.value || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</div>
                    <div className={`text-sm font-medium ${positive ? 'text-green-600' : 'text-red-600'}`}>
                      {positive ? '+' : ''}{Number(index.change || 0).toFixed(2)} ({positive ? '+' : ''}{Number(index.changePercent || 0).toFixed(2)}%)
                    </div>
                  </div>
                );
              })}

              {oilPrice && (
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">Crude Oil</div>
                  <div className="text-xl font-bold text-gray-900">${Number(oilPrice.price || 0).toFixed(2)}</div>
                  <div className={`text-sm font-medium ${Number(oilPrice.change || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {Number(oilPrice.change || 0) >= 0 ? '+' : ''}{Number(oilPrice.change || 0).toFixed(2)} ({Number(oilPrice.changePercent || 0) >= 0 ? '+' : ''}{Number(oilPrice.changePercent || 0).toFixed(2)}%)
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Portfolio Holdings</h2>
            {!dashboard?.holdings?.length ? (
              <p className="text-sm text-gray-500">No holdings found.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 text-gray-600">
                      <th className="text-left py-2 pr-4">Symbol</th>
                      <th className="text-right py-2 px-2">Qty</th>
                      <th className="text-right py-2 px-2">Avg</th>
                      <th className="text-right py-2 px-2">Current</th>
                      <th className="text-right py-2 pl-2">P&L</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboard.holdings.map((h) => {
                      const pnlPct = h.avg_buy_price > 0 ? (h.pnl / (h.avg_buy_price * h.quantity || 1)) * 100 : 0;
                      return (
                        <tr key={`${h.ticker}-${h.company}`} className="border-b border-gray-100">
                          <td className="py-2 pr-4 font-medium text-gray-900">{h.ticker}</td>
                          <td className="py-2 px-2 text-right">{Number(h.quantity || 0).toLocaleString()}</td>
                          <td className="py-2 px-2 text-right">{formatCurrency(Number(h.avg_buy_price || 0))}</td>
                          <td className="py-2 px-2 text-right">{formatCurrency(Number(h.current_price || 0))}</td>
                          <td className={`py-2 pl-2 text-right font-medium ${Number(h.pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatCurrency(Number(h.pnl || 0))} ({pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(2)}%)
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Orders</h2>
            {!dashboard?.recent_orders?.length ? (
              <p className="text-sm text-gray-500">No recent orders.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 text-gray-600">
                      <th className="text-left py-2 pr-4">Time</th>
                      <th className="text-left py-2 px-2">Symbol</th>
                      <th className="text-left py-2 px-2">Side</th>
                      <th className="text-right py-2 px-2">Qty</th>
                      <th className="text-right py-2 px-2">Price</th>
                      <th className="text-left py-2 pl-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboard.recent_orders.map((order) => (
                      <tr key={order.order_id} className="border-b border-gray-100">
                        <td className="py-2 pr-4 text-gray-500">{formatDate(order.timestamp)}</td>
                        <td className="py-2 px-2 font-medium text-gray-900">{order.ticker}</td>
                        <td className={`py-2 px-2 font-medium ${String(order.side).toUpperCase() === 'BUY' ? 'text-blue-600' : 'text-red-600'}`}>
                          {String(order.side).toUpperCase()}
                        </td>
                        <td className="py-2 px-2 text-right">{Number(order.quantity || 0).toLocaleString()}</td>
                        <td className="py-2 px-2 text-right">{formatCurrency(Number(order.price || 0))}</td>
                        <td className="py-2 pl-2">{order.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Transactions</h2>
            {!dashboard?.recent_transactions?.length ? (
              <p className="text-sm text-gray-500">No recent transactions.</p>
            ) : (
              <div className="space-y-3">
                {dashboard.recent_transactions.map((txn) => {
                  const amount = Number(txn.quantity || 0) * Number(txn.price || 0);
                  const buy = String(txn.side).toUpperCase() === 'BUY';
                  return (
                    <div key={txn.transaction_id} className="border border-gray-200 rounded-lg p-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium text-gray-900">{txn.ticker}</div>
                          <div className={`text-xs font-semibold ${buy ? 'text-blue-600' : 'text-red-600'}`}>{String(txn.side).toUpperCase()}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-semibold text-gray-900">{formatCurrency(amount)}</div>
                          <div className="text-xs text-gray-500">{formatDate(txn.timestamp)}</div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Broker Status</h2>
            <div className="flex items-start gap-3">
              <div className={`w-3 h-3 rounded-full mt-1 ${brokerConfig?.has_access_token ? 'bg-green-500' : 'bg-red-500'}`} />
              <div>
                <p className={`font-medium ${brokerConfig?.has_access_token ? 'text-green-700' : 'text-red-700'}`}>
                  {brokerConfig?.has_access_token ? 'Broker Connected' : 'Broker Not Connected'}
                </p>
                {!brokerConfig?.configured && brokerConfig?.missing_env_keys?.length ? (
                  <p className="text-sm text-red-700 mt-1">Missing env keys: {brokerConfig.missing_env_keys.join(', ')}</p>
                ) : (
                  <p className="text-sm text-gray-600 mt-1">Paytm Money provider configuration status</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
