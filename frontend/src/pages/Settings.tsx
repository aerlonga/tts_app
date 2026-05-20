import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getHealthDetails } from '@/api/health';
import { Alert } from '@/components/common/Alert';
import { Loading } from '@/components/common/Loading';
import { useAuth } from '@/hooks/useAuth';
import { getErrorMessage } from '@/api/client';
import { useAppStore } from '@/stores/appStore';

export function Settings() {
  const { data, login, logout, loginPending, logoutPending } = useAuth();
  const language = useAppStore((state) => state.language);
  const setLanguage = useAppStore((state) => state.setLanguage);
  const healthQuery = useQuery({
    queryKey: ['health-details', 'settings'],
    queryFn: getHealthDetails,
  });
  const [apiKey, setApiKey] = useState('');
  const [feedback, setFeedback] = useState<{ tone: 'success' | 'error' | 'info'; message: string } | null>(null);

  async function handleSave() {
    try {
      await login({ gemini_api_key: apiKey });
      setApiKey('');
      setFeedback({ tone: 'success', message: 'API key salva na sessão server-side.' });
    } catch (error) {
      setFeedback({ tone: 'error', message: getErrorMessage(error, 'Falha ao salvar API key.') });
    }
  }

  async function handleLogout() {
    try {
      await logout();
      setFeedback({ tone: 'info', message: 'Sessão encerrada.' });
    } catch (error) {
      setFeedback({ tone: 'error', message: getErrorMessage(error, 'Falha ao encerrar sessão.') });
    }
  }

  if (healthQuery.isLoading) {
    return <Loading label="Carregando settings..." />;
  }

  return (
    <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <div className="space-y-6 rounded-[32px] border border-[var(--border)] bg-[linear-gradient(180deg,rgba(14,16,20,0.96),rgba(8,10,12,0.96))] p-6">
        <div>
          <p className="text-xs uppercase tracking-[0.32em] text-[var(--amber)]">Sessão Gemini</p>
          <h3 className="mt-3 font-display text-4xl uppercase tracking-[0.08em] text-[var(--text)]">
            {data?.authenticated ? 'Ativa' : 'Inativa'}
          </h3>
          <p className="mt-2 text-sm text-[var(--text2)]">
            A API key fica no backend via cookie de sessão httpOnly. O frontend não usa mais `localStorage`.
          </p>
        </div>

        <div className="space-y-4">
          <input
            type="password"
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
            placeholder="Cole sua GEMINI_API_KEY"
            className="w-full rounded-2xl border border-[var(--border2)] bg-[var(--bg3)] px-4 py-3 text-sm text-[var(--text)] outline-none focus:border-[var(--amber)]"
          />
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => void handleSave()}
              disabled={loginPending || !apiKey.trim()}
              className="rounded-full border border-[var(--amber)] bg-[var(--amber)]/10 px-4 py-2 text-sm text-[var(--amber)] transition hover:bg-[var(--amber)]/20 disabled:opacity-50"
            >
              {loginPending ? 'Salvando...' : data?.authenticated ? 'Substituir key' : 'Entrar'}
            </button>
            <button
              type="button"
              onClick={() => void handleLogout()}
              disabled={logoutPending || !data?.authenticated}
              className="rounded-full border border-[var(--border2)] px-4 py-2 text-sm text-[var(--text)] transition hover:border-[var(--red)] hover:text-[var(--red)] disabled:opacity-50"
            >
              {logoutPending ? 'Saindo...' : 'Logout'}
            </button>
          </div>
        </div>

        {feedback ? <Alert tone={feedback.tone} message={feedback.message} /> : null}
      </div>

      {/* Language selector */}
      <div className="space-y-4 rounded-[32px] border border-[var(--border)] bg-[linear-gradient(180deg,rgba(14,16,20,0.96),rgba(8,10,12,0.96))] p-6">
        <div>
          <p className="text-xs uppercase tracking-[0.32em] text-[var(--amber)]">Idioma do Conteúdo</p>
          <h3 className="mt-3 font-display text-4xl uppercase tracking-[0.08em] text-[var(--text)]">
            {language === 'pt' ? 'Português' : 'English'}
          </h3>
          <p className="mt-2 text-sm text-[var(--text2)]">
            Define o idioma dos roteiros, entonação e shorts gerados pelo Gemini.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            id="settings-lang-pt"
            type="button"
            onClick={() => setLanguage('pt')}
            className={`rounded-full border px-6 py-2 text-sm font-semibold tracking-wide transition ${
              language === 'pt'
                ? 'border-[var(--amber)] bg-[var(--amber)]/15 text-[var(--amber)]'
                : 'border-[var(--border2)] text-[var(--text2)] hover:border-[var(--amber)] hover:text-[var(--amber)]'
            }`}
          >
            🇧🇷 Português
          </button>
          <button
            id="settings-lang-en"
            type="button"
            onClick={() => setLanguage('en')}
            className={`rounded-full border px-6 py-2 text-sm font-semibold tracking-wide transition ${
              language === 'en'
                ? 'border-[var(--amber)] bg-[var(--amber)]/15 text-[var(--amber)]'
                : 'border-[var(--border2)] text-[var(--text2)] hover:border-[var(--amber)] hover:text-[var(--amber)]'
            }`}
          >
            🇺🇸 English
          </button>
        </div>
      </div>

      <div className="rounded-[32px] border border-[var(--border)] bg-[var(--bg2)] p-6">
        <p className="text-xs uppercase tracking-[0.32em] text-[var(--amber)]">Saúde do Backend</p>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg3)]/60 p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--text3)]">Database URL</p>
            <p className="mt-2 break-all text-sm text-[var(--text)]">{healthQuery.data?.database_url}</p>
          </div>
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg3)]/60 p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--text3)]">Top Risk</p>
            <p className="mt-2 text-sm text-[var(--text)]">{healthQuery.data?.cost_control.top_risk}</p>
          </div>
        </div>

        <div className="mt-4 space-y-3">
          {healthQuery.data?.storage.map((item) => (
            <div key={item.path} className="rounded-2xl border border-[var(--border)] bg-[var(--bg3)]/60 p-4 text-sm text-[var(--text2)]">
              <p className="text-[var(--text)]">{item.path}</p>
              <p className="mt-1">
                existe={String(item.exists)} / diretório={String(item.is_dir)} / gravável={String(item.writable)}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
