import { useEffect, useState } from 'react';
import { fetchActivityLog, LogEntry } from '../api/activity';

interface Props {
  userId: string;
}

function formatTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  const hrs = Math.floor(mins / 60);
  const days = Math.floor(hrs / 24);
  if (days > 0) return days === 1 ? 'Yesterday' : `${days}d ago`;
  if (hrs > 0) return `${hrs}h ago`;
  if (mins > 0) return `${mins} min ago`;
  return 'Just now';
}

export default function ActivityLog({ userId }: Props) {
  const [log, setLog] = useState<LogEntry[]>([]);

  useEffect(() => {
    const load = async () => {
      const entries = await fetchActivityLog(userId);
      setLog(entries);
    };

    load();
    const interval = setInterval(load, 10_000);
    return () => clearInterval(interval);
  }, [userId]);

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-semibold text-gray-500">Activity log</span>
        <span className="text-xs text-gray-400">Refreshes every 10 s</span>
      </div>

      {log.length === 0 ? (
        <p className="text-sm text-gray-400 py-4 text-center">
          No activity yet. Start asking Claude questions about your LinkedIn.
        </p>
      ) : (
        <div>
          {log.map((entry, i) => (
            <div
              key={i}
              className={`flex items-center justify-between py-2 ${
                i < log.length - 1 ? 'border-b border-gray-100' : ''
              }`}
            >
              <span className="font-mono text-xs text-blue-600">{entry.tool_name}</span>
              <span className="text-xs text-gray-400">{formatTime(entry.called_at)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
