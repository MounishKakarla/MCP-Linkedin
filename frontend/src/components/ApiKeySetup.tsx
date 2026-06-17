import { useState } from 'react';

interface Props {
  onSave: (key: string) => void;
}

export default function ApiKeySetup({ onSave }: Props) {
  const [value, setValue] = useState('');
  const [show, setShow] = useState(false);
  const [error, setError] = useState('');

  const handleSave = () => {
    const trimmed = value.trim();
    if (!trimmed.startsWith('sk-ant-')) {
      setError('Key must start with sk-ant-');
      return;
    }
    setError('');
    onSave(trimmed);
  };

  return (
    <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-6 flex flex-col gap-5 min-h-[520px] justify-center dark:bg-white/5 dark:border-white/10 dark:backdrop-blur-xl dark:shadow-none">
      <div className="flex flex-col items-center gap-3 text-center">
        <div className="w-14 h-14 rounded-2xl bg-slate-50 border border-slate-200 dark:bg-white/10 dark:border-white/20 flex items-center justify-center">
          <svg className="w-7 h-7 text-slate-400 dark:text-white/70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
          </svg>
        </div>
        <div>
          <h2 className="text-slate-800 dark:text-white font-semibold text-lg">Connect your Claude</h2>
          <p className="text-slate-500 dark:text-white/50 text-sm mt-1">
            Enter your Anthropic API key to enable in-browser chat.
            <br />Key stays in your browser — never stored on our server.
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <div className="relative">
          <input
            type={show ? 'text' : 'password'}
            value={value}
            onChange={e => { setValue(e.target.value); setError(''); }}
            onKeyDown={e => e.key === 'Enter' && handleSave()}
            placeholder="sk-ant-api03-..."
            className="w-full bg-slate-50 border border-slate-300 text-slate-900 placeholder-slate-400 rounded-xl px-4 py-3 pr-16 text-sm font-mono focus:outline-none focus:border-slate-400 focus:bg-white transition-all dark:bg-white/5 dark:border-white/20 dark:text-white dark:placeholder-white/30 dark:focus:border-white/50 dark:focus:bg-white/10"
          />
          <button
            onClick={() => setShow(s => !s)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-slate-600 dark:text-white/40 dark:hover:text-white/70 transition-colors"
          >
            {show ? 'Hide' : 'Show'}
          </button>
        </div>

        {error && (
          <p className="text-xs text-red-500 dark:text-red-300">{error}</p>
        )}

        <button
          onClick={handleSave}
          disabled={!value.trim()}
          className="w-full bg-[#0077B5] hover:bg-[#005885] disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold rounded-xl py-3 text-sm transition-colors"
        >
          Connect Claude
        </button>

        <a
          href="https://console.anthropic.com/settings/keys"
          target="_blank"
          rel="noopener noreferrer"
          className="text-center text-xs text-slate-400 hover:text-slate-600 dark:text-white/40 dark:hover:text-white/60 transition-colors"
        >
          Get an API key at console.anthropic.com →
        </a>
      </div>
    </div>
  );
}
