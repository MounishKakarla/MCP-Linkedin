import { useEffect, useState } from 'react';
import ConnectButton from './components/ConnectButton';
import EndpointCard from './components/EndpointCard';
import ActivityLog from './components/ActivityLog';

export default function App() {
  const [userId, setUserId] = useState<string | null>(null);

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
  }, []);

  if (!userId) return <ConnectButton />;

  return (
    <div className="min-h-screen bg-gray-50 py-10 px-4">
      <div className="max-w-2xl mx-auto space-y-4">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-9 h-9 bg-blue-700 rounded-lg flex items-center justify-center text-white font-bold text-lg">
            in
          </div>
          <span className="text-lg font-semibold">LinkedIn MCP</span>
          <span className="ml-auto flex items-center gap-1.5 text-xs font-medium text-green-700 bg-green-50 border border-green-200 rounded-full px-3 py-1">
            <span className="w-1.5 h-1.5 bg-green-600 rounded-full inline-block" />
            Connected
          </span>
        </div>
        <EndpointCard userId={userId} />
        <ActivityLog userId={userId} />
      </div>
    </div>
  );
}
