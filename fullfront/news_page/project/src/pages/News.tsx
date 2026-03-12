import { useEffect, useState } from 'react';
import { Newspaper, BarChart3, Brain, TrendingUp, RefreshCw } from 'lucide-react';
import { supabase, type NewsArticle } from '../lib/supabase';
import { NewsCard } from '../components/NewsCard';
import { TrendingSection } from '../components/TrendingSection';

export function News() {
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [trending, setTrending] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchNews = async () => {
    try {
      const { data: allNews, error } = await supabase
        .from('news_articles')
        .select('*')
        .order('published_at', { ascending: false });

      if (error) throw error;

      if (allNews) {
        setTrending(allNews.filter((article) => article.is_trending).slice(0, 3));
        setNews(allNews.filter((article) => !article.is_trending));
      }
    } catch (error) {
      console.error('Error fetching news:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchNews();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchNews();
  };

  const impactCounts = {
    positive: news.filter((a) => a.impact === 'positive').length,
    negative: news.filter((a) => a.impact === 'negative').length,
    neutral: news.filter((a) => a.impact === 'neutral').length,
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-blue-600 p-2 rounded-lg">
                <Newspaper className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Live Market News & Impact</h1>
                <p className="text-sm text-gray-600 mt-0.5">Real-time financial news with market impact analysis</p>
              </div>
            </div>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              <span className="font-medium">Refresh</span>
            </button>
          </div>

          <div className="flex items-center gap-6 mt-4">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 border border-green-200 rounded-full">
              <TrendingUp className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-green-700">{impactCounts.positive} Positive</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-red-50 border border-red-200 rounded-full">
              <span className="text-sm font-medium text-red-700">{impactCounts.negative} Negative</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-full">
              <span className="text-sm font-medium text-gray-700">{impactCounts.neutral} Neutral</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
          </div>
        ) : (
          <>
            {trending.length > 0 && (
              <div className="mb-8">
                <TrendingSection articles={trending} />
              </div>
            )}

            {news.length === 0 && trending.length === 0 ? (
              <div className="text-center py-20">
                <Newspaper className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No news articles yet</h3>
                <p className="text-gray-600">Check back soon for the latest market updates</p>
              </div>
            ) : (
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-5">Latest News</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                  {news.map((article) => (
                    <NewsCard key={article.id} article={article} />
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </main>

      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <Newspaper className="w-5 h-5 text-gray-600" />
              <span className="text-sm text-gray-600">Market Intelligence Platform</span>
            </div>
            <div className="flex items-center gap-4">
              <a
                href="#markets"
                className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors duration-200"
              >
                <BarChart3 className="w-4 h-4" />
                <span className="font-medium">Markets</span>
              </a>
              <a
                href="#predictions"
                className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors duration-200"
              >
                <TrendingUp className="w-4 h-4" />
                <span className="font-medium">Predictions</span>
              </a>
              <a
                href="#chatbot"
                className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors duration-200"
              >
                <Brain className="w-4 h-4" />
                <span className="font-medium">Chatbot</span>
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
