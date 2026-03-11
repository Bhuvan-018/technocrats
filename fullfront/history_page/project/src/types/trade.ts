export interface Transaction {
  time: string;
  transactionId: string;
  orderId: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  status: string;
}

export interface TradeHistoryResponse {
  transactions: Transaction[];
  total: number;
  page: number;
  pageSize: number;
}

export interface OrderStatusResponse {
  orderId: string;
  status: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  filledQuantity: number;
  price: number;
  timestamp: string;
}

export interface TradeFilters {
  side?: 'BUY' | 'SELL' | 'ALL';
  startDate?: string;
  endDate?: string;
  ticker?: string;
  page?: number;
  pageSize?: number;
}
