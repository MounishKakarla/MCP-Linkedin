const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  response: string;
  toolsUsed: string[];
}

export async function sendChatMessage(userId: string, messages: Message[], apiKey: string): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/chat/${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, apiKey }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail ?? 'Chat request failed');
  }
  return res.json();
}
