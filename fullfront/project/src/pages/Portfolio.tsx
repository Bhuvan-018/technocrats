import { useEffect, useMemo, useState } from 'react';
import { ArrowUpDown, DollarSign, TrendingDown, TrendingUp } from 'lucide-react';
const MOCK_API = 'http://127.0.0.1:9050';

async function mockFetch(path: string, options: RequestInit = {}) {
  const response = await fetch(`${MOCK_API}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.message || 'Request failed');
  }
  return response.json();
}
import { Portfolio as PortfolioData, PortfolioHolding } from '../types';

type SortField = 'symbol' | 'name' | 'quantity' | 'avgPrice' | 'currentPrice' | 'gainLoss';
type SortDirection = 'asc' | 'desc';

export function Portfolio() {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>('symbol');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  const loadPortfolio = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await mockFetch('/api/trade/portfolio');
      setPortfolio(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load portfolio');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPortfolio();
  }, []);

  const sortedHoldings = useMemo(() => {
    if (!portfolio?.holdings) {
      return [];
    }
    const rows = [...portfolio.holdings];
    rows.sort((a: PortfolioHolding, b: PortfolioHolding) => {
      const aValue = a[sortField];
      const bValue = b[sortField];
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc' ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
      }
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
      }
      return 0;
    });
    return rows;
  }, [portfolio, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'));
      return;
    }
    setSortField(field);
    setSortDirection('asc');
  };

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(value);

  if (loading) {
    return (
      <div className="p-6">
        <div className="bg-white rounded-lg shadow-sm p-12 flex flex-col items-center">
          <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <p className="mt-4 text-gray-600">Loading portfolio...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-white rounded-lg shadow-sm p-8 max-w-md">
          <h2 className="text-lg font-semibold text-red-700 mb-2">Failed to load portfolio</h2>
          <p className="text-sm text-gray-700 mb-4">{error}</p>
          <button
            onClick={loadPortfolio}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!portfolio) {
    return null;
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Portfolio</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-sm p-6 border-l-4 border-blue-600">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Total Value</p>
              <p className="text-xl font-bold text-gray-900">{formatCurrency(portfolio.totalValue)}</p>
            </div>
            <div className="bg-blue-100 p-3 rounded-full">
              <DollarSign className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border-l-4 border-slate-600">
          <p className="text-sm text-gray-600 mb-1">Total Investment</p>
          <p className="text-xl font-bold text-gray-900">{formatCurrency(portfolio.totalInvestment)}</p>
        </div>

        <div
          className={`bg-white rounded-lg shadow-sm p-6 border-l-4 ${
            portfolio.totalGainLoss >= 0 ? 'border-green-600' : 'border-red-600'
          }`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Total P&L</p>
              <p className={`text-xl font-bold ${portfolio.totalGainLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {portfolio.totalGainLoss >= 0 ? '+' : ''}
                {formatCurrency(portfolio.totalGainLoss)}
              </p>
            </div>
            <div className={`p-3 rounded-full ${portfolio.totalGainLoss >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
              {portfolio.totalGainLoss >= 0 ? (
                <TrendingUp className="w-6 h-6 text-green-600" />
              ) : (
                <TrendingDown className="w-6 h-6 text-red-600" />
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {[
                  { field: 'symbol' as SortField, label: 'Symbol' },
                  { field: 'name' as SortField, label: 'Company' },
                  { field: 'quantity' as SortField, label: 'Qty' },
                  { field: 'avgPrice' as SortField, label: 'Avg Buy Price' },
                  { field: 'currentPrice' as SortField, label: 'Current Price' },
                  { field: 'gainLoss' as SortField, label: 'P&L' },
                ].map(({ field, label }) => (
                  <th
                    key={field}
                    onClick={() => handleSort(field)}
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  >
                    <div className="inline-flex items-center gap-1">
                      <span>{label}</span>
                      <ArrowUpDown className={`w-4 h-4 ${sortField === field ? 'text-blue-600' : 'text-gray-400'}`} />
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedHoldings.map((holding) => (
                <tr key={`${holding.symbol}-${holding.name}`} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">{holding.symbol}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{holding.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{holding.quantity.toLocaleString()}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(holding.avgPrice)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatCurrency(holding.currentPrice)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span
                      className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                        holding.gainLoss >= 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {holding.gainLoss >= 0 ? '+' : ''}
                      {formatCurrency(holding.gainLoss)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {sortedHoldings.length === 0 && (
          <div className="text-center py-12 text-gray-500">No holdings found</div>
        )}
      </div>
    </div>
  );
}
