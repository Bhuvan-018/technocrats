import { CheckCircle, XCircle, X } from 'lucide-react';
import { OrderResponse as OrderResponseType } from '../../api/trading';

interface OrderResponseProps {
  response: OrderResponseType | null;
  onClose: () => void;
}

export function OrderResponse({ response, onClose }: OrderResponseProps) {
  if (!response) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-start justify-between mb-4">
        <h2 className="text-xl font-semibold">Order Response</h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {response.success ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start">
            <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 mr-3 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-semibold text-green-900 mb-1">
                Order Placed Successfully
              </h3>
              {response.order_id && (
                <p className="text-green-800 text-sm mb-2">
                  Order ID: <span className="font-mono">{response.order_id}</span>
                </p>
              )}
              {response.message && (
                <p className="text-green-700 text-sm">{response.message}</p>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <XCircle className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-semibold text-red-900 mb-1">
                Order Failed
              </h3>
              <p className="text-red-700 text-sm">
                {response.error || response.message || 'Unknown error occurred'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
