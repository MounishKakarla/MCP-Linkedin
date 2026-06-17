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
    <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-5 shadow-xl">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-semibold text-white/80">Activity log</span>
        <span className="text-xs text-white/30">Refreshes every 10 s</span>
      </div>

      {log.length === 0 ? (
        <p className="text-sm text-white/40 py-4 text-center">
          No activity yet. Start chatting or ask Claude questions.
        </p>
      ) : (
        <div>
          {log.map((entry, i) => (
            <div
              key={i}
              className={`flex items-center justify-between py-2 ${
                i < log.length - 1 ? 'border-b border-white/10' : ''
              }`}
            >
              <span className="font-mono text-xs text-blue-300">{entry.tool_name}</span>
              <span className="text-xs text-white/40">{formatTime(entry.called_at)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
