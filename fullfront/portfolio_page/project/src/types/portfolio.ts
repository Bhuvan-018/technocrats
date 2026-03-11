export interface Holding {
  symbol: string;
  company: string;
  quantity: number;
  avgBuyPrice: number;
  currentPrice: number;
  pnl: number;
}

export interface PortfolioData {
  totalValue: number;
  totalPnL: number;
  holdings: Holding[];
}

export type SortField = 'symbol' | 'company' | 'quantity' | 'avgBuyPrice' | 'currentPrice' | 'pnl';
export type SortDirection = 'asc' | 'desc';
