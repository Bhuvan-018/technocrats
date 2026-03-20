import { useEffect, useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight, Filter, Search, X } from 'lucide-react';
const MOCK_API = 'http://127.0.0.1:9050';

async function mockFetch(path: string, options: RequestInit = {}) {
  const response = await fetch(`${MOCK_API}${path}`, {
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

type TxnRow = {
  transactionId: string;
  orderId: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  status: string;
  time: string;
};

type OrderStatus = {
  orderId: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  filledQuantity: number;
  price: number;
  status: string;
  timestamp: string;
};

type Filters = {
  side: 'ALL' | 'BUY' | 'SELL';
  ticker: string;
  startDate: string;
  endDate: string;
  page: number;
  pageSize: number;
};

export function History() {
  const [rows, setRows] = useState<TxnRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<Filters>({
    side: 'ALL',
    ticker: '',
    startDate: '',
    endDate: '',
    page: 1,
    pageSize: 20,
  });

  const [statusModal, setStatusModal] = useState<{
    open: boolean;
    loading: boolean;
    data: OrderStatus | null;
  }>({
    open: false,
    loading: false,
    data: null,
  });

  const formatTime = (timestamp: string) =>
    new Date(timestamp).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });

  const formatPrice = (price: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(price);

  const loadHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await mockFetch('/api/trade/history');
      const mapped: TxnRow[] = (res.transactions || []).map((row: any) => ({
        transactionId: row.transaction_id,
        orderId: row.order_id,
        symbol: row.ticker,
        side: row.side,
        quantity: Number(row.quantity || 0),
        price: Number(row.price || 0),
        status: row.status,
        time: row.timestamp,
      }));
      setRows(mapped);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const filteredRows = useMemo(() => {
    let result = rows;

    if (filters.side !== 'ALL') {
      result = result.filter((r) => r.side === filters.side);
    }

    if (filters.ticker.trim()) {
      const q = filters.ticker.trim().toUpperCase();
      result = result.filter((r) => r.symbol.toUpperCase().includes(q));
    }

    if (filters.startDate) {
      const start = new Date(filters.startDate);
      result = result.filter((r) => new Date(r.time) >= start);
    }

    if (filters.endDate) {
      const end = new Date(filters.endDate);
      end.setHours(23, 59, 59, 999);
      result = result.filter((r) => new Date(r.time) <= end);
    }

    return result;
  }, [rows, filters.side, filters.ticker, filters.startDate, filters.endDate]);

  const total = filteredRows.length;
  const totalPages = Math.max(1, Math.ceil(total / filters.pageSize));
  const page = Math.min(filters.page, totalPages);
  const startIndex = (page - 1) * filters.pageSize;
  const pagedRows = filteredRows.slice(startIndex, startIndex + filters.pageSize);

  const setFilter = (partial: Partial<Filters>) => {
    setFilters((prev) => ({ ...prev, ...partial, page: 1 }));
  };

  const openOrderStatus = async (orderId: string) => {
    setStatusModal({ open: true, loading: true, data: null });
    try {
      const row = await mockFetch(`/api/trade/order-status?id=${encodeURIComponent(orderId)}`);
      const mapped: OrderStatus = {
        orderId: row.order_id,
        symbol: row.ticker,
        side: row.side,
        quantity: Number(row.quantity || 0),
        filledQuantity: Number(row.quantity || 0),
        price: Number(row.price || 0),
        status: row.status,
        timestamp: row.timestamp,
      };
      setStatusModal({ open: true, loading: false, data: mapped });
    } catch (e) {
      setStatusModal({ open: true, loading: false, data: null });
      setError(e instanceof Error ? e.message : 'Failed to fetch order status');
    }
  };

  return (
    <div className="p-6">
      <div className="bg-white rounded-lg shadow-sm">
        <div className="border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-gray-900">Transaction History</h1>
          <button
            onClick={() => setShowFilters((v) => !v)}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Filter className="w-4 h-4" />
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </button>
        </div>

        {showFilters && (
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Side</label>
                <select
                  value={filters.side}
                  onChange={(e) => setFilter({ side: e.target.value as Filters['side'] })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="ALL">All</option>
                  <option value="BUY">Buy</option>
                  <option value="SELL">Sell</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ticker</label>
                <input
                  type="text"
                  value={filters.ticker}
                  onChange={(e) => setFilter({ ticker: e.target.value })}
                  placeholder="e.g. RELIANCE"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                <input
                  type="date"
                  value={filters.startDate}
                  onChange={(e) => setFilter({ startDate: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                <input
                  type="date"
                  value={filters.endDate}
                  onChange={(e) => setFilter({ endDate: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
            {error}
          </div>
        )}

        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : pagedRows.length === 0 ? (
            <div className="text-center py-12">
              <Search className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600">No transactions found</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Time</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Transaction ID</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Order ID</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Symbol</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Side</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Quantity</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">Price</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Status</th>
                      <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {pagedRows.map((row) => (
                      <tr key={row.transactionId} className="hover:bg-gray-50">
                        <td className="py-3 px-4 text-sm text-gray-900">{formatTime(row.time)}</td>
                        <td className="py-3 px-4 text-sm text-gray-600 font-mono">{row.transactionId}</td>
                        <td className="py-3 px-4 text-sm text-gray-600 font-mono">{row.orderId}</td>
                        <td className="py-3 px-4 text-sm font-medium text-gray-900">{row.symbol}</td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              row.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {row.side}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm text-right text-gray-900">{row.quantity.toLocaleString()}</td>
                        <td className="py-3 px-4 text-sm text-right text-gray-900 font-medium">{formatPrice(row.price)}</td>
                        <td className="py-3 px-4">
                          <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
                            {row.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <button
                            onClick={() => openOrderStatus(row.orderId)}
                            className="inline-flex items-center gap-1 px-3 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100"
                          >
                            Status
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
                <div className="text-sm text-gray-700">
                  Showing {startIndex + 1} to {Math.min(startIndex + filters.pageSize, total)} of {total} transactions
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setFilters((p) => ({ ...p, page: Math.max(1, page - 1) }))}
                    disabled={page <= 1}
                    className="p-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <span className="px-4 py-2 text-sm text-gray-700">Page {page} of {totalPages}</span>
                  <button
                    onClick={() => setFilters((p) => ({ ...p, page: Math.min(totalPages, page + 1) }))}
                    disabled={page >= totalPages}
                    className="p-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {statusModal.open && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Order Status</h2>
              <button onClick={() => setStatusModal({ open: false, loading: false, data: null })}>
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            <div className="px-6 py-4">
              {statusModal.loading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : statusModal.data ? (
                <div className="space-y-3 text-sm text-gray-800">
                  <div><span className="font-medium">Order ID:</span> {statusModal.data.orderId}</div>
                  <div><span className="font-medium">Symbol:</span> {statusModal.data.symbol}</div>
                  <div><span className="font-medium">Side:</span> {statusModal.data.side}</div>
                  <div><span className="font-medium">Status:</span> {statusModal.data.status}</div>
                  <div><span className="font-medium">Quantity:</span> {statusModal.data.quantity}</div>
                  <div><span className="font-medium">Filled:</span> {statusModal.data.filledQuantity}</div>
                  <div><span className="font-medium">Price:</span> {formatPrice(statusModal.data.price)}</div>
                  <div><span className="font-medium">Time:</span> {formatTime(statusModal.data.timestamp)}</div>
                </div>
              ) : (
                <div className="text-sm text-gray-600">Failed to load order status.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
