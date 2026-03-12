import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { NewsArticle } from '../lib/supabase';

interface NewsCardProps {
  article: NewsArticle;
}

export function NewsCard({ article }: NewsCardProps) {
  const impactConfig = {
    positive: {
      icon: TrendingUp,
      color: 'text-green-600',
      bg: 'bg-green-50',
      border: 'border-green-200',
      label: 'Positive Impact',
    },
    negative: {
      icon: TrendingDown,
      color: 'text-red-600',
      bg: 'bg-red-50',
      border: 'border-red-200',
      label: 'Negative Impact',
    },
    neutral: {
      icon: Minus,
      color: 'text-gray-600',
      bg: 'bg-gray-50',
      border: 'border-gray-200',
      label: 'Neutral Impact',
    },
  };

  const config = impactConfig[article.impact];
  const Icon = config.icon;

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 p-5 border border-gray-100">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 leading-tight mb-2">
            {article.headline}
          </h3>
          {article.related_stocks.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-2">
              {article.related_stocks.map((stock) => (
                <span
                  key={stock}
                  className="text-xs font-medium px-2 py-0.5 bg-blue-50 text-blue-700 rounded"
                >
                  {stock}
                </span>
              ))}
            </div>
          )}
        </div>
        <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full ${config.bg} border ${config.border}`}>
          <Icon className={`w-4 h-4 ${config.color}`} />
          <span className={`text-sm font-medium ${config.color}`}>
            {article.impact === 'positive' ? '↑' : article.impact === 'negative' ? '↓' : '→'}
          </span>
        </div>
      </div>

      <p className="text-gray-600 text-sm leading-relaxed mb-3">
        {article.summary}
      </p>

      <div className="flex items-center justify-between text-xs text-gray-500">
        <span className="font-medium">{article.source}</span>
        <span>{formatTime(article.published_at)}</span>
      </div>
    </div>
  );
}
