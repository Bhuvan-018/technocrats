import { TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { PredictionHorizon } from '../services/api';

interface ForecastCardProps {
  horizon: string;
  prediction: PredictionHorizon;
  currentPrice: number;
}

export default function ForecastCard({ horizon, prediction, currentPrice }: ForecastCardProps) {
  const change = prediction.close - currentPrice;
  const changePercent = (change / currentPrice) * 100;
  const isPositive = change >= 0;

  const horizonLabels: Record<string, string> = {
    '10m': '10 Minutes',
    '30m': '30 Minutes',
    '1h': '1 Hour',
  };

  return (
    <div className="bg-gray-800 rounded-xl shadow-xl border border-gray-700 overflow-hidden hover:shadow-2xl hover:border-gray-600 transition-all duration-300">
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 px-6 py-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-white">{horizonLabels[horizon]}</h3>
          <div className={`flex items-center gap-1 ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
            {isPositive ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
          </div>
        </div>
      </div>

      <div className="p-6 space-y-4">
        <div className="flex items-end justify-between">
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Predicted Close</p>
            <p className="text-3xl font-bold text-white">Rs {prediction.close.toFixed(2)}</p>
          </div>
          <div className={`flex items-center gap-1 px-3 py-1 rounded-full ${isPositive ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
            {isPositive ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
            <span className="text-sm font-semibold">{changePercent.toFixed(2)}%</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-700">
          <div>
            <p className="text-xs text-gray-400 mb-1">High</p>
            <p className="text-lg font-semibold text-green-400">Rs {prediction.high.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 mb-1">Low</p>
            <p className="text-lg font-semibold text-red-400">Rs {prediction.low.toFixed(2)}</p>
          </div>
        </div>

        <div className="pt-4 border-t border-gray-700">
          <p className="text-xs text-gray-400 mb-2">Confidence Range</p>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-300">Rs {prediction.confidence_low.toFixed(2)}</span>
            <div className="flex-1 h-2 bg-gray-900 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-blue-600 to-blue-400" style={{ width: '100%' }} />
            </div>
            <span className="text-sm text-gray-300">Rs {prediction.confidence_high.toFixed(2)}</span>
          </div>
        </div>

        <div className="pt-4 border-t border-gray-700">
          <p className="text-xs text-gray-400 mb-1">Volume</p>
          <p className="text-sm font-medium text-gray-200">{prediction.volume.toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
}
