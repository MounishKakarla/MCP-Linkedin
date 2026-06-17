const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:3000';

const SCOPES = [
  ['👤', 'Profile, headline & photo'],
  ['🔗', 'First-degree connection count'],
  ['📝', 'Your posts, reactions & comments'],
  ['🔒', 'No write access — ever'],
] as const;

export default function ConnectButton() {
  const handleConnect = () => {
    window.location.href = `${API_URL}/auth/linkedin`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0077B5] via-[#004182] to-[#001B44] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-white/20 backdrop-blur-sm border border-white/30 rounded-2xl flex items-center justify-center text-white font-bold text-3xl mx-auto mb-5 shadow-lg">
            in
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">LinkedIn MCP</h1>
          <p className="text-white/60 text-sm">
            Give Claude read-only access to your LinkedIn network.
          </p>
        </div>

        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-6 shadow-2xl">
          <div className="font-semibold text-white mb-1">Connect your account</div>
          <p className="text-sm text-white/60 mb-5">
            We request read-only scopes. We never post or message on your behalf.
          </p>

          <ul className="space-y-3 mb-6">
            {SCOPES.map(([icon, label]) => (
              <li key={label} className="flex items-center gap-3 text-sm text-white/70">
                <div className="w-8 h-8 rounded-xl bg-white/10 border border-white/20 flex items-center justify-center flex-shrink-0">
                  {icon}
                </div>
                {label}
              </li>
            ))}
          </ul>

          <button
            onClick={handleConnect}
            className="w-full bg-[#0077B5] hover:bg-[#005885] text-white font-semibold rounded-xl py-3 flex items-center justify-center gap-2.5 transition-colors shadow-lg"
          >
            <div className="w-5 h-5 bg-white/20 rounded flex items-center justify-center text-white font-bold text-xs">
              in
            </div>
            Continue with LinkedIn
          </button>
        </div>

        <p className="text-center text-xs text-white/30 mt-4">
          Your OAuth token is stored server-side and never sent to the browser.
        </p>
      </div>
    </div>
  );
}
