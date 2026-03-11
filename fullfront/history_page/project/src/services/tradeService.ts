import { apiRequest } from '../utils/apiClient';
import type {
  TradeHistoryResponse,
  OrderStatusResponse,
  TradeFilters,
  Transaction,
} from '../types/trade';

type BackendTransaction = {
  transaction_id: string;
  order_id: string;
  ticker: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  status: string;
  timestamp: string;
};

type BackendHistoryResponse = {
  user_id: string;
  transactions: BackendTransaction[];
};

type BackendOrderStatus = {
  order_id: string;
  ticker: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  status: string;
  timestamp: string;
};

const toTransaction = (row: BackendTransaction): Transaction => ({
  transactionId: row.transaction_id,
  orderId: row.order_id,
  symbol: row.ticker,
  side: row.side,
  quantity: Number(row.quantity || 0),
  price: Number(row.price || 0),
  status: row.status,
  time: row.timestamp,
});

export const fetchTradeHistory = async (
  filters: TradeFilters
): Promise<TradeHistoryResponse> => {
  const response = await apiRequest<BackendHistoryResponse>('/trade/history');

  const allRows = (response.transactions || []).map(toTransaction);
  let filtered = allRows;

  if (filters.side && filters.side !== 'ALL') {
    filtered = filtered.filter((row) => row.side === filters.side);
  }

  if (filters.ticker && filters.ticker.trim()) {
    const needle = filters.ticker.trim().toUpperCase();
    filtered = filtered.filter((row) => row.symbol.toUpperCase().includes(needle));
  }

  if (filters.startDate) {
    const start = new Date(filters.startDate);
    filtered = filtered.filter((row) => new Date(row.time) >= start);
  }

  if (filters.endDate) {
    const end = new Date(filters.endDate);
    end.setHours(23, 59, 59, 999);
    filtered = filtered.filter((row) => new Date(row.time) <= end);
  }

  const page = Math.max(1, Number(filters.page || 1));
  const pageSize = Math.max(1, Number(filters.pageSize || 20));
  const startIndex = (page - 1) * pageSize;
  const pagedRows = filtered.slice(startIndex, startIndex + pageSize);

  return {
    transactions: pagedRows,
    total: filtered.length,
    page,
    pageSize,
  };
};

export const fetchOrderStatus = async (
  orderId: string
): Promise<OrderStatusResponse> => {
  const row = await apiRequest<BackendOrderStatus>(
    `/trade/order-status?id=${encodeURIComponent(orderId)}`
  );

  return {
    orderId: row.order_id,
    symbol: row.ticker,
    side: row.side,
    quantity: Number(row.quantity || 0),
    filledQuantity: Number(row.quantity || 0),
    price: Number(row.price || 0),
    status: row.status,
    timestamp: row.timestamp,
  };
};
