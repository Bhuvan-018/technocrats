import { X } from 'lucide-react';
import type { OrderStatusResponse } from '../types/trade';

interface OrderStatusModalProps {
  orderId: string;
  data: OrderStatusResponse | null;
  loading: boolean;
  onClose: () => void;
}

function OrderStatusModal({ orderId, data, loading, onClose }: OrderStatusModalProps) {
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(price);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Order Status</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 py-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : data ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">
                  Order ID
                </label>
                <p className="text-sm text-gray-900 font-mono">{data.orderId}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">
                    Symbol
                  </label>
                  <p className="text-sm text-gray-900 font-semibold">{data.symbol}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">
                    Side
                  </label>
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      data.side === 'BUY'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {data.side}
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">
                  Status
                </label>
                <span
                  className={`inline-flex px-3 py-1 text-sm font-medium rounded-full ${
                    data.status === 'COMPLETED' || data.status === 'FILLED'
                      ? 'bg-blue-100 text-blue-800'
                      : data.status === 'PENDING' || data.status === 'PARTIAL'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {data.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">
                    Quantity
                  </label>
                  <p className="text-sm text-gray-900">{data.quantity.toLocaleString()}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">
                    Filled
                  </label>
                  <p className="text-sm text-gray-900">
                    {data.filledQuantity.toLocaleString()}
                  </p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">
                  Price
                </label>
                <p className="text-sm text-gray-900 font-semibold">
                  {formatPrice(data.price)}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">
                  Timestamp
                </label>
                <p className="text-sm text-gray-900">{formatTime(data.timestamp)}</p>
              </div>

              {data.filledQuantity < data.quantity && (
                <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    Partially filled: {((data.filledQuantity / data.quantity) * 100).toFixed(1)}%
                    complete
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-600">
              Failed to load order status
            </div>
          )}
        </div>

        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 rounded-b-lg">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default OrderStatusModal;
