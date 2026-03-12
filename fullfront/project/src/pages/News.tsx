import { useEffect, useMemo, useState } from 'react';
import { createClient } from '@supabase/supabase-js';
import {
  AlertCircle,
  Flame,
  Minus,
  Newspaper,
  RefreshCw,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';

type Impact = 'positive' | 'negative' | 'neutral';

type NewsArticle = {
  id: string;
  headline: string;
  summary: string;
  impact: Impact;
  is_trending: boolean;
  source: string;
  related_stocks: string[];
  published_at: string;
};

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
const supabase =
  supabaseUrl && supabaseAnonKey ? createClient(supabaseUrl, supabaseAnonKey) : null;

function toStringArray(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.map((v) => String(v)).filter(Boolean);
  }
  if (typeof value === 'string' && value.trim()) {
    return value
      .split(',')
      .map((part) => part.trim())
      .filter(Boolean);
  }
  return [];
}

function mapRow(row: any): NewsArticle {
  const rawImpact = String(row?.impact || 'neutral').toLowerCase();
  const impact: Impact =
    rawImpact === 'positive' || rawImpact === 'negative' || rawImpact === 'neutral'
      ? rawImpact
      : 'neutral';

  return {
    id: String(row?.id ?? `${row?.headline ?? 'news'}-${row?.published_at ?? ''}`),
    headline: String(row?.headline ?? 'Untitled News'),
    summary: String(row?.summary ?? ''),
    impact,
    is_trending: Boolean(row?.is_trending),
    source: String(row?.source ?? 'Unknown Source'),
    related_stocks: toStringArray(row?.related_stocks),
    published_at: String(row?.published_at ?? new Date().toISOString()),
  };
}

function formatTime(timestamp: string) {
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
}

export function News() {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchNews = async (isRefresh = false) => {
    if (!supabase) {
      setArticles([]);
      setError(
        'News data source is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in fullfront/project/.env.'
      );
      setLoading(false);
      setRefreshing(false);
      return;
    }

    try {
      if (isRefresh) {
        setRefreshing(true);
      }
      setError(null);

      const { data, error: queryError } = await supabase
        .from('news_articles')
        .select('*')
        .order('published_at', { ascending: false })
        .limit(120);

      if (queryError) {
        throw queryError;
      }

      setArticles((data || []).map(mapRow));
    } catch (err) {
      console.error('Error fetching news:', err);
      setError('Unable to load market news right now. Please verify Supabase table access.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchNews();
  }, []);

  const trending = useMemo(() => articles.filter((article) => article.is_trending).slice(0, 3), [articles]);
  const news = useMemo(() => articles.filter((article) => !article.is_trending), [articles]);

  const impactCounts = {
    positive: articles.filter((a) => a.impact === 'positive').length,
    negative: articles.filter((a) => a.impact === 'negative').length,
    neutral: articles.filter((a) => a.impact === 'neutral').length,
  };

  const impactClass = (impact: Impact) => {
    if (impact === 'positive') return 'text-green-600 bg-green-50 border-green-200';
    if (impact === 'negative') return 'text-red-600 bg-red-50 border-red-200';
    return 'text-gray-600 bg-gray-50 border-gray-200';
  };

  const ImpactIcon = ({ impact }: { impact: Impact }) => {
    if (impact === 'positive') return <TrendingUp className="w-4 h-4" />;
    if (impact === 'negative') return <TrendingDown className="w-4 h-4" />;
    return <Minus className="w-4 h-4" />;
  };

  return (
    <div className="p-6 space-y-6">
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Newspaper className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Live Market News & Impact</h1>
              <p className="text-sm text-gray-600 mt-0.5">Real-time financial news with impact tags</p>
            </div>
          </div>

          <button
            onClick={() => fetchNews(true)}
            disabled={refreshing || loading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        <div className="flex items-center gap-3 mt-5 flex-wrap">
          <span className="text-sm font-medium px-3 py-1.5 rounded-full bg-green-50 text-green-700 border border-green-200">
            {impactCounts.positive} Positive
          </span>
          <span className="text-sm font-medium px-3 py-1.5 rounded-full bg-red-50 text-red-700 border border-red-200">
            {impactCounts.negative} Negative
          </span>
          <span className="text-sm font-medium px-3 py-1.5 rounded-full bg-gray-50 text-gray-700 border border-gray-200">
            {impactCounts.neutral} Neutral
          </span>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {loading ? (
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-14 flex items-center justify-center">
          <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
        </div>
      ) : (
        <>
          {trending.length > 0 && (
            <section className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-xl border border-orange-100 p-6">
              <div className="flex items-center gap-2 mb-4">
                <Flame className="w-5 h-5 text-orange-600" />
                <h2 className="text-xl font-bold text-gray-900">Top Market-Moving Stories</h2>
              </div>
              <div className="space-y-3">
                {trending.map((article, idx) => (
                  <div key={article.id} className="bg-white rounded-lg p-4 border-l-4 border-l-orange-400 shadow-sm">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-orange-100 text-orange-700 text-sm font-bold flex items-center justify-center">
                        {idx + 1}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold text-gray-900">{article.headline}</p>
                        {article.related_stocks.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            {article.related_stocks.map((stock) => (
                              <span key={`${article.id}-${stock}`} className="text-xs font-semibold px-2 py-0.5 bg-blue-100 text-blue-800 rounded">
                                {stock}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full border ${impactClass(article.impact)}`}>
                        <ImpactIcon impact={article.impact} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {news.length === 0 && trending.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-14 text-center">
              <Newspaper className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No news articles yet</h3>
              <p className="text-gray-600">News will appear here once rows are available in the `news_articles` table.</p>
            </div>
          ) : (
            <section className="space-y-4">
              <h2 className="text-xl font-bold text-gray-900">Latest News</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
                {news.map((article) => (
                  <article key={article.id} className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <h3 className="text-lg font-semibold text-gray-900 leading-tight">{article.headline}</h3>
                      <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full border ${impactClass(article.impact)}`}>
                        <ImpactIcon impact={article.impact} />
                      </div>
                    </div>

                    <p className="text-sm text-gray-600 leading-relaxed mb-3">{article.summary}</p>

                    {article.related_stocks.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mb-3">
                        {article.related_stocks.map((stock) => (
                          <span key={`${article.id}-list-${stock}`} className="text-xs font-medium px-2 py-0.5 bg-blue-50 text-blue-700 rounded">
                            {stock}
                          </span>
                        ))}
                      </div>
                    )}

                    <div className="text-xs text-gray-500 flex items-center justify-between">
                      <span className="font-medium">{article.source}</span>
                      <span>{formatTime(article.published_at)}</span>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
