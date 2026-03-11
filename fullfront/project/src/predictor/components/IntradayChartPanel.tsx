import { useEffect, useMemo, useState } from 'react';
import { BarChart3 } from 'lucide-react';
import { ChartPoint, PredictionHorizon, getChartData } from '../services/api';

interface IntradayChartPanelProps {
  ticker: string;
  predictions?: {
    '10m': PredictionHorizon;
    '30m': PredictionHorizon;
    '1h': PredictionHorizon;
  };
}

type HorizonKey = '10m' | '30m' | '1h';

interface PredictionPlot {
  label: HorizonKey;
  x: number;
  open: number;
  high: number;
  low: number;
  close: number;
  yOpen: number;
  yHigh: number;
  yLow: number;
  yClose: number;
  isBullish: boolean;
}

export default function IntradayChartPanel({ ticker, predictions }: IntradayChartPanelProps) {
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!ticker) {
      setChartData([]);
      return;
    }

    let cancelled = false;
    setLoading(true);
    getChartData(ticker, '2d', '5m')
      .then((data) => {
        if (cancelled) return;
        const cleaned = (data.points || [])
          .map((p) => ({
            time: String(p.time),
            close: Number(p.close),
          }))
          .filter((p) => Number.isFinite(p.close) && !Number.isNaN(new Date(p.time).getTime()))
          .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());
        setChartData(cleaned);
      })
      .catch(() => {
        if (!cancelled) setChartData([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [ticker]);

  const derived = useMemo<{
    minPrice: number;
    maxPrice: number;
    midPrice: number;
    first?: ChartPoint;
    mid?: ChartPoint;
    last?: ChartPoint;
    points: string;
    projectedCloseLine: string;
    predictionPlots: PredictionPlot[];
  }>(() => {
    if (chartData.length === 0) {
      return {
        minPrice: 0,
        maxPrice: 0,
        midPrice: 0,
        points: '',
        projectedCloseLine: '',
        predictionPlots: [],
      };
    }

    const predictionOrder: HorizonKey[] = ['10m', '30m', '1h'];
    const rawPredictions = predictionOrder
      .map((key) => {
        const p = predictions?.[key];
        if (!p) return null;
        return {
          label: key,
          open: Number(p.open),
          high: Number(p.high),
          low: Number(p.low),
          close: Number(p.close),
        };
      })
      .filter(
        (p): p is { label: HorizonKey; open: number; high: number; low: number; close: number } =>
          !!p &&
          Number.isFinite(p.open) &&
          Number.isFinite(p.high) &&
          Number.isFinite(p.low) &&
          Number.isFinite(p.close)
      );

    const closes = chartData.map((p) => p.close);
    const predictionPrices = rawPredictions.flatMap((p) => [p.low, p.high, p.open, p.close]);
    const fullSeries = [...closes, ...predictionPrices];
    const minRaw = Math.min(...fullSeries);
    const maxRaw = Math.max(...fullSeries);
    const baseRange = Math.max(0.0001, maxRaw - minRaw);
    const padding = Math.max(0.0001, baseRange * 0.08);
    const minPrice = minRaw - padding;
    const maxPrice = maxRaw + padding;
    const priceRange = Math.max(0.0001, maxPrice - minPrice);
    const midPrice = minPrice + priceRange / 2;
    const first = chartData[0];
    const mid = chartData[Math.floor((chartData.length - 1) / 2)];
    const last = chartData[chartData.length - 1];

    const chartTop = 4;
    const chartBottom = 68;
    const histMaxX = rawPredictions.length > 0 ? 82 : 98;
    const yForPrice = (price: number) => {
      const rawY = chartBottom - ((price - minPrice) / priceRange) * (chartBottom - chartTop);
      return Math.max(chartTop, Math.min(chartBottom, rawY));
    };

    const points = chartData
      .map((point, i) => {
        const x = chartData.length > 1 ? (i / (chartData.length - 1)) * histMaxX : 0;
        const y = yForPrice(point.close);
        return `${x.toFixed(2)},${y.toFixed(2)}`;
      })
      .join(' ');

    const predictionPlots: PredictionPlot[] = rawPredictions.map((p, index) => {
      const startX = 86;
      const endX = 98;
      const x = rawPredictions.length === 1
        ? endX
        : startX + (index * (endX - startX)) / (rawPredictions.length - 1);
      return {
        label: p.label,
        x,
        open: p.open,
        high: p.high,
        low: p.low,
        close: p.close,
        yOpen: yForPrice(p.open),
        yHigh: yForPrice(p.high),
        yLow: yForPrice(p.low),
        yClose: yForPrice(p.close),
        isBullish: p.close >= p.open,
      };
    });

    const projectedCloseLine = predictionPlots.length > 0
      ? [
          `${histMaxX.toFixed(2)},${yForPrice(last.close).toFixed(2)}`,
          ...predictionPlots.map((p) => `${p.x.toFixed(2)},${p.yClose.toFixed(2)}`),
        ].join(' ')
      : '';

    return { minPrice, maxPrice, midPrice, first, mid, last, points, projectedCloseLine, predictionPlots };
  }, [chartData, predictions]);

  const formatAxisTime = (isoString?: string) => {
    if (!isoString) return '--:--';
    const date = new Date(isoString);
    if (Number.isNaN(date.getTime())) return '--:--';
    return date.toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: 'Asia/Kolkata',
    });
  };

  const formatPrice = (value: number) => `Rs ${value.toFixed(2)}`;

  return (
    <div className="bg-gray-800 rounded-xl shadow-xl border border-gray-700 p-6">
      <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
        <BarChart3 className="w-6 h-6 text-blue-400" />
        Intraday Chart + Forecast Candles
      </h3>

      <p className="text-xs text-gray-400 uppercase tracking-wide mb-3">
        {ticker} | Last 2 trading days | 5m candles (yfinance)
      </p>

      <div className="h-96 bg-gray-900 rounded-lg p-4 overflow-hidden">
        {loading ? (
          <div className="h-full flex items-center justify-center text-sm text-gray-500">Loading chart...</div>
        ) : chartData.length > 1 ? (
          <div className="h-full flex flex-col">
            <div className="flex-1">
              <svg width="100%" height="100%" viewBox="0 0 100 72" preserveAspectRatio="none" className="block overflow-hidden">
                <polyline fill="none" stroke="#1f2937" strokeWidth="0.8" points="0,4 100,4" opacity="0.6" />
                <polyline fill="none" stroke="#1f2937" strokeWidth="0.8" points="0,36 100,36" opacity="0.6" />
                <polyline fill="none" stroke="#1f2937" strokeWidth="0.8" points="0,68 100,68" opacity="0.6" />
                <polyline fill="none" stroke="url(#intradayGradient)" strokeWidth="1.8" points={derived.points} />
                {derived.projectedCloseLine && (
                  <polyline
                    fill="none"
                    stroke="#f59e0b"
                    strokeWidth="1.4"
                    strokeDasharray="1.8 1.6"
                    points={derived.projectedCloseLine}
                  />
                )}
                {derived.predictionPlots.map((p) => {
                  const bodyTop = Math.min(p.yOpen, p.yClose);
                  const bodyHeight = Math.max(0.8, Math.abs(p.yClose - p.yOpen));
                  const candleColor = p.isBullish ? '#22c55e' : '#ef4444';
                  const labelY = Math.max(5.5, p.yHigh - 1.2);
                  const valueY = Math.min(67, p.yClose + 4);

                  return (
                    <g key={p.label}>
                      <line x1={p.x} y1={p.yHigh} x2={p.x} y2={p.yLow} stroke={candleColor} strokeWidth="0.7" />
                      <rect x={p.x - 0.9} y={bodyTop} width="1.8" height={bodyHeight} fill={candleColor} rx="0.25" />
                      <text x={p.x} y={labelY} textAnchor="middle" fontSize="1.9" fill="#e5e7eb">
                        {p.label}
                      </text>
                      <text x={p.x} y={valueY} textAnchor="middle" fontSize="1.65" fill="#94a3b8">
                        {p.close.toFixed(1)}
                      </text>
                    </g>
                  );
                })}
                <defs>
                  <linearGradient id="intradayGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#3b82f6" />
                    <stop offset="100%" stopColor="#60a5fa" />
                  </linearGradient>
                </defs>
              </svg>
            </div>

            <div className="mt-2 flex items-center justify-between text-xs text-gray-400">
              <span>{formatAxisTime(derived.first?.time)}</span>
              <span>{formatAxisTime(derived.mid?.time)}</span>
              <span>{formatAxisTime(derived.last?.time)}</span>
            </div>
            <div className="mt-1 flex items-center justify-between text-xs text-gray-500">
              <span>Low {formatPrice(derived.minPrice)}</span>
              <span>Mid {formatPrice(derived.midPrice)}</span>
              <span>High {formatPrice(derived.maxPrice)}</span>
            </div>
            <div className="mt-3 flex items-center gap-4 text-xs text-gray-400">
              <span className="flex items-center gap-1">
                <span className="w-3 h-0.5 bg-blue-400 rounded" />
                2d Close
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-0.5 border-t border-dashed border-amber-400 rounded" />
                Forecast Path
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-sm" />
                Bullish Candle
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-red-500 rounded-sm" />
                Bearish Candle
              </span>
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-sm text-gray-500">Chart data unavailable</div>
        )}
      </div>
    </div>
  );
}
