export interface User {
  id: string;
  email: string;
  name: string;
  subscriptionTier?: string;
  subscriptionExpiry?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export interface MarketIndex {
  name: string;
  value: number;
  change: number;
  changePercent: number;
}

export interface Company {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume?: number;
}

export interface WatchlistItem {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
}

export interface Portfolio {
  totalValue: number;
  totalInvestment: number;
  totalGainLoss: number;
  holdings: PortfolioHolding[];
}

export interface PortfolioHolding {
  symbol: string;
  name: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  gainLoss: number;
  gainLossPercent: number;
}

export interface OilPrice {
  price: number;
  change: number;
  changePercent: number;
  timestamp: string;
}

export interface Prediction {
  symbol: string;
  predictions: number[];
  dates: string[];
  confidence: number;
}

export interface TrustMetrics {
  accuracy: number;
  consistency: number;
  reliability: number;
  overallTrust: number;
}

export interface Explainability {
  factors: Array<{
    name: string;
    impact: number;
    description: string;
  }>;
}

export interface BacktestResult {
  dates: string[];
  predicted: number[];
  actual: number[];
  accuracy: number;
  profitability: number;
}
