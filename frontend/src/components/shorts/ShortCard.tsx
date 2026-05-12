import { useEffect, useState } from 'react';
import { createGeneratedVideoJob } from '@/api/media';
import { getErrorMessage } from '@/api/client';
import { Alert } from '@/components/common/Alert';
import { CopyButton } from '@/components/common/CopyButton';
import { AudioPlayer } from '@/components/media/AudioPlayer';
import { FileUpload } from '@/components/media/FileUpload';
import { ProgressBar } from '@/components/media/ProgressBar';
import { VideoPlayer } from '@/components/media/VideoPlayer';
import { useJobPolling } from '@/hooks/useJobPolling';
import { useSSE } from '@/hooks/useSSE';
import { VOICES } from '@/lib/voices';
import type { ShortItem } from '@/types/media';
import { ProductionPackPanel } from './ProductionPackPanel';

interface ShortCardProps {
  item: ShortItem;
  defaultVoice: string;
}

export function ShortCard({ item, defaultVoice }: ShortCardProps) {
  const [title, setTitle] = useState(item.title);
  const [script, setScript] = useState(item.script);
  const [voice, setVoice] = useState(defaultVoice);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [assetFiles, setAssetFiles] = useState<File[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ tone: 'info' | 'success' | 'error' | 'loading'; message: string } | null>(
    null,
  );

  const tts = useSSE();
  const jobQuery = useJobPolling(jobId);

  useEffect(() => {
    if (!audioFile) {
      setAudioUrl(null);
      return;
    }
    const nextUrl = URL.createObjectURL(audioFile);
    setAudioUrl(nextUrl);
    return () => URL.revokeObjectURL(nextUrl);
  }, [audioFile]);

  useEffect(() => {
    async function loadVideo() {
      if (jobQuery.data?.status !== 'done' || !jobQuery.data.download_url) {
        return;
      }
      const response = await fetch(jobQuery.data.download_url, { credentials: 'include' });
      const blob = await response.blob();
      const nextUrl = URL.createObjectURL(blob);
      setVideoUrl((current) => {
        if (current) {
          URL.revokeObjectURL(current);
        }
        return nextUrl;
      });
      setFeedback({ tone: 'success', message: 'Short montado com sucesso.' });
    }

    void loadVideo();
  }, [jobQuery.data]);

  async function handleGenerateAudio() {
    try {
      setFeedback({ tone: 'loading', message: 'Gerando narração por SSE...' });
      const file = await tts.runStream({ text: script, voice });
      setAudioFile(file);
      setFeedback({ tone: 'success', message: 'Áudio do short gerado.' });
    } catch (error) {
      setFeedback({ tone: 'error', message: getErrorMessage(error, 'Falha ao gerar áudio.') });
    }
  }

  async function handleGenerateVideo() {
    if (!item.production_pack) {
      setFeedback({ tone: 'error', message: 'Este short não possui production pack válido.' });
      return;
    }
    if (assetFiles.length !== 6) {
      setFeedback({ tone: 'error', message: 'Envie exatamente 6 assets na ordem do template: 1 vídeo + 5 imagens.' });
      return;
    }

    try {
      setFeedback({ tone: 'loading', message: 'Enviando assets e iniciando montagem do short...' });
      const manifest = item.production_pack.timeline_segments.map((segment, index) => ({
        type: 'upload',
        filename: assetFiles[index]?.name,
        slot_index: segment.slot_index,
        asset_kind: segment.asset_kind,
        duration_seconds: segment.duration_seconds,
        motion_preset: segment.motion_preset,
        overlay_text: segment.overlay_text,
      }));

      const formData = new FormData();
      formData.append('script', script);
      formData.append('voice', voice);
      formData.append('format', 'short');
      formData.append('manifest', JSON.stringify(manifest));
      assetFiles.forEach((file) => formData.append('images', file, file.name));

      const data = await createGeneratedVideoJob(formData);
      setJobId(data.job_id);
      setFeedback({ tone: 'loading', message: `Job ${data.job_id.slice(0, 8)} iniciado.` });
    } catch (error) {
      setFeedback({ tone: 'error', message: getErrorMessage(error, 'Falha ao montar short.') });
    }
  }

  return (
    <article className="space-y-5 rounded-[32px] border border-[var(--border)] bg-[linear-gradient(180deg,rgba(14,16,20,0.96),rgba(8,10,12,0.96))] p-6">
      <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-4">
          <div>
            <p className="text-xs uppercase tracking-[0.32em] text-[var(--amber)]">{item.id}</p>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              className="mt-3 w-full rounded-2xl border border-[var(--border2)] bg-[var(--bg3)] px-4 py-3 font-display text-3xl uppercase tracking-[0.08em] text-[var(--text)] outline-none focus:border-[var(--amber)]"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <span className="rounded-full border border-[var(--amber)] bg-[var(--amber)]/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-[var(--amber)]">
              Hook
            </span>
            <span className="rounded-full border border-[var(--border2)] bg-[var(--bg3)] px-3 py-1 text-xs text-[var(--text)]">
              {item.hook}
            </span>
            <span className="rounded-full border border-[var(--blue)] bg-[var(--blue)]/10 px-3 py-1 text-xs uppercase tracking-[0.24em] text-[var(--blue)]">
              CTA
            </span>
            <span className="rounded-full border border-[var(--border2)] bg-[var(--bg3)] px-3 py-1 text-xs text-[var(--text)]">
              {item.cta}
            </span>
          </div>

          <textarea
            value={script}
            onChange={(event) => setScript(event.target.value)}
            rows={10}
            className="w-full rounded-[24px] border border-[var(--border2)] bg-[var(--bg3)] px-4 py-4 text-sm leading-6 text-[var(--text)] outline-none focus:border-[var(--amber)]"
          />

          <div className="flex flex-wrap gap-2">
            {item.broll_keywords.map((keyword) => (
              <span key={keyword} className="rounded-full border border-[var(--border2)] px-3 py-1 text-xs uppercase tracking-[0.18em] text-[var(--text2)]">
                {keyword}
              </span>
            ))}
          </div>

          <div className="rounded-[24px] border border-[var(--border)] bg-[var(--bg2)] p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <p className="text-xs uppercase tracking-[0.24em] text-[var(--text3)]">Image Prompts</p>
              <CopyButton text={item.image_prompts.map((prompt) => prompt.prompt).join('\n\n')} label="Copiar tudo" />
            </div>
            <div className="grid gap-3">
              {item.image_prompts.map((prompt, index) => (
                <div key={`${prompt.cue}_${index}`} className="rounded-2xl border border-[var(--border)] bg-[var(--bg3)]/60 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-[var(--text)]">{prompt.cue || `Prompt ${index + 1}`}</p>
                      <p className="mt-2 text-sm text-[var(--text2)]">{prompt.prompt}</p>
                    </div>
                    <CopyButton text={prompt.prompt} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-[24px] border border-[var(--border)] bg-[var(--bg2)] p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--text3)]">Voz do short</p>
            <select
              value={voice}
              onChange={(event) => setVoice(event.target.value)}
              className="mt-3 w-full rounded-2xl border border-[var(--border2)] bg-[var(--bg3)] px-4 py-3 text-sm text-[var(--text)] outline-none focus:border-[var(--amber)]"
            >
              {VOICES.map((candidate) => (
                <option key={candidate.id} value={candidate.id}>
                  {candidate.label}
                </option>
              ))}
            </select>
          </div>

          <FileUpload
            onFiles={(files) => setAssetFiles(files.slice(0, 6))}
            accept="video/*,image/*"
            multiple
            title="Assets do template"
            description="Envie 6 arquivos na ordem da timeline do production pack. O slot 1 precisa ser vídeo; os demais, imagens."
          />

          <div className="rounded-[24px] border border-[var(--border)] bg-[var(--bg2)] p-4 text-sm text-[var(--text2)]">
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--text3)]">Arquivos enviados</p>
            <ol className="mt-3 space-y-2">
              {assetFiles.map((file, index) => (
                <li key={`${file.name}_${index}`}>{index + 1}. {file.name}</li>
              ))}
            </ol>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => void handleGenerateAudio()}
              disabled={tts.isStreaming}
              className="rounded-full border border-[var(--amber)] bg-[var(--amber)]/10 px-4 py-2 text-sm text-[var(--amber)] transition hover:bg-[var(--amber)]/20 disabled:opacity-50"
            >
              {tts.isStreaming ? 'Gerando áudio...' : 'Gerar Áudio'}
            </button>
            <button
              type="button"
              onClick={() => void handleGenerateVideo()}
              disabled={jobQuery.isFetching}
              className="rounded-full border border-[var(--blue)] bg-[var(--blue)]/10 px-4 py-2 text-sm text-[var(--blue)] transition hover:bg-[var(--blue)]/20 disabled:opacity-50"
            >
              {jobQuery.isFetching ? 'Montando...' : 'Montar Short'}
            </button>
          </div>

          {tts.progress.total > 0 ? (
            <ProgressBar
              value={(tts.progress.current / Math.max(tts.progress.total, 1)) * 100}
              label={tts.progress.label}
              rightLabel={`${tts.progress.current}/${tts.progress.total}`}
            />
          ) : null}

          {jobQuery.data ? (
            <ProgressBar
              value={jobQuery.data.progress * 100}
              label={jobQuery.data.status === 'done' ? 'Short finalizado' : 'Montagem em andamento'}
            />
          ) : null}

          {feedback ? <Alert tone={feedback.tone} message={feedback.message} /> : null}

          {audioUrl && audioFile ? <AudioPlayer url={audioUrl} fileName={audioFile.name} /> : null}
          {videoUrl && jobQuery.data?.download_url ? <VideoPlayer url={videoUrl} downloadUrl={jobQuery.data.download_url} title="Preview do Short" /> : null}
        </div>
      </div>

      {item.production_pack ? <ProductionPackPanel pack={item.production_pack} /> : null}
    </article>
  );
}
