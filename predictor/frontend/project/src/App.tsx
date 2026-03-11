import { useState, useEffect } from 'react';
import TopBar from './components/TopBar';
import InputSection from './components/InputSection';
import ForecastCard from './components/ForecastCard';
import MarketSnapshot from './components/MarketSnapshot';
import TrustMetrics from './components/TrustMetrics';
import DeepDive from './components/DeepDive';
import {
  getMarketStatus,
  getCompanies,
  getPrediction,
  MarketStatus,
  Company,
  PredictionResponse
} from './services/api';

function App() {
  const [marketStatus, setMarketStatus] = useState<MarketStatus | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedTicker, setSelectedTicker] = useState('');
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [showTrust, setShowTrust] = useState(false);

  useEffect(() => {
    Promise.all([
      getMarketStatus(),
      getCompanies()
    ]).then(([status, companiesList]) => {
      setMarketStatus(status);
      setCompanies(companiesList);
    });

    const interval = setInterval(() => {
      getMarketStatus().then(setMarketStatus);
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const handleForecast = async () => {
    if (!selectedTicker) return;

    setLoading(true);
    try {
      const result = await getPrediction(selectedTicker, true);
      setPrediction(result);
    } catch (error) {
      console.error('Forecast error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <TopBar marketStatus={marketStatus} />

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        <InputSection
          companies={companies}
          selectedTicker={selectedTicker}
          onTickerChange={setSelectedTicker}
          onForecast={handleForecast}
          loading={loading}
        />

        {prediction && (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <ForecastCard
                horizon="10m"
                prediction={prediction.predictions['10m']}
                currentPrice={prediction.current_price}
              />
              <ForecastCard
                horizon="30m"
                prediction={prediction.predictions['30m']}
                currentPrice={prediction.current_price}
              />
              <ForecastCard
                horizon="1h"
                prediction={prediction.predictions['1h']}
                currentPrice={prediction.current_price}
              />
            </div>

            <MarketSnapshot
              ticker={prediction.ticker}
              currentPrice={prediction.current_price}
              lastCandleTime={prediction.last_candle_time}
              isOpen={prediction.market_status.is_open}
              sessionStart={marketStatus?.session_start || '09:15'}
              sessionEnd={marketStatus?.session_end || '15:30'}
            />

            <div className="flex items-center gap-3 px-6">
              <input
                type="checkbox"
                id="showTrust"
                checked={showTrust}
                onChange={(e) => setShowTrust(e.target.checked)}
                className="w-4 h-4 rounded bg-gray-800 border-gray-700 text-blue-600 focus:ring-blue-500 focus:ring-offset-gray-900"
              />
              <label htmlFor="showTrust" className="text-sm text-gray-300 cursor-pointer">
                Show accuracy metrics
              </label>
            </div>

            <TrustMetrics ticker={prediction.ticker} show={showTrust} />

            <DeepDive ticker={prediction.ticker} />
          </>
        )}

        {!prediction && !loading && (
          <div className="text-center py-20">
            <p className="text-gray-500 text-lg">
              Select a company and click "Get Forecast" to see predictions
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
