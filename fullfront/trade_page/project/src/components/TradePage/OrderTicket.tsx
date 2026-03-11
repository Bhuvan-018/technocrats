import { useState } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { OrderRequest } from '../../api/trading';

interface OrderTicketProps {
  isBrokerConnected: boolean;
  paperMode: boolean;
  onSubmitOrder: (order: OrderRequest & { side: 'BUY' | 'SELL' }) => void;
  isSubmitting: boolean;
}

export function OrderTicket({
  isBrokerConnected,
  paperMode,
  onSubmitOrder,
  isSubmitting,
}: OrderTicketProps) {
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const [symbol, setSymbol] = useState('');
  const [quantity, setQuantity] = useState('');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [price, setPrice] = useState('');

  const isDisabled = !isBrokerConnected && !paperMode;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!symbol || !quantity) {
      return;
    }

    const order: OrderRequest & { side: 'BUY' | 'SELL' } = {
      symbol: symbol.toUpperCase(),
      quantity: parseInt(quantity, 10),
      order_type: orderType,
      side,
    };

    if (orderType === 'LIMIT' && price) {
      order.price = parseFloat(price);
    }

    onSubmitOrder(order);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Order Ticket</h2>

      {isDisabled && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-yellow-800 text-sm">
            Live broker not connected. Orders are disabled unless in paper mode.
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => setSide('BUY')}
            className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-semibold transition-colors ${
              side === 'BUY'
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <TrendingUp className="w-5 h-5" />
            BUY
          </button>
          <button
            type="button"
            onClick={() => setSide('SELL')}
            className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-semibold transition-colors ${
              side === 'SELL'
                ? 'bg-red-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <TrendingDown className="w-5 h-5" />
            SELL
          </button>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Symbol
          </label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            placeholder="e.g., RELIANCE"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isDisabled || isSubmitting}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Quantity
          </label>
          <input
            type="number"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            placeholder="Enter quantity"
            min="1"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isDisabled || isSubmitting}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Order Type
          </label>
          <select
            value={orderType}
            onChange={(e) => setOrderType(e.target.value as 'MARKET' | 'LIMIT')}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isDisabled || isSubmitting}
          >
            <option value="MARKET">Market Order</option>
            <option value="LIMIT">Limit Order</option>
          </select>
        </div>

        {orderType === 'LIMIT' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Price
            </label>
            <input
              type="number"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="Enter limit price"
              step="0.01"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isDisabled || isSubmitting}
              required
            />
          </div>
        )}

        <button
          type="submit"
          disabled={isDisabled || isSubmitting}
          className={`w-full py-3 px-4 rounded-lg font-semibold text-white transition-colors ${
            side === 'BUY'
              ? 'bg-green-600 hover:bg-green-700'
              : 'bg-red-600 hover:bg-red-700'
          } disabled:bg-gray-400 disabled:cursor-not-allowed`}
        >
          {isSubmitting ? 'Placing Order...' : `Place ${side} Order`}
        </button>
      </form>
    </div>
  );
}
