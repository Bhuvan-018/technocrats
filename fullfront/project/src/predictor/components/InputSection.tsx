import { Search, TrendingUp } from 'lucide-react';
import { Company } from '../services/api';

interface InputSectionProps {
  companies: Company[];
  selectedTicker: string;
  onTickerChange: (ticker: string) => void;
  onForecast: () => void;
  loading: boolean;
}

export default function InputSection({
  companies,
  selectedTicker,
  onTickerChange,
  onForecast,
  loading
}: InputSectionProps) {
  return (
    <div className="bg-gray-800 rounded-xl shadow-xl p-6 border border-gray-700">
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Select Company
          </label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <select
              value={selectedTicker}
              onChange={(e) => onTickerChange(e.target.value)}
              className="w-full pl-11 pr-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
            >
              <option value="">Choose a stock...</option>
              {companies.map((company) => (
                <option key={company.ticker} value={company.ticker}>
                  {company.ticker} - {company.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-end">
          <button
            onClick={onForecast}
            disabled={!selectedTicker || loading}
            className="w-full md:w-auto px-8 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-700 disabled:to-gray-700 text-white font-semibold rounded-lg transition-all duration-200 shadow-lg hover:shadow-blue-500/50 disabled:cursor-not-allowed flex items-center gap-2 justify-center"
          >
            <TrendingUp className="w-5 h-5" />
            {loading ? 'Loading...' : 'Get Forecast'}
          </button>
        </div>
      </div>
    </div>
  );
}
