import { Clock, TrendingUp } from 'lucide-react';

interface MarketSnapshotProps {
  ticker: string;
  currentPrice: number;
  lastCandleTime: string;
  isOpen: boolean;
  sessionStart: string;
  sessionEnd: string;
}

export default function MarketSnapshot({
  ticker,
  currentPrice,
  lastCandleTime,
  isOpen,
  sessionStart,
  sessionEnd,
}: MarketSnapshotProps) {
  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Asia/Kolkata',
    });
  };

  const getTimeUntilClose = () => {
    const now = new Date();
    const istOffset = 5.5 * 60 * 60 * 1000;
    const istTime = new Date(now.getTime() + istOffset);

    const [hours, minutes] = sessionEnd.split(':').map(Number);
    const closeTime = new Date(istTime);
    closeTime.setUTCHours(hours, minutes, 0, 0);

    const diff = closeTime.getTime() - istTime.getTime();
    if (diff <= 0) return 'Market Closed';

    const hoursLeft = Math.floor(diff / (1000 * 60 * 60));
    const minutesLeft = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return `${hoursLeft}h ${minutesLeft}m until close`;
  };

  return (
    <div className="bg-gray-800 rounded-xl shadow-xl border border-gray-700 p-6">
      <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
        <TrendingUp className="w-6 h-6 text-blue-400" />
        Market Snapshot
      </h3>

      <div className="space-y-4">
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Current Price</p>
          <p className="text-4xl font-bold text-white">Rs {currentPrice.toFixed(2)}</p>
        </div>

        <div className="flex items-center gap-2 text-sm text-gray-300">
          <Clock className="w-4 h-4 text-gray-400" />
          <span>Last updated: {formatTime(lastCandleTime)} | {ticker}</span>
        </div>

        <div className="pt-4 border-t border-gray-700">
          <p className="text-xs text-gray-400 mb-2">Session</p>
          <p className="text-sm text-gray-300">
            {sessionStart} - {sessionEnd} IST
          </p>
          {isOpen && <p className="text-xs text-blue-400 mt-2">{getTimeUntilClose()}</p>}
        </div>
      </div>
    </div>
  );
}
