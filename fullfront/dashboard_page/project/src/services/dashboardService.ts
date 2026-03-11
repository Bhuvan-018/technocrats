import { apiRequest } from '../utils/api'
import {
  DashboardData,
  MarketStatus,
  Index,
  OilPrice,
  BrokerConfig,
  Order,
  Transaction,
} from '../types/dashboard'

export const dashboardService = {
  getDashboard: () => apiRequest<DashboardData>('/trade/dashboard'),

  getMarketStatus: () => apiRequest<MarketStatus>('/market-status'),

  getIndices: () => apiRequest<Index[]>('/indices'),

  getOilPrice: () => apiRequest<OilPrice>('/oil-price'),

  getBrokerConfig: () => apiRequest<BrokerConfig>('/broker/paytm/config'),

  getRecentOrders: () => apiRequest<Order[]>('/trade/orders/recent'),

  getRecentTransactions: () => apiRequest<Transaction[]>('/trade/transactions/recent'),
}
