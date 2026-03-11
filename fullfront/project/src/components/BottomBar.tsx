import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { marketAPI } from '../services/api';
import { OilPrice } from '../types';

export function BottomBar() {
  const [oilPrice, setOilPrice] = useState<OilPrice | null>(null);

  useEffect(() => {
    const fetchOilPrice = async () => {
      try {
        const data = await marketAPI.getOilPrice();
        setOilPrice(data);
      } catch (error) {
        console.error('Failed to fetch oil price:', error);
      }
    };

    fetchOilPrice();
    const interval = setInterval(fetchOilPrice, 60000);

    return () => clearInterval(interval);
  }, []);

  if (!oilPrice) {
    return null;
  }

  const isPositive = oilPrice.change >= 0;

  return (
    <div className="bg-gray-900 text-white px-6 py-2 flex items-center justify-center border-t border-gray-800">
      <div className="flex items-center gap-6">
        <span className="text-sm font-medium text-gray-400">Crude Oil (Brent)</span>
        <div className="flex items-center gap-3">
          <span className="text-lg font-bold">${oilPrice.price.toFixed(2)}</span>
          <div
            className={`flex items-center gap-1 text-sm font-medium ${
              isPositive ? 'text-green-400' : 'text-red-400'
            }`}
          >
            {isPositive ? (
              <TrendingUp className="w-4 h-4" />
            ) : (
              <TrendingDown className="w-4 h-4" />
            )}
            <span>
              {isPositive ? '+' : ''}
              {oilPrice.change.toFixed(2)} ({isPositive ? '+' : ''}
              {oilPrice.changePercent.toFixed(2)}%)
            </span>
          </div>
        </div>
        <span className="text-xs text-gray-500">
          Updated: {new Date(oilPrice.timestamp).toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
}
