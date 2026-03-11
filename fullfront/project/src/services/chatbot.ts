const CHATBOT_API = import.meta.env.VITE_CHATBOT_API || 'http://127.0.0.1:7000';

async function chatbotFetch(path: string, options: RequestInit = {}) {
  const response = await fetch(`${CHATBOT_API}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = (data && (data.error || data.message)) || 'Request failed';
    throw new Error(message);
  }
  return data;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  stock?: string;
  conversation_id?: string;
  period?: string;
}

export async function sendChatMessage(payload: ChatRequest) {
  return chatbotFetch('/chat', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
