export interface DashboardData {
  totalPortfolioValue: number
  todayPnL: number
  totalPnL: number
  holdingsCount: number
  openOrdersCount: number
  holdings: Holding[]
  positions: Position[]
}

export interface Holding {
  symbol: string
  quantity: number
  averagePrice: number
  currentPrice: number
  pnl: number
  pnlPercentage: number
}

export interface Position {
  symbol: string
  quantity: number
  entryPrice: number
  currentPrice: number
  pnl: number
}

export interface MarketStatus {
  status: string
  timestamp: string
  nextOpen?: string
  nextClose?: string
}

export interface Index {
  name: string
  value: number
  change: number
  changePercentage: number
}

export interface OilPrice {
  price: number
  change: number
  changePercentage: number
  lastUpdated: string
}

export interface BrokerConfig {
  connected: boolean
  broker: string
  accountId?: string
  lastSync?: string
}

export interface Order {
  id: string
  symbol: string
  type: string
  side: string
  quantity: number
  price: number
  status: string
  timestamp: string
}

export interface Transaction {
  id: string
  type: string
  symbol: string
  quantity: number
  price: number
  amount: number
  timestamp: string
}
