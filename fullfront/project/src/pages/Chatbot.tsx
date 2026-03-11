import { useMemo, useState } from 'react';
import { Bot, Send, Sparkles } from 'lucide-react';
import { sendChatMessage, ChatMessage } from '../services/chatbot';

const PERIODS = ['5d', '1mo', '3mo', '6mo', '1y'];

export function Chatbot() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: 'Hi, I am STOCKY. Ask me about a stock or market trend.',
    },
  ]);
  const [input, setInput] = useState('');
  const [stock, setStock] = useState('TSLA');
  const [period, setPeriod] = useState('1mo');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const canSend = input.trim().length > 0 && !loading;

  const visibleMessages = useMemo(() => messages, [messages]);

  const handleSend = async () => {
    if (!canSend) return;
    const userMessage: ChatMessage = { role: 'user', content: input.trim() };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput('');
    setError('');
    setLoading(true);

    try {
      const response = await sendChatMessage({
        messages: nextMessages,
        stock: stock.trim() || undefined,
        period,
      });
      const assistantText =
        response.answer ||
        response.response ||
        response.message ||
        response?.data?.response ||
        (typeof response === 'string' ? response : JSON.stringify(response));
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: assistantText || 'No response from STOCKY.' },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Chatbot request failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-600 to-cyan-600 flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">STOCKY</h1>
            <p className="text-sm text-gray-500">Finance chatbot powered by market data</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto bg-gray-50 px-6 py-6 space-y-4">
        {visibleMessages.map((msg, idx) => (
          <div
            key={`${msg.role}-${idx}`}
            className={`max-w-3xl ${
              msg.role === 'user' ? 'ml-auto text-right' : 'mr-auto text-left'
            }`}
          >
            <div
              className={`inline-block rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-900 border border-gray-200'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      <div className="border-t border-gray-200 bg-white px-6 py-4">
        {error && (
          <div className="mb-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            {error}
          </div>
        )}
        <div className="flex flex-wrap items-center gap-3 mb-3">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Sparkles className="w-4 h-4 text-blue-500" />
            Focus stock:
          </div>
          <input
            value={stock}
            onChange={(e) => setStock(e.target.value.toUpperCase())}
            placeholder="TSLA"
            className="w-24 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {PERIODS.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask about a stock, trend, or company news..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSend}
            disabled={!canSend}
            className="inline-flex items-center gap-2 px-4 py-3 rounded-lg bg-blue-600 text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-700"
          >
            {loading ? 'Sending...' : 'Send'}
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
