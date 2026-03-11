import { useState, useEffect } from 'react';
import { Filter, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { fetchTradeHistory, fetchOrderStatus } from '../services/tradeService';
import type { Transaction, TradeFilters, OrderStatusResponse } from '../types/trade';
import OrderStatusModal from './OrderStatusModal';
import TransactionTable from './TransactionTable';
import FilterPanel from './FilterPanel';

function HistoryPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const [filters, setFilters] = useState<TradeFilters>({
    side: 'ALL',
    startDate: '',
    endDate: '',
    ticker: '',
    page: 1,
    pageSize: 20,
  });

  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    pageSize: 20,
    totalPages: 0,
  });

  const [orderStatusModal, setOrderStatusModal] = useState<{
    show: boolean;
    orderId: string;
    data: OrderStatusResponse | null;
    loading: boolean;
  }>({
    show: false,
    orderId: '',
    data: null,
    loading: false,
  });

  const loadHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchTradeHistory(filters);
      setTransactions(response.transactions);
      setPagination({
        total: response.total,
        page: response.page,
        pageSize: response.pageSize,
        totalPages: Math.ceil(response.total / response.pageSize),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load transaction history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [filters]);

  const handleFilterChange = (newFilters: Partial<TradeFilters>) => {
    setFilters((prev) => ({ ...prev, ...newFilters, page: 1 }));
  };

  const handlePageChange = (newPage: number) => {
    setFilters((prev) => ({ ...prev, page: newPage }));
  };

  const handleCheckOrderStatus = async (orderId: string) => {
    setOrderStatusModal({
      show: true,
      orderId,
      data: null,
      loading: true,
    });

    try {
      const status = await fetchOrderStatus(orderId);
      setOrderStatusModal((prev) => ({
        ...prev,
        data: status,
        loading: false,
      }));
    } catch (err) {
      setOrderStatusModal((prev) => ({
        ...prev,
        loading: false,
      }));
      setError(err instanceof Error ? err.message : 'Failed to fetch order status');
    }
  };

  const closeModal = () => {
    setOrderStatusModal({
      show: false,
      orderId: '',
      data: null,
      loading: false,
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-sm">
          <div className="border-b border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-semibold text-gray-900">Transaction History</h1>
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <Filter className="w-4 h-4" />
                {showFilters ? 'Hide Filters' : 'Show Filters'}
              </button>
            </div>
          </div>

          {showFilters && (
            <FilterPanel filters={filters} onFilterChange={handleFilterChange} />
          )}

          {error && (
            <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <div className="p-6">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : transactions.length === 0 ? (
              <div className="text-center py-12">
                <Search className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600">No transactions found</p>
              </div>
            ) : (
              <>
                <TransactionTable
                  transactions={transactions}
                  onCheckStatus={handleCheckOrderStatus}
                />

                <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
                  <div className="text-sm text-gray-700">
                    Showing {(pagination.page - 1) * pagination.pageSize + 1} to{' '}
                    {Math.min(pagination.page * pagination.pageSize, pagination.total)} of{' '}
                    {pagination.total} transactions
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handlePageChange(pagination.page - 1)}
                      disabled={pagination.page === 1}
                      className="p-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      <ChevronLeft className="w-5 h-5" />
                    </button>

                    <span className="px-4 py-2 text-sm text-gray-700">
                      Page {pagination.page} of {pagination.totalPages}
                    </span>

                    <button
                      onClick={() => handlePageChange(pagination.page + 1)}
                      disabled={pagination.page >= pagination.totalPages}
                      className="p-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      <ChevronRight className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {orderStatusModal.show && (
        <OrderStatusModal
          orderId={orderStatusModal.orderId}
          data={orderStatusModal.data}
          loading={orderStatusModal.loading}
          onClose={closeModal}
        />
      )}
    </div>
  );
}

export default HistoryPage;
