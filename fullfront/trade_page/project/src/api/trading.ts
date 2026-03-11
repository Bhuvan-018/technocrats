import { apiClient } from './client';

export interface BrokerConfig {
  configured: boolean;
  has_access_token: boolean;
  missing_env_keys?: string[];
}

export interface OrderRequest {
  symbol: string;
  quantity: number;
  price?: number;
  order_type?: 'MARKET' | 'LIMIT';
}

export interface OrderResponse {
  success: boolean;
  message?: string;
  order_id?: string;
  error?: string;
}

export interface OrderStatus {
  order_id: string;
  status: string;
  symbol: string;
  quantity: number;
  price?: number;
  filled_quantity?: number;
  timestamp?: string;
}

export interface BrokerRequest {
  action: string;
  params?: Record<string, unknown>;
}

export const tradingApi = {
  getBrokerConfig: () =>
    apiClient.get<BrokerConfig>('/broker/paytm/config'),

  connectBroker: () =>
    apiClient.get<{ auth_url: string }>('/broker/paytm/connect'),

  buyOrder: (order: OrderRequest) =>
    apiClient.post<OrderResponse>('/trade/buy', order),

  sellOrder: (order: OrderRequest) =>
    apiClient.post<OrderResponse>('/trade/sell', order),

  placeOrder: (order: OrderRequest & { side: 'BUY' | 'SELL' }) =>
    apiClient.post<OrderResponse>('/trade/place', order),

  getOrderStatus: (orderId: string) =>
    apiClient.get<OrderStatus>(`/trade/order-status?id=${orderId}`),

  brokerRequest: (request: BrokerRequest) =>
    apiClient.post<unknown>('/broker/paytm/request', request),

  logoutBroker: () =>
    apiClient.delete<{ success: boolean }>('/broker/paytm/logout'),
};
