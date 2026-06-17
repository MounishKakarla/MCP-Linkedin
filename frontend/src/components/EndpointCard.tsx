import { useState } from 'react';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000';

interface Props {
  userId: string;
}

export default function EndpointCard({ userId }: Props) {
  const [copied, setCopied] = useState(false);
  const endpointUrl = `${API_URL}/mcp/${userId}`;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(endpointUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-5 shadow-xl">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-white">Your MCP endpoint</span>
        <span className="flex items-center gap-1 text-xs font-medium text-green-300 bg-green-500/20 border border-green-400/30 rounded-full px-2.5 py-0.5">
          <span className="w-1.5 h-1.5 bg-green-400 rounded-full inline-block" />
          Live
        </span>
      </div>

      <p className="text-xs text-white/50 mb-3">
        Paste this URL into Claude → Settings → Integrations → Add MCP Server
      </p>

      <div className="flex items-center gap-2.5 bg-white/5 border border-white/20 rounded-xl px-3 py-2.5">
        <span className="flex-1 font-mono text-xs text-blue-300 truncate">{endpointUrl}</span>
        <button
          onClick={handleCopy}
          className="flex-shrink-0 flex items-center gap-1 text-xs bg-white/10 hover:bg-white/20 border border-white/20 text-white/70 hover:text-white rounded-md px-2.5 py-1 transition-colors"
        >
          {copied ? '✓ Copied' : '⎘ Copy'}
        </button>
      </div>

      <p className="text-xs text-white/30 mt-2">Rate limited to 1,000 calls / day</p>
    </div>
  );
}
