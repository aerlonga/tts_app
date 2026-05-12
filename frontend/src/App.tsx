import { Routes, Route, Navigate } from 'react-router-dom';
import { useState } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { Dashboard } from '@/pages/Dashboard';
import { ScriptStudio } from '@/pages/ScriptStudio';
import { TTSStudio } from '@/pages/TTSStudio';
import { BRollSearch } from '@/pages/BRollSearch';
import { VideoAssembly } from '@/pages/VideoAssembly';
import { ShortsGenerator } from '@/pages/ShortsGenerator';
import { Settings } from '@/pages/Settings';
import { useAuth } from '@/hooks/useAuth';
import { Loading } from '@/components/common/Loading';
import { Alert } from '@/components/common/Alert';
import { getErrorMessage } from '@/api/client';

function LoginGate() {
  const { data, isLoading, isError, error, login, loginPending } = useAuth();
  const [apiKey, setApiKey] = useState('');
  const [feedback, setFeedback] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--bg)] px-4">
        <Loading label="Verificando sessão..." />
      </div>
    );
  }

  if (data?.authenticated) {
    return (
      <Routes>
        <Route element={<AppShell authenticated={true} />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/scripts" element={<ScriptStudio />} />
          <Route path="/tts" element={<TTSStudio />} />
          <Route path="/broll" element={<BRollSearch />} />
          <Route path="/assembly" element={<VideoAssembly />} />
          <Route path="/shorts" element={<ShortsGenerator />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,rgba(200,132,10,0.15),transparent_45%),var(--bg)] px-4">
      <div className="w-full max-w-xl rounded-[36px] border border-[var(--border)] bg-[linear-gradient(180deg,rgba(14,16,20,0.96),rgba(8,10,12,0.98))] p-8 shadow-[0_30px_120px_rgba(0,0,0,0.45)]">
        <p className="text-xs uppercase tracking-[0.42em] text-[var(--amber)]">Login obrigatório</p>
        <h1 className="mt-4 font-display text-6xl uppercase leading-none tracking-[0.08em] text-[var(--text)]">API Session</h1>
        <p className="mt-4 text-sm leading-7 text-[var(--text2)]">
          A chave do Gemini será salva apenas na sessão server-side do FastAPI. O frontend não reenviará `api_key` em cada request.
        </p>

        <input
          type="password"
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
          placeholder="GEMINI_API_KEY"
          className="mt-8 w-full rounded-2xl border border-[var(--border2)] bg-[var(--bg3)] px-4 py-4 text-sm text-[var(--text)] outline-none focus:border-[var(--amber)]"
        />

        <button
          type="button"
          onClick={() =>
            void login({ gemini_api_key: apiKey })
              .then(() => setFeedback(null))
              .catch((err) => setFeedback(getErrorMessage(err, 'Falha ao iniciar sessão.')))
          }
          disabled={!apiKey.trim() || loginPending}
          className="mt-5 w-full rounded-full border border-[var(--amber)] bg-[var(--amber)]/10 px-4 py-3 text-sm text-[var(--amber)] transition hover:bg-[var(--amber)]/20 disabled:opacity-50"
        >
          {loginPending ? 'Entrando...' : 'Entrar'}
        </button>

        {feedback ? <Alert tone="error" message={feedback} className="mt-4" /> : null}
        {isError ? <Alert tone="error" message={getErrorMessage(error, 'Backend indisponível.')} className="mt-4" /> : null}
      </div>
    </div>
  );
}

export default function App() {
  return <LoginGate />;
}
