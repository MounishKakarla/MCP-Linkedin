const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

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
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-6">
          <div className="w-14 h-14 bg-blue-700 rounded-2xl flex items-center justify-center text-white font-bold text-2xl mx-auto mb-4">
            in
          </div>
          <h1 className="text-xl font-semibold mb-1">LinkedIn MCP</h1>
          <p className="text-gray-500 text-sm">
            Give Claude read-only access to your LinkedIn network.
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl p-5">
          <div className="font-semibold mb-1">Connect your account</div>
          <p className="text-sm text-gray-500 mb-4">
            We request read-only scopes. We never post or message on your behalf.
          </p>

          <ul className="space-y-2.5 mb-5">
            {SCOPES.map(([icon, label]) => (
              <li key={label} className="flex items-center gap-2.5 text-sm text-gray-500">
                <div className="w-7 h-7 rounded-lg bg-gray-100 border border-gray-200 flex items-center justify-center flex-shrink-0">
                  {icon}
                </div>
                {label}
              </li>
            ))}
          </ul>

          <button
            onClick={handleConnect}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl py-3 flex items-center justify-center gap-2 transition-colors"
          >
            <div className="w-5 h-5 bg-blue-800 rounded flex items-center justify-center text-white font-bold text-xs">
              in
            </div>
            Continue with LinkedIn
          </button>
        </div>

        <p className="text-center text-xs text-gray-400 mt-3">
          Your OAuth token is stored server-side and never sent to the browser.
        </p>
      </div>
    </div>
  );
}
