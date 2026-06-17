import { useState, useRef, useEffect } from 'react';
import { sendChatMessage, Message, AttachedImage } from '../api/chat';

interface Props {
  userId: string;
  apiKey: string;
  onChangeKey: () => void;
}

const SUGGESTIONS = [
  'Show my LinkedIn profile',
  'Create a post about AI trends',
  'What is my email address?',
];

export default function Chat({ userId, apiKey, onChangeKey }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [attachedImage, setAttachedImage] = useState<AttachedImage | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      const base64 = dataUrl.split(',')[1];
      setAttachedImage({ data: base64, mimeType: file.type || 'image/jpeg' });
      setImagePreview(dataUrl);
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  const clearImage = () => {
    setAttachedImage(null);
    setImagePreview(null);
  };

  const send = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || loading) return;

    const userMsg: Message = { role: 'user', content };
    const next = [...messages, userMsg];
    setMessages(next);
    setInput('');
    const imgToSend = attachedImage;
    setAttachedImage(null);
    setImagePreview(null);
    setLoading(true);
    setError(null);

    try {
      const result = await sendChatMessage(userId, next, apiKey, imgToSend ?? undefined);
      setMessages([...next, { role: 'assistant', content: result.response }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reach assistant.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-5 flex flex-col min-h-[520px] dark:bg-white/5 dark:border-white/10 dark:backdrop-blur-xl dark:shadow-none">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-semibold text-slate-800 dark:text-white">Claude Chat</span>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 dark:text-white/50">LinkedIn tools enabled</span>
          <button
            onClick={onChangeKey}
            className="text-xs text-slate-400 hover:text-slate-600 bg-slate-50 hover:bg-slate-100 border border-slate-200 dark:text-white/40 dark:hover:text-white/70 dark:bg-white/5 dark:hover:bg-white/10 dark:border-white/10 rounded-full px-2.5 py-0.5 transition-colors"
            title="Change Anthropic API key"
          >
            Change key
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-1">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full py-8 gap-4">
            <div className="w-12 h-12 rounded-2xl bg-slate-50 border border-slate-200 dark:bg-white/10 dark:border-white/20 flex items-center justify-center">
              <svg className="w-6 h-6 text-slate-400 dark:text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <p className="text-slate-400 dark:text-white/50 text-sm text-center">
              Ask Claude about your LinkedIn or create posts.
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="text-xs bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-500 hover:text-slate-700 dark:bg-white/10 dark:hover:bg-white/15 dark:border-white/20 dark:text-white/60 dark:hover:text-white rounded-full px-3 py-1.5 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap ${
                msg.role === 'user'
                  ? 'bg-[#0077B5] text-white rounded-br-sm'
                  : 'bg-slate-100 text-slate-800 border border-slate-200 rounded-bl-sm dark:bg-white/10 dark:text-white dark:border-white/10'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-100 border border-slate-200 dark:bg-white/10 dark:border-white/10 rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex gap-1.5 items-center">
                {[0, 150, 300].map(delay => (
                  <span
                    key={delay}
                    className="w-2 h-2 bg-slate-300 dark:bg-white/50 rounded-full animate-bounce"
                    style={{ animationDelay: `${delay}ms` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="text-xs text-red-600 bg-red-50 border border-red-200 dark:text-red-300 dark:bg-red-500/10 dark:border-red-400/20 rounded-xl px-3 py-2">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {imagePreview && (
        <div className="flex items-center gap-2 mb-2">
          <div className="relative inline-block">
            <img src={imagePreview} alt="Attached" className="h-16 w-16 object-cover rounded-lg border border-slate-200 dark:border-white/20" />
            <button
              onClick={clearImage}
              className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-slate-600 text-white rounded-full text-xs flex items-center justify-center leading-none hover:bg-slate-800"
              title="Remove image"
            >
              ×
            </button>
          </div>
          <span className="text-xs text-slate-400 dark:text-white/50">Image attached</span>
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
      />

      <div className="flex gap-2">
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
          title="Attach image"
          className="bg-slate-50 hover:bg-slate-100 border border-slate-300 text-slate-500 hover:text-slate-700 dark:bg-white/5 dark:hover:bg-white/10 dark:border-white/20 dark:text-white/50 dark:hover:text-white/80 disabled:opacity-40 rounded-xl px-3 py-2.5 transition-colors flex-shrink-0"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </button>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          placeholder="Ask about your LinkedIn..."
          disabled={loading}
          className="flex-1 bg-slate-50 border border-slate-300 text-slate-900 placeholder-slate-400 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-slate-400 focus:bg-white transition-all disabled:opacity-50 dark:bg-white/5 dark:border-white/20 dark:text-white dark:placeholder-white/40 dark:focus:border-white/50 dark:focus:bg-white/10"
        />
        <button
          onClick={() => send()}
          disabled={loading || !input.trim()}
          className="bg-[#0077B5] hover:bg-[#005885] disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl px-4 py-2.5 text-sm font-medium transition-colors flex-shrink-0"
        >
          Send
        </button>
      </div>
    </div>
  );
}
