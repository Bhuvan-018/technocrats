import { useState } from 'react';
import { Search, AlertCircle } from 'lucide-react';
import { OrderStatus as OrderStatusType } from '../../api/trading';

interface OrderStatusProps {
  onLookup: (orderId: string) => void;
  status: OrderStatusType | null;
  loading: boolean;
  error: string | null;
}

export function OrderStatus({
  onLookup,
  status,
  loading,
  error,
}: OrderStatusProps) {
  const [orderId, setOrderId] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (orderId.trim()) {
      onLookup(orderId.trim());
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Order Status Lookup</h2>

      <form onSubmit={handleSubmit} className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            placeholder="Enter Order ID"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !orderId.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Search className="w-4 h-4" />
            Lookup
          </button>
        </div>
      </form>

      {loading && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <p className="text-gray-600">Loading order status...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-red-900 mb-1">Error</h3>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        </div>
      )}

      {status && !loading && !error && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-3">Order Details</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-blue-700">Order ID:</span>
              <span className="font-mono text-blue-900">{status.order_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-blue-700">Symbol:</span>
              <span className="font-semibold text-blue-900">{status.symbol}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-blue-700">Status:</span>
              <span className="font-semibold text-blue-900">{status.status}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-blue-700">Quantity:</span>
              <span className="text-blue-900">{status.quantity}</span>
            </div>
            {status.filled_quantity !== undefined && (
              <div className="flex justify-between">
                <span className="text-blue-700">Filled Quantity:</span>
                <span className="text-blue-900">{status.filled_quantity}</span>
              </div>
            )}
            {status.price !== undefined && (
              <div className="flex justify-between">
                <span className="text-blue-700">Price:</span>
                <span className="text-blue-900">{status.price.toFixed(2)}</span>
              </div>
            )}
            {status.timestamp && (
              <div className="flex justify-between">
                <span className="text-blue-700">Timestamp:</span>
                <span className="text-blue-900 text-xs">
                  {new Date(status.timestamp).toLocaleString()}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
