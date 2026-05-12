import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { generateShorts } from '@/api/media';
import { getErrorMessage } from '@/api/client';
import { Alert } from '@/components/common/Alert';
import { EmptyState } from '@/components/common/EmptyState';
import { ShortCard } from '@/components/shorts/ShortCard';
import { useAppStore } from '@/stores/appStore';
import type { ShortItem } from '@/types/media';

export function ShortsGenerator() {
  const selectedVoice = useAppStore((state) => state.selectedVoice);
  const [script, setScript] = useState('');
  const [count, setCount] = useState(3);
  const [duration, setDuration] = useState(60);
  const [shorts, setShorts] = useState<ShortItem[]>([]);
  const [feedback, setFeedback] = useState<{ tone: 'success' | 'error' | 'loading'; message: string } | null>(null);

  const mutation = useMutation({
    mutationFn: generateShorts,
    onSuccess: (data) => {
      setShorts(data.shorts);
      setFeedback({ tone: 'success', message: `${data.count} shorts gerados para ${data.duration_seconds}s.` });
    },
    onError: (error) => {
      setFeedback({ tone: 'error', message: getErrorMessage(error, 'Falha ao gerar shorts.') });
    },
  });

  return (
    <section className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[0.86fr_1.14fr]">
        <div className="space-y-5 rounded-[32px] border border-[var(--border)] bg-[linear-gradient(180deg,rgba(14,16,20,0.96),rgba(8,10,12,0.96))] p-6">
          <div>
            <p className="text-xs uppercase tracking-[0.32em] text-[var(--amber)]">Stage 5</p>
            <h3 className="mt-3 font-display text-5xl uppercase tracking-[0.08em] text-[var(--text)]">Shorts Generator</h3>
            <p className="mt-3 text-sm text-[var(--text2)]">
              Geração de 2 ou 3 shorts com `production_pack` completo: Flow prompt, 5 prompts Whisk, timeline de 62s e CTA final.
            </p>
          </div>

          <textarea
            value={script}
            onChange={(event) => setScript(event.target.value)}
            rows={14}
            placeholder="Cole aqui o roteiro longo de referência..."
            className="w-full rounded-[28px] border border-[var(--border2)] bg-[var(--bg3)] px-5 py-5 text-sm leading-7 text-[var(--text)] outline-none focus:border-[var(--amber)]"
          />

          <div className="grid gap-4 md:grid-cols-2">
            <select
              value={count}
              onChange={(event) => setCount(Number(event.target.value))}
              className="rounded-2xl border border-[var(--border2)] bg-[var(--bg3)] px-4 py-3 text-sm text-[var(--text)] outline-none focus:border-[var(--amber)]"
            >
              <option value={2}>2 shorts</option>
              <option value={3}>3 shorts</option>
            </select>
            <select
              value={duration}
              onChange={(event) => setDuration(Number(event.target.value))}
              className="rounded-2xl border border-[var(--border2)] bg-[var(--bg3)] px-4 py-3 text-sm text-[var(--text)] outline-none focus:border-[var(--amber)]"
            >
              <option value={45}>45 segundos</option>
              <option value={60}>60 segundos</option>
              <option value={65}>65 segundos</option>
            </select>
          </div>

          <button
            type="button"
            onClick={() => mutation.mutate({ script, count, duration_seconds: duration })}
            disabled={mutation.isPending || script.trim().length < 500}
            className="rounded-full border border-[var(--amber)] bg-[var(--amber)]/10 px-4 py-3 text-sm text-[var(--amber)] transition hover:bg-[var(--amber)]/20 disabled:opacity-50"
          >
            {mutation.isPending ? 'Gerando...' : 'Gerar Shorts'}
          </button>

          {feedback ? <Alert tone={feedback.tone} message={feedback.message} /> : null}
        </div>

        <div className="rounded-[32px] border border-[var(--border)] bg-[var(--bg2)] p-6">
          <p className="text-xs uppercase tracking-[0.32em] text-[var(--amber)]">Voz padrão</p>
          <p className="mt-3 font-display text-4xl uppercase tracking-[0.08em] text-[var(--text)]">{selectedVoice}</p>
          <p className="mt-3 text-sm text-[var(--text2)]">
            Cada card permite trocar a voz antes de gerar áudio ou montar o short com assets do template.
          </p>
        </div>
      </div>

      {shorts.length ? (
        <div className="space-y-6">
          {shorts.map((item) => (
            <ShortCard key={item.id} item={item} defaultVoice={selectedVoice} />
          ))}
        </div>
      ) : (
        <EmptyState title="Nenhum short" description="O backend começa a retornar cards assim que receber um roteiro longo com pelo menos 500 caracteres." />
      )}
    </section>
  );
}
