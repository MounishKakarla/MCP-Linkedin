const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000';

export interface LogEntry {
  tool_name: string;
  called_at: string;
}

export async function fetchActivityLog(userId: string): Promise<LogEntry[]> {
  const res = await fetch(`${API_URL}/api/activity/${userId}`);
  if (!res.ok) return [];
  return res.json();
}
