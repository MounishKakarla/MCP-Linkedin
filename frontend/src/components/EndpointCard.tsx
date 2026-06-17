import { useState } from 'react';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

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
    <div className="bg-white border border-gray-200 rounded-2xl p-5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold">Your MCP endpoint</span>
        <span className="flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 border border-green-200 rounded-full px-2.5 py-0.5">
          <span className="w-1.5 h-1.5 bg-green-600 rounded-full inline-block" />
          Live
        </span>
      </div>

      <p className="text-xs text-gray-500 mb-3">
        Paste this URL into Claude → Settings → Integrations → Add MCP Server
      </p>

      <div className="flex items-center gap-2.5 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5">
        <span className="flex-1 font-mono text-xs text-blue-600 truncate">{endpointUrl}</span>
        <button
          onClick={handleCopy}
          className="flex-shrink-0 flex items-center gap-1 text-xs bg-white border border-gray-300 rounded-md px-2.5 py-1 hover:bg-gray-50 transition-colors"
        >
          {copied ? '✓ Copied' : '⎘ Copy'}
        </button>
      </div>

      <p className="text-xs text-gray-400 mt-2">Rate limited to 1,000 calls / day</p>
    </div>
  );
}
