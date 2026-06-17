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
  const [theme, setTheme] = useState<'light' | 'dark'>(() =>
    (localStorage.getItem('theme') as 'light' | 'dark') || 'light'
  );

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

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

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark');

  if (!userId) return <ConnectButton onToggleTheme={toggleTheme} theme={theme} />;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-gray-100 to-slate-200 dark:from-slate-900 dark:via-slate-800 dark:to-zinc-900 py-8 px-4 transition-colors duration-200">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-9 h-9 bg-[#0077B5] rounded-lg flex items-center justify-center text-white font-bold text-lg shadow">
            in
          </div>
          <span className="text-lg font-semibold text-slate-800 dark:text-white">LinkedIn MCP</span>
          <span className="ml-auto flex items-center gap-1.5 text-xs font-medium text-green-700 bg-green-50 border border-green-200 rounded-full px-3 py-1 dark:text-green-300 dark:bg-green-500/20 dark:border-green-400/30">
            <span className="w-1.5 h-1.5 bg-green-500 dark:bg-green-400 rounded-full inline-block animate-pulse" />
            Connected
          </span>
          <button
            onClick={toggleTheme}
            className="w-8 h-8 flex items-center justify-center rounded-full bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-600 dark:bg-white/10 dark:hover:bg-white/15 dark:border-white/20 dark:text-white/70 transition-colors"
            title="Toggle theme"
          >
            {theme === 'dark' ? (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>
          <button
            onClick={handleLogout}
            className="text-xs bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-600 hover:text-slate-800 dark:bg-white/10 dark:hover:bg-white/15 dark:border-white/20 dark:text-white/70 dark:hover:text-white rounded-full px-3 py-1 transition-colors"
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
