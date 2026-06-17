import { useEffect, useState } from 'react';
import ConnectButton from './components/ConnectButton';
import EndpointCard from './components/EndpointCard';
import ActivityLog from './components/ActivityLog';
import Chat from './components/Chat';
import ApiKeySetup from './components/ApiKeySetup';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000';

export default function App() {
  const [userId, setUserId] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlUserId = params.get('userId');

    if (urlUserId) {
      localStorage.setItem('linkedin_mcp_user_id', urlUserId);
      setUserId(urlUserId);
      window.history.replaceState({}, '', window.location.pathname);
    } else {
      const stored = localStorage.getItem('linkedin_mcp_user_id');
      if (stored) setUserId(stored);
    }

    const storedKey = localStorage.getItem('anthropic_api_key');
    if (storedKey) setApiKey(storedKey);
  }, []);

  const handleLogout = async () => {
    if (!userId) return;
    try {
      await fetch(`${API_URL}/api/logout/${userId}`, { method: 'DELETE' });
    } catch {
      // best-effort server revocation
    }
    localStorage.removeItem('linkedin_mcp_user_id');
    setUserId(null);
  };

  const handleSaveKey = (key: string) => {
    localStorage.setItem('anthropic_api_key', key);
    setApiKey(key);
  };

  const handleChangeKey = () => {
    localStorage.removeItem('anthropic_api_key');
    setApiKey(null);
  };

  if (!userId) return <ConnectButton />;

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0077B5] via-[#004182] to-[#001B44] py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-9 h-9 bg-white/20 backdrop-blur-sm border border-white/30 rounded-lg flex items-center justify-center text-white font-bold text-lg shadow">
            in
          </div>
          <span className="text-lg font-semibold text-white">LinkedIn MCP</span>
          <span className="ml-auto flex items-center gap-1.5 text-xs font-medium text-green-300 bg-green-500/20 border border-green-400/30 rounded-full px-3 py-1">
            <span className="w-1.5 h-1.5 bg-green-400 rounded-full inline-block animate-pulse" />
            Connected
          </span>
          <button
            onClick={handleLogout}
            className="text-xs bg-white/10 hover:bg-white/20 border border-white/20 text-white/70 hover:text-white rounded-full px-3 py-1 transition-colors"
          >
            Logout
          </button>
        </div>

        {/* Two-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-4 items-start">
          <div className="space-y-4">
            <EndpointCard userId={userId} />
            <ActivityLog userId={userId} />
          </div>
          {apiKey ? (
            <Chat userId={userId} apiKey={apiKey} onChangeKey={handleChangeKey} />
          ) : (
            <ApiKeySetup onSave={handleSaveKey} />
          )}
        </div>
      </div>
    </div>
  );
}
