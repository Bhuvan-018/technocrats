import { useEffect, useState } from 'react';
import { ChevronDown, ChevronUp, Lightbulb, History } from 'lucide-react';
import { CoreIndicators, Feature, BacktestRow, getBacktest, getExplainability } from '../services/api';

interface DeepDiveProps {
  ticker: string;
}

export default function DeepDive({ ticker }: DeepDiveProps) {
  const [expanded, setExpanded] = useState(false);
  const [features, setFeatures] = useState<Feature[]>([]);
  const [coreIndicators, setCoreIndicators] = useState<CoreIndicators>({});
  const [backtest, setBacktest] = useState<BacktestRow[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (expanded && ticker) {
      setLoading(true);
      Promise.all([getExplainability(ticker), getBacktest(ticker, 10, '10m')])
        .then(([explainData, backtestData]) => {
          setFeatures(explainData.top_features || []);
          setCoreIndicators(explainData.core_indicators || {});
          setBacktest(backtestData.rows || []);
        })
        .finally(() => setLoading(false));
    }
  }, [expanded, ticker]);

  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
  };

  const coreRows = [
    { label: 'RSI', value: coreIndicators.RSI ?? 0 },
    { label: 'SMA20', value: coreIndicators.SMA20 ?? 0 },
    { label: 'ATR', value: coreIndicators.ATR ?? 0 },
  ];

  return (
    <div className="bg-gray-800 rounded-xl shadow-xl border border-gray-700 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-750 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-yellow-400" />
          <h3 className="text-lg font-bold text-white">Deep Dive: Model Explanation</h3>
        </div>
        {expanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
      </button>

      {expanded && (
        <div className="px-6 pb-6 space-y-6 border-t border-gray-700">
          {loading ? (
            <div className="py-8 space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 bg-gray-900 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <>
              <div className="pt-6">
                <h4 className="text-sm font-semibold text-gray-300 mb-4">Core Indicators (Streamlit-aligned)</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {coreRows.map((item) => (
                    <div key={item.label} className="bg-gray-900 border border-gray-700 rounded-lg p-3">
                      <p className="text-xs text-gray-400 mb-1">{item.label}</p>
                      <p className="text-lg font-semibold text-white">{(item.value * 100).toFixed(2)}%</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-6 border-t border-gray-700">
                <h4 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
                  <BarChart className="w-4 h-4" />
                  Feature Importance
                </h4>
                <div className="space-y-3">
                  {features.map((feature, i) => (
                    <div key={i} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-300">{feature.feature}</span>
                        <span className="text-gray-400 font-mono">{(feature.importance * 100).toFixed(1)}%</span>
                      </div>
                      <div className="h-2 bg-gray-900 rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-blue-600 to-blue-400" style={{ width: `${feature.importance * 100}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-6 border-t border-gray-700">
                <h4 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
                  <History className="w-4 h-4" />
                  Recent Predictions vs Actuals
                </h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="text-xs uppercase text-gray-400 border-b border-gray-700">
                      <tr>
                        <th className="text-left py-3 px-2">Date</th>
                        <th className="text-left py-3 px-2">Horizon</th>
                        <th className="text-right py-3 px-2">Predicted</th>
                        <th className="text-right py-3 px-2">Actual</th>
                        <th className="text-right py-3 px-2">Error</th>
                      </tr>
                    </thead>
                    <tbody className="text-gray-300">
                      {backtest.map((row, i) => (
                        <tr key={i} className="border-b border-gray-800 hover:bg-gray-900">
                          <td className="py-3 px-2">{formatDate(row.date)}</td>
                          <td className="py-3 px-2">{row.horizon || '10m'}</td>
                          <td className="text-right py-3 px-2 font-mono">Rs {row.predicted_close.toFixed(2)}</td>
                          <td className="text-right py-3 px-2 font-mono">Rs {row.actual_close.toFixed(2)}</td>
                          <td className={`text-right py-3 px-2 font-mono ${row.error >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                            {row.error >= 0 ? '+' : ''}Rs {row.error.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function BarChart({ className }: { className?: string }) {
  return (
    <svg className={className} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
    </svg>
  );
}
