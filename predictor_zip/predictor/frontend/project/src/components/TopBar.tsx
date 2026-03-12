import { Clock, Activity } from 'lucide-react';
import { MarketStatus } from '../services/api';

interface TopBarProps {
  marketStatus: MarketStatus | null;
}

export default function TopBar({ marketStatus }: TopBarProps) {
  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZone: 'Asia/Kolkata',
    });
  };

  return (
    <div className="sticky top-0 z-50 bg-gray-900 border-b border-gray-800 shadow-lg">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity className="w-8 h-8 text-blue-400" />
            <h1 className="text-2xl font-bold text-white">Market Forecaster</h1>
          </div>

          <div className="flex items-center gap-6">
            {marketStatus && (
              <>
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-gray-400" />
                  <span className="text-sm text-gray-300">{formatTime(marketStatus.current_time_ist)} IST</span>
                </div>

                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${marketStatus.is_open ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
                  <span className={`text-sm font-medium ${marketStatus.is_open ? 'text-green-400' : 'text-red-400'}`}>
                    {marketStatus.is_open ? 'Market Open' : 'Market Closed'}
                  </span>
                </div>

                <div className="px-3 py-1 rounded-full bg-gray-800 border border-gray-700">
                  <span className="text-xs font-medium text-gray-300">
                    {marketStatus.mode === 'live' ? 'Live Forecast' : 'Simulation Mode'}
                  </span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
