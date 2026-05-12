import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { enhanceText, generateScript } from '@/api/media';
import { getErrorMessage } from '@/api/client';
import { Alert } from '@/components/common/Alert';
import { CopyButton } from '@/components/common/CopyButton';
import { EmptyState } from '@/components/common/EmptyState';
import { useAppStore } from '@/stores/appStore';

export function ScriptStudio() {
  const navigate = useNavigate();
  const setScriptBundle = useAppStore((state) => state.setScriptBundle);
  const imagePrompts = useAppStore((state) => state.imagePrompts);
  const scriptDraft = useAppStore((state) => state.scriptDraft);
  const setTtsText = useAppStore((state) => state.setTtsText);

  const [url, setUrl] = useState('');
  const [scriptText, setScriptText] = useState(scriptDraft);
  const [feedback, setFeedback] = useState<{ tone: 'success' | 'error' | 'loading'; message: string } | null>(null);

  const generateMutation = useMutation({
    mutationFn: generateScript,
    onSuccess: (data) => {
      setScriptBundle({ script: data.script, prompts: data.image_prompts });
      setScriptText(data.script);
      setFeedback({ tone: 'success', message: `Roteiro gerado com ${data.source_chars} caracteres de origem.` });
    },
    onError: (error) => {
      setFeedback({ tone: 'error', message: getErrorMessage(error, 'Falha ao gerar roteiro.') });
    },
  });

  const enhanceMutation = useMutation({
    mutationFn: enhanceText,
    onSuccess: (data) => {
      setScriptText(data.enhanced_text);
      setScriptBundle({ script: data.enhanced_text, prompts: imagePrompts });
      setFeedback({ tone: 'success', message: 'Entonação aplicada ao roteiro.' });
    },
    onError: (error) => {
      setFeedback({ tone: 'error', message: getErrorMessage(error, 'Falha ao melhorar roteiro.') });
    },
  });

  function handleAdvance() {
    setTtsText(scriptText);
    navigate('/tts');
  }

  return (
    <section className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
      <div className="space-y-6 rounded-[32px] border border-[var(--border)] bg-[linear-gradient(180deg,rgba(14,16,20,0.96),rgba(8,10,12,0.96))] p-6">
        <div>
          <p className="text-xs uppercase tracking-[0.32em] text-[var(--amber)]">Stage 1</p>
          <h3 className="mt-3 font-display text-5xl uppercase tracking-[0.08em] text-[var(--text)]">Script Studio</h3>
          <p className="mt-3 text-sm text-[var(--text2)]">
            Cole uma URL, gere o roteiro principal e refine a entonação antes de seguir para o TTS.
          </p>
        </div>

        <div className="space-y-4">
          <input
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            placeholder="https://..."
            className="w-full rounded-2xl border border-[var(--border2)] bg-[var(--bg3)] px-4 py-3 text-sm text-[var(--text)] outline-none focus:border-[var(--amber)]"
          />
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => generateMutation.mutate({ url })}
              disabled={generateMutation.isPending || !url.trim()}
              className="rounded-full border border-[var(--amber)] bg-[var(--amber)]/10 px-4 py-2 text-sm text-[var(--amber)] transition hover:bg-[var(--amber)]/20 disabled:opacity-50"
            >
              {generateMutation.isPending ? 'Gerando...' : 'Gerar Roteiro'}
            </button>
            <button
              type="button"
              onClick={() => enhanceMutation.mutate({ text: scriptText })}
              disabled={enhanceMutation.isPending || !scriptText.trim()}
              className="rounded-full border border-[var(--border2)] px-4 py-2 text-sm text-[var(--text)] transition hover:border-[var(--blue)] hover:text-[var(--blue)] disabled:opacity-50"
            >
              {enhanceMutation.isPending ? 'Aplicando...' : 'Entonação Inteligente'}
            </button>
            <button
              type="button"
              onClick={handleAdvance}
              disabled={!scriptText.trim()}
              className="rounded-full border border-[var(--green)] bg-[var(--green)]/10 px-4 py-2 text-sm text-[var(--green)] transition hover:bg-[var(--green)]/20 disabled:opacity-50"
            >
              Avançar para TTS
            </button>
          </div>
        </div>

        {feedback ? <Alert tone={feedback.tone} message={feedback.message} /> : null}

        <textarea
          value={scriptText}
          onChange={(event) => setScriptText(event.target.value)}
          rows={18}
          className="w-full rounded-[28px] border border-[var(--border2)] bg-[var(--bg3)] px-5 py-5 text-sm leading-7 text-[var(--text)] outline-none focus:border-[var(--amber)]"
        />
      </div>

      <div className="rounded-[32px] border border-[var(--border)] bg-[var(--bg2)] p-6">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.32em] text-[var(--amber)]">Image Prompts</p>
            <p className="mt-2 text-sm text-[var(--text2)]">Prompts extraídos do backend para storyboard e geração visual.</p>
          </div>
          {imagePrompts.length ? <CopyButton text={imagePrompts.map((item) => item.prompt).join('\n\n')} label="Copiar todos" /> : null}
        </div>

        <div className="mt-5">
          {imagePrompts.length ? (
            <div className="grid gap-3">
              {imagePrompts.map((prompt, index) => (
                <div key={`${prompt.timestamp}_${index}`} className="rounded-2xl border border-[var(--border)] bg-[var(--bg3)]/60 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-[var(--text)]">
                        {prompt.timestamp || '00:00'} {prompt.cue ? `· ${prompt.cue}` : ''}
                      </p>
                      <p className="mt-2 text-sm leading-6 text-[var(--text2)]">{prompt.prompt}</p>
                    </div>
                    <CopyButton text={prompt.prompt} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="Sem prompts" description="Gere um roteiro a partir de uma URL para popular o painel de prompts visuais." />
          )}
        </div>
      </div>
    </section>
  );
}
