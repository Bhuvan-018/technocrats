import { FormEvent, useEffect, useState } from 'react';
import {
  AlertCircle,
  CheckCircle,
  ExternalLink,
  Search,
  TrendingDown,
  TrendingUp,
  XCircle,
} from 'lucide-react';
import { brokerageFetch } from '../services/api';

type BrokerConfig = {
  configured: boolean;
  has_access_token: boolean;
  missing_env_keys?: string[];
};

type OrderSide = 'BUY' | 'SELL';
type OrderType = 'MARKET' | 'LIMIT';

type OrderResult = {
  success: boolean;
  message?: string;
  orderId?: string;
  error?: string;
};

type OrderStatusResult = {
  orderId: string;
  symbol: string;
  side: string;
  status: string;
  quantity: number;
  filledQuantity: number;
  price: number;
  timestamp: string;
};

export function Trade() {
  const [brokerConfig, setBrokerConfig] = useState<BrokerConfig | null>(null);
  const [configLoading, setConfigLoading] = useState(true);
  const [configError, setConfigError] = useState<string | null>(null);

  const [side, setSide] = useState<OrderSide>('BUY');
  const [symbol, setSymbol] = useState('');
  const [quantity, setQuantity] = useState('');
  const [orderType, setOrderType] = useState<OrderType>('MARKET');
  const [price, setPrice] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [orderResponse, setOrderResponse] = useState<OrderResult | null>(null);

  const [orderIdLookup, setOrderIdLookup] = useState('');
  const [statusLoading, setStatusLoading] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [orderStatus, setOrderStatus] = useState<OrderStatusResult | null>(null);

  const loadBrokerConfig = async () => {
    try {
      setConfigLoading(true);
      setConfigError(null);
      const config = await brokerageFetch('/api/broker/paytm/config');
      setBrokerConfig(config);
    } catch (e) {
      setConfigError(e instanceof Error ? e.message : 'Failed to load broker configuration');
      setBrokerConfig(null);
    } finally {
      setConfigLoading(false);
    }
  };

  useEffect(() => {
    loadBrokerConfig();
  }, []);

  const handleConnect = async () => {
    try {
      const res = await brokerageFetch('/api/broker/paytm/connect');
      if (res?.auth_url) {
        window.open(res.auth_url, '_blank', 'noopener,noreferrer');
      }
      await loadBrokerConfig();
    } catch (e) {
      setConfigError(e instanceof Error ? e.message : 'Failed to start broker connection');
    }
  };

  const handleLogout = async () => {
    try {
      await brokerageFetch('/api/broker/paytm/logout', { method: 'DELETE' });
      await loadBrokerConfig();
    } catch (e) {
      setConfigError(e instanceof Error ? e.message : 'Failed to logout from broker');
    }
  };

  const handleSubmitOrder = async (e: FormEvent) => {
    e.preventDefault();
    if (!symbol.trim() || !quantity.trim()) {
      return;
    }

    const parsedQty = Number(quantity);
    const parsedPrice = price.trim() ? Number(price) : 0;
    if (!Number.isFinite(parsedQty) || parsedQty <= 0) {
      setOrderResponse({ success: false, error: 'Quantity must be a positive number' });
      return;
    }
    if (orderType === 'LIMIT' && (!Number.isFinite(parsedPrice) || parsedPrice <= 0)) {
      setOrderResponse({ success: false, error: 'Limit order requires a valid price' });
      return;
    }

    try {
      setSubmitting(true);
      setOrderResponse(null);

      // Backend expects ticker/type and currently validates presence of price.
      const payload = {
        ticker: symbol.trim().toUpperCase(),
        company: symbol.trim().toUpperCase(),
        quantity: parsedQty,
        price: orderType === 'LIMIT' ? parsedPrice : 0,
        type: side,
      };

      const res = await brokerageFetch('/api/trade/place', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      const orderId = res?.order?.order_id;
      setOrderResponse({
        success: true,
        orderId,
        message: orderId ? 'Order placed successfully' : 'Order placed',
      });
    } catch (e) {
      setOrderResponse({
        success: false,
        error: e instanceof Error ? e.message : 'Failed to place order',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleLookup = async (e: FormEvent) => {
    e.preventDefault();
    if (!orderIdLookup.trim()) {
      return;
    }
    try {
      setStatusLoading(true);
      setStatusError(null);
      setOrderStatus(null);
      const raw = await brokerageFetch(`/api/trade/order-status?id=${encodeURIComponent(orderIdLookup.trim())}`);
      setOrderStatus({
        orderId: raw.order_id,
        symbol: raw.ticker,
        side: raw.side || raw.type || '',
        status: raw.status || '',
        quantity: Number(raw.quantity || 0),
        filledQuantity: Number(raw.filled_quantity ?? raw.quantity ?? 0),
        price: Number(raw.price || 0),
        timestamp: raw.timestamp || '',
      });
    } catch (e) {
      setStatusError(e instanceof Error ? e.message : 'Failed to fetch order status');
    } finally {
      setStatusLoading(false);
    }
  };

  const isBrokerConnected = !!(brokerConfig?.configured && brokerConfig?.has_access_token);
  const ordersDisabled = !isBrokerConnected;

  const formatPrice = (value: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(value);

  return (
    <div className="p-6">
      <div className="bg-white rounded-lg shadow-sm">
        <div className="border-b border-gray-200 px-6 py-4">
          <h1 className="text-2xl font-semibold text-gray-900">Trading Dashboard</h1>
        </div>

        <div className="p-6 space-y-6">
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Broker Connection</h2>

            {configLoading && <p className="text-sm text-gray-600">Loading broker configuration...</p>}

            {!configLoading && configError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700 mb-3">
                {configError}
              </div>
            )}

            {!configLoading && brokerConfig && !brokerConfig.configured && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <XCircle className="w-5 h-5 text-red-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-red-900">Broker Not Configured</p>
                    {brokerConfig.missing_env_keys && brokerConfig.missing_env_keys.length > 0 && (
                      <p className="text-sm text-red-700 mt-1">
                        Missing env keys: {brokerConfig.missing_env_keys.join(', ')}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {!configLoading && brokerConfig?.configured && !brokerConfig.has_access_token && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-yellow-700 mt-0.5" />
                  <div>
                    <p className="font-medium text-yellow-900">Broker Not Connected</p>
                    <p className="text-sm text-yellow-800">Connect your Paytm Money account to start trading.</p>
                  </div>
                </div>
                <button
                  onClick={handleConnect}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
                >
                  Connect Paytm
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
            )}

            {!configLoading && isBrokerConnected && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-green-700 mt-0.5" />
                  <div>
                    <p className="font-medium text-green-900">Broker Connected</p>
                    <p className="text-sm text-green-800">Your Paytm account is connected and ready to trade.</p>
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-medium hover:bg-red-700"
                >
                  Logout
                </button>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Order Ticket</h2>

              {ordersDisabled && (
                <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
                  Live broker not connected. Connect Paytm to place orders.
                </div>
              )}

              <form onSubmit={handleSubmitOrder} className="space-y-4">
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setSide('BUY')}
                    className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-semibold transition-colors ${
                      side === 'BUY' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    <TrendingUp className="w-5 h-5" /> BUY
                  </button>
                  <button
                    type="button"
                    onClick={() => setSide('SELL')}
                    className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-semibold transition-colors ${
                      side === 'SELL' ? 'bg-red-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    <TrendingDown className="w-5 h-5" /> SELL
                  </button>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Symbol</label>
                  <input
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                    placeholder="e.g. RELIANCE"
                    disabled={ordersDisabled || submitting}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
                  <input
                    type="number"
                    min="1"
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    placeholder="Enter quantity"
                    disabled={ordersDisabled || submitting}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Order Type</label>
                  <select
                    value={orderType}
                    onChange={(e) => setOrderType(e.target.value as OrderType)}
                    disabled={ordersDisabled || submitting}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="MARKET">Market Order</option>
                    <option value="LIMIT">Limit Order</option>
                  </select>
                </div>

                {orderType === 'LIMIT' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Price</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={price}
                      onChange={(e) => setPrice(e.target.value)}
                      placeholder="Enter limit price"
                      disabled={ordersDisabled || submitting}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      required
                    />
                  </div>
                )}

                <button
                  type="submit"
                  disabled={ordersDisabled || submitting}
                  className={`w-full py-3 rounded-lg text-white font-semibold transition-colors ${
                    side === 'BUY' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
                  } disabled:bg-gray-400 disabled:cursor-not-allowed`}
                >
                  {submitting ? 'Placing Order...' : `Place ${side} Order`}
                </button>
              </form>
            </div>

            <div className="space-y-6">
              {orderResponse && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">Order Response</h2>
                  {orderResponse.success ? (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <p className="font-medium text-green-900">Order Placed Successfully</p>
                      {orderResponse.orderId && (
                        <p className="text-sm text-green-800 mt-1">
                          Order ID: <span className="font-mono">{orderResponse.orderId}</span>
                        </p>
                      )}
                      {orderResponse.message && (
                        <p className="text-sm text-green-700 mt-1">{orderResponse.message}</p>
                      )}
                    </div>
                  ) : (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <p className="font-medium text-red-900">Order Failed</p>
                      <p className="text-sm text-red-700 mt-1">{orderResponse.error || orderResponse.message}</p>
                    </div>
                  )}
                </div>
              )}

              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Order Status Lookup</h2>

                <form onSubmit={handleLookup} className="mb-4">
                  <div className="flex gap-2">
                    <input
                      value={orderIdLookup}
                      onChange={(e) => setOrderIdLookup(e.target.value)}
                      placeholder="Enter Order ID"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                      disabled={statusLoading}
                    />
                    <button
                      type="submit"
                      disabled={statusLoading || !orderIdLookup.trim()}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed inline-flex items-center gap-2"
                    >
                      <Search className="w-4 h-4" />
                      Lookup
                    </button>
                  </div>
                </form>

                {statusLoading && <p className="text-sm text-gray-600">Loading order status...</p>}
                {statusError && <p className="text-sm text-red-700">{statusError}</p>}

                {orderStatus && !statusLoading && !statusError && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm space-y-2">
                    <div className="flex justify-between"><span>Order ID</span><span className="font-mono">{orderStatus.orderId}</span></div>
                    <div className="flex justify-between"><span>Symbol</span><span>{orderStatus.symbol}</span></div>
                    <div className="flex justify-between"><span>Side</span><span>{orderStatus.side}</span></div>
                    <div className="flex justify-between"><span>Status</span><span>{orderStatus.status}</span></div>
                    <div className="flex justify-between"><span>Quantity</span><span>{orderStatus.quantity}</span></div>
                    <div className="flex justify-between"><span>Filled</span><span>{orderStatus.filledQuantity}</span></div>
                    <div className="flex justify-between"><span>Price</span><span>{formatPrice(orderStatus.price)}</span></div>
                    <div className="flex justify-between gap-4">
                      <span>Timestamp</span>
                      <span className="text-right">{orderStatus.timestamp ? new Date(orderStatus.timestamp).toLocaleString() : '-'}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
