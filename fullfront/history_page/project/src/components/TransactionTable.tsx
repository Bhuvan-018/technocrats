import { Info } from 'lucide-react';
import type { Transaction } from '../types/trade';

interface TransactionTableProps {
  transactions: Transaction[];
  onCheckStatus: (orderId: string) => void;
}

function TransactionTable({ transactions, onCheckStatus }: TransactionTableProps) {
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
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
          {transactions.map((transaction) => (
            <tr key={transaction.transactionId} className="hover:bg-gray-50 transition-colors">
              <td className="py-3 px-4 text-sm text-gray-900">
                {formatTime(transaction.time)}
              </td>
              <td className="py-3 px-4 text-sm text-gray-600 font-mono">
                {transaction.transactionId}
              </td>
              <td className="py-3 px-4 text-sm text-gray-600 font-mono">
                {transaction.orderId}
              </td>
              <td className="py-3 px-4 text-sm font-medium text-gray-900">
                {transaction.symbol}
              </td>
              <td className="py-3 px-4">
                <span
                  className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    transaction.side === 'BUY'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {transaction.side}
                </span>
              </td>
              <td className="py-3 px-4 text-sm text-right text-gray-900">
                {transaction.quantity.toLocaleString()}
              </td>
              <td className="py-3 px-4 text-sm text-right text-gray-900 font-medium">
                {formatPrice(transaction.price)}
              </td>
              <td className="py-3 px-4">
                <span
                  className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                    transaction.status === 'COMPLETED' || transaction.status === 'FILLED'
                      ? 'bg-blue-100 text-blue-800'
                      : transaction.status === 'PENDING'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {transaction.status}
                </span>
              </td>
              <td className="py-3 px-4 text-center">
                <button
                  onClick={() => onCheckStatus(transaction.orderId)}
                  className="inline-flex items-center gap-1 px-3 py-1 text-xs font-medium text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                  title="Check order status"
                >
                  <Info className="w-3.5 h-3.5" />
                  Status
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default TransactionTable;
