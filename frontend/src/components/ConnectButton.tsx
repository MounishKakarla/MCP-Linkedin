interface Props {
  onToggleTheme: () => void;
  theme: 'light' | 'dark';
}

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000';

const SCOPES = [
  ['👤', 'Profile, headline & photo'],
  ['🔗', 'First-degree connection count'],
  ['📝', 'Your posts, reactions & comments'],
  ['🔒', 'No write access — ever'],
] as const;

export default function ConnectButton({ onToggleTheme, theme }: Props) {
  const handleConnect = () => {
    window.location.href = `${API_URL}/auth/linkedin`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-gray-100 to-slate-200 dark:from-slate-900 dark:via-slate-800 dark:to-zinc-900 flex items-center justify-center p-4 transition-colors duration-200">
      {/* Theme toggle — top right */}
      <button
        onClick={onToggleTheme}
        className="fixed top-4 right-4 w-9 h-9 flex items-center justify-center rounded-full bg-white border border-slate-200 text-slate-500 hover:text-slate-800 shadow-sm dark:bg-white/10 dark:border-white/20 dark:text-white/60 dark:hover:text-white transition-colors"
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

      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-[#0077B5] rounded-2xl flex items-center justify-center text-white font-bold text-3xl mx-auto mb-5 shadow-lg">
            in
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">LinkedIn MCP</h1>
          <p className="text-slate-500 dark:text-white/50 text-sm">
            Give Claude read-only access to your LinkedIn network.
          </p>
        </div>

        <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-6 dark:bg-white/5 dark:border-white/10 dark:backdrop-blur-xl dark:shadow-none">
          <div className="font-semibold text-slate-800 dark:text-white mb-1">Connect your account</div>
          <p className="text-sm text-slate-500 dark:text-white/50 mb-5">
            We request read-only scopes. We never post or message on your behalf.
          </p>

          <ul className="space-y-3 mb-6">
            {SCOPES.map(([icon, label]) => (
              <li key={label} className="flex items-center gap-3 text-sm text-slate-500 dark:text-white/60">
                <div className="w-8 h-8 rounded-xl bg-slate-50 border border-slate-200 dark:bg-white/10 dark:border-white/20 flex items-center justify-center flex-shrink-0">
                  {icon}
                </div>
                {label}
              </li>
            ))}
          </ul>

          <button
            onClick={handleConnect}
            className="w-full bg-[#0077B5] hover:bg-[#005885] text-white font-semibold rounded-xl py-3 flex items-center justify-center gap-2.5 transition-colors shadow"
          >
            <div className="w-5 h-5 bg-white/20 rounded flex items-center justify-center text-white font-bold text-xs">
              in
            </div>
            Continue with LinkedIn
          </button>
        </div>

        <p className="text-center text-xs text-slate-400 dark:text-white/30 mt-4">
          Your OAuth token is stored server-side and never sent to the browser.
        </p>
      </div>
    </div>
  );
}
