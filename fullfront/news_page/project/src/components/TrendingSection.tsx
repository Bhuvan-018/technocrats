import { Flame, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { NewsArticle } from '../lib/supabase';

interface TrendingSectionProps {
  articles: NewsArticle[];
}

export function TrendingSection({ articles }: TrendingSectionProps) {
  if (articles.length === 0) return null;

  const getImpactIcon = (impact: string) => {
    switch (impact) {
      case 'positive':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'negative':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <Minus className="w-4 h-4 text-gray-600" />;
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'positive':
        return 'border-l-green-500';
      case 'negative':
        return 'border-l-red-500';
      default:
        return 'border-l-gray-500';
    }
  };

  return (
    <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-xl shadow-sm border border-orange-100 p-6">
      <div className="flex items-center gap-2 mb-5">
        <Flame className="w-5 h-5 text-orange-600" />
        <h2 className="text-xl font-bold text-gray-900">Top Market-Moving Stories</h2>
      </div>

      <div className="space-y-3">
        {articles.map((article, index) => (
          <div
            key={article.id}
            className={`bg-white rounded-lg p-4 border-l-4 ${getImpactColor(article.impact)} shadow-sm hover:shadow-md transition-shadow duration-200`}
          >
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-orange-100 text-orange-700 rounded-full flex items-center justify-center font-bold text-sm">
                {index + 1}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-semibold text-gray-900 leading-tight">
                    {article.headline}
                  </h3>
                  {getImpactIcon(article.impact)}
                </div>
                {article.related_stocks.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {article.related_stocks.map((stock) => (
                      <span
                        key={stock}
                        className="text-xs font-semibold px-2 py-0.5 bg-blue-100 text-blue-800 rounded"
                      >
                        {stock}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
