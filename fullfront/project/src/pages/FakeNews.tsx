import { useState } from 'react';
import { AlertCircle, CheckCircle, Loader2, Shield } from 'lucide-react';

const FAKE_NEWS_API_BASE = import.meta.env.VITE_FAKE_NEWS_API || 'http://127.0.0.1:8000';

export function FakeNews() {
  const [newsText, setNewsText] = useState('');
  const [prediction, setPrediction] = useState<'fake' | 'real' | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handlePredict = async () => {
    if (!newsText.trim()) {
      setError('Please enter some text to analyze.');
      return;
    }

    setLoading(true);
    setError('');
    setPrediction(null);

    try {
      const response = await fetch(`${FAKE_NEWS_API_BASE}/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: newsText }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.error || 'Failed to get prediction.');
      }

      setPrediction(data.prediction === 'fake' ? 'fake' : 'real');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error connecting to detector backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handlePredict();
    }
  };

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-8 py-6">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-white" />
            <h1 className="text-3xl font-bold text-white">Fake News Detection System</h1>
          </div>
          <p className="text-blue-100 mt-2">Analyze news and detect potential misinformation.</p>
        </div>

        <div className="p-8">
          <div className="mb-6">
            <label htmlFor="newsInput" className="block text-sm font-medium text-gray-700 mb-2">
              Enter News Article or Text
            </label>
            <textarea
              id="newsInput"
              value={newsText}
              onChange={(e) => setNewsText(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Paste your news article here..."
              className="w-full h-64 px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none resize-none text-gray-700"
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-2">Press Ctrl+Enter to predict quickly.</p>
          </div>

          <button
            onClick={handlePredict}
            disabled={loading || !newsText.trim()}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold py-4 px-6 rounded-lg transition-all flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Shield className="w-5 h-5" />
                Predict
              </>
            )}
          </button>

          {error && (
            <div className="mt-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-r-lg">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <p className="text-red-700 font-medium">{error}</p>
              </div>
            </div>
          )}

          {prediction && !error && (
            <div
              className={`mt-6 p-6 rounded-xl border-2 ${
                prediction === 'fake' ? 'bg-red-50 border-red-300' : 'bg-green-50 border-green-300'
              }`}
            >
              <div className="flex items-center gap-3">
                {prediction === 'fake' ? (
                  <>
                    <AlertCircle className="w-8 h-8 text-red-600 flex-shrink-0" />
                    <div>
                      <h3 className="text-xl font-bold text-red-800">Fake News Detected</h3>
                      <p className="text-red-700 mt-1">This content may contain misinformation. Verify with trusted sources.</p>
                    </div>
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-8 h-8 text-green-600 flex-shrink-0" />
                    <div>
                      <h3 className="text-xl font-bold text-green-800">Real News</h3>
                      <p className="text-green-700 mt-1">This content appears to be legitimate news.</p>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
