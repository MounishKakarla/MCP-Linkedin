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
    <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-5 dark:bg-white/5 dark:border-white/10 dark:backdrop-blur-xl dark:shadow-none">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-slate-800 dark:text-white">Your MCP endpoint</span>
        <span className="flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 border border-green-200 rounded-full px-2.5 py-0.5 dark:text-green-300 dark:bg-green-500/20 dark:border-green-400/30">
          <span className="w-1.5 h-1.5 bg-green-500 dark:bg-green-400 rounded-full inline-block" />
          Live
        </span>
      </div>

      <p className="text-xs text-slate-500 dark:text-white/50 mb-3">
        Paste this URL into Claude → Settings → Integrations → Add MCP Server
      </p>

      <div className="flex items-center gap-2.5 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 dark:bg-white/5 dark:border-white/10">
        <span className="flex-1 font-mono text-xs text-[#0077B5] dark:text-blue-300 truncate">{endpointUrl}</span>
        <button
          onClick={handleCopy}
          className="flex-shrink-0 flex items-center gap-1 text-xs bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 rounded-md px-2.5 py-1 transition-colors dark:bg-white/10 dark:hover:bg-white/15 dark:border-white/20 dark:text-white/70"
        >
          {copied ? '✓ Copied' : '⎘ Copy'}
        </button>
      </div>

      <p className="text-xs text-slate-400 dark:text-white/30 mt-2">Rate limited to 1,000 calls / day</p>
    </div>
  );
}
