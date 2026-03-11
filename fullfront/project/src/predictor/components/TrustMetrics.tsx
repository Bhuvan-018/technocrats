import { useEffect, useState } from 'react';
import { Shield, Target, Calendar, BarChart3 } from 'lucide-react';
import { getTrustMetrics, TrustMetrics as TrustMetricsType } from '../services/api';

interface TrustMetricsProps {
  ticker: string;
  show: boolean;
}

export default function TrustMetrics({ ticker, show }: TrustMetricsProps) {
  const [metrics, setMetrics] = useState<TrustMetricsType | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (show && ticker) {
      setLoading(true);
      getTrustMetrics(ticker)
        .then(setMetrics)
        .finally(() => setLoading(false));
    }
  }, [show, ticker]);

  if (!show) return null;

  return (
    <div className="bg-gray-800 rounded-xl shadow-xl border border-gray-700 p-6 animate-fadeIn">
      <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
        <Shield className="w-6 h-6 text-green-400" />
        Trust & Accuracy Metrics
      </h3>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-20 bg-gray-900 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : metrics ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-5 h-5 text-green-400" />
              <p className="text-xs text-gray-400 uppercase tracking-wide">Directional Accuracy</p>
            </div>
            <p className="text-3xl font-bold text-white">{(metrics.directional_accuracy * 100).toFixed(1)}%</p>
            <div className="mt-2 h-2 bg-gray-800 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-green-600 to-green-400" style={{ width: `${metrics.directional_accuracy * 100}%` }} />
            </div>
          </div>

          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="w-5 h-5 text-blue-400" />
              <p className="text-xs text-gray-400 uppercase tracking-wide">Mean Absolute Error</p>
            </div>
            <p className="text-3xl font-bold text-white">Rs {metrics.mean_absolute_error.toFixed(2)}</p>
            <p className="text-xs text-gray-500 mt-2">Average prediction error</p>
          </div>

          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="w-5 h-5 text-purple-400" />
              <p className="text-xs text-gray-400 uppercase tracking-wide">Evaluation Window</p>
            </div>
            <p className="text-3xl font-bold text-white">{metrics.window_days}</p>
            <p className="text-xs text-gray-500 mt-2">Days of historical data</p>
          </div>

          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="w-5 h-5 text-orange-400" />
              <p className="text-xs text-gray-400 uppercase tracking-wide">Sample Count</p>
            </div>
            <p className="text-3xl font-bold text-white">{metrics.sample_count.toLocaleString()}</p>
            <p className="text-xs text-gray-500 mt-2">Predictions evaluated</p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
