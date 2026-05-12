import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { enhanceText } from '@/api/media';
import { getErrorMessage } from '@/api/client';
import { Alert } from '@/components/common/Alert';
import { EmptyState } from '@/components/common/EmptyState';
import { AudioPlayer } from '@/components/media/AudioPlayer';
import { ProgressBar } from '@/components/media/ProgressBar';
import { useSSE } from '@/hooks/useSSE';
import { VOICES } from '@/lib/voices';
import { useAppStore } from '@/stores/appStore';

export function TTSStudio() {
  const navigate = useNavigate();
  const selectedVoice = useAppStore((state) => state.selectedVoice);
  const setSelectedVoice = useAppStore((state) => state.setSelectedVoice);
  const ttsText = useAppStore((state) => state.ttsText);
  const setTtsText = useAppStore((state) => state.setTtsText);
  const setGeneratedAudio = useAppStore((state) => state.setGeneratedAudio);

  const tts = useSSE();
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [useEnhance, setUseEnhance] = useState(true);
  const [feedback, setFeedback] = useState<{ tone: 'success' | 'error' | 'loading'; message: string } | null>(null);

  useEffect(() => {
    if (!audioFile) {
      setAudioUrl(null);
      return;
    }
    const nextUrl = URL.createObjectURL(audioFile);
    setAudioUrl(nextUrl);
    return () => URL.revokeObjectURL(nextUrl);
  }, [audioFile]);

  async function handleGenerate() {
    try {
      let text = ttsText;
      if (useEnhance) {
        setFeedback({ tone: 'loading', message: 'Aplicando entonação inteligente...' });
        const enhanced = await enhanceText({ text });
        text = enhanced.enhanced_text;
        setTtsText(text);
      }

      setFeedback({ tone: 'loading', message: 'Conectando ao stream TTS...' });
      const file = await tts.runStream({
        text,
        voice: selectedVoice,
        session_id: tts.sessionId,
      });
      setAudioFile(file);
      setGeneratedAudio(file);
      setFeedback({ tone: 'success', message: 'Áudio gerado com sucesso.' });
    } catch (error) {
      setFeedback({ tone: 'error', message: getErrorMessage(error, 'Falha ao gerar áudio.') });
    }
  }

  return (
    <section className="grid gap-6 xl:grid-cols-[0.86fr_1.14fr]">
      <div className="space-y-6 rounded-[32px] border border-[var(--border)] bg-[linear-gradient(180deg,rgba(14,16,20,0.96),rgba(8,10,12,0.96))] p-6">
        <div>
          <p className="text-xs uppercase tracking-[0.32em] text-[var(--amber)]">Stage 2</p>
          <h3 className="mt-3 font-display text-5xl uppercase tracking-[0.08em] text-[var(--text)]">TTS Studio</h3>
          <p className="mt-3 text-sm text-[var(--text2)]">Streaming via SSE com cache de chunks, controle de voz e download direto do WAV.</p>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          {VOICES.map((voice) => (
            <button
              key={voice.id}
              type="button"
              onClick={() => setSelectedVoice(voice.id)}
              className={`rounded-[24px] border px-4 py-4 text-left transition ${
                selectedVoice === voice.id
                  ? 'border-[var(--amber)] bg-[var(--amber)]/10'
                  : 'border-[var(--border2)] bg-[var(--bg2)] hover:border-[var(--amber)]/50'
              }`}
            >
              <p className="font-display text-2xl uppercase tracking-[0.08em] text-[var(--text)]">{voice.label}</p>
              <p className="mt-2 text-sm text-[var(--text2)]">{voice.desc}</p>
            </button>
          ))}
        </div>

        <label className="flex items-center gap-3 rounded-2xl border border-[var(--border)] bg-[var(--bg2)] px-4 py-3 text-sm text-[var(--text2)]">
          <input type="checkbox" checked={useEnhance} onChange={(event) => setUseEnhance(event.target.checked)} />
          Entonação inteligente antes do TTS
        </label>

        <button
          type="button"
          onClick={() => void handleGenerate()}
          disabled={!ttsText.trim() || tts.isStreaming}
          className="rounded-full border border-[var(--amber)] bg-[var(--amber)]/10 px-4 py-3 text-sm text-[var(--amber)] transition hover:bg-[var(--amber)]/20 disabled:opacity-50"
        >
          {tts.isStreaming ? 'Gerando...' : 'Gerar Áudio'}
        </button>

        <button
          type="button"
          onClick={() => navigate('/assembly')}
          disabled={!audioFile}
          className="rounded-full border border-[var(--green)] bg-[var(--green)]/10 px-4 py-3 text-sm text-[var(--green)] transition hover:bg-[var(--green)]/20 disabled:opacity-50"
        >
          Avançar para Assembly
        </button>
      </div>

      <div className="space-y-5 rounded-[32px] border border-[var(--border)] bg-[var(--bg2)] p-6">
        <textarea
          value={ttsText}
          onChange={(event) => setTtsText(event.target.value)}
          rows={16}
          className="w-full rounded-[28px] border border-[var(--border2)] bg-[var(--bg3)] px-5 py-5 text-sm leading-7 text-[var(--text)] outline-none focus:border-[var(--amber)]"
          placeholder="Seu roteiro aparecerá aqui."
        />

        {feedback ? <Alert tone={feedback.tone} message={feedback.message} /> : null}

        {tts.progress.total > 0 ? (
          <ProgressBar
            value={(tts.progress.current / Math.max(tts.progress.total, 1)) * 100}
            label={tts.progress.label}
            rightLabel={`${tts.progress.current}/${tts.progress.total}`}
          />
        ) : null}

        <div className="rounded-[24px] border border-[var(--border)] bg-[var(--bg3)]/50 p-4">
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--text3)]">Log do Stream</p>
          {tts.logs.length ? (
            <div className="mt-3 max-h-[320px] space-y-2 overflow-auto pr-2 font-mono text-xs text-[var(--text2)]">
              {tts.logs.map((log) => (
                <div key={log.id} className="rounded-xl border border-[var(--border)] bg-[var(--bg2)] px-3 py-2">
                  {log.message}
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-3">
              <EmptyState title="Sem stream" description="Os eventos SSE de progresso, waiting, skipped e done aparecem aqui." />
            </div>
          )}
        </div>

        {audioUrl && audioFile ? <AudioPlayer url={audioUrl} fileName={audioFile.name} /> : null}
      </div>
    </section>
  );
}
