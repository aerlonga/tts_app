import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { createAssembleJob } from '@/api/media';
import { getErrorMessage } from '@/api/client';
import { Alert } from '@/components/common/Alert';
import { EmptyState } from '@/components/common/EmptyState';
import { FileUpload } from '@/components/media/FileUpload';
import { ProgressBar } from '@/components/media/ProgressBar';
import { VideoPlayer } from '@/components/media/VideoPlayer';
import { useJobPolling } from '@/hooks/useJobPolling';
import { useAppStore } from '@/stores/appStore';

export function VideoAssembly() {
  const generatedAudio = useAppStore((state) => state.generatedAudio);
  const assemblyAssets = useAppStore((state) => state.assemblyAssets);
  const addAssemblyUploads = useAppStore((state) => state.addAssemblyUploads);
  const moveAssemblyAsset = useAppStore((state) => state.moveAssemblyAsset);
  const removeAssemblyAsset = useAppStore((state) => state.removeAssemblyAsset);

  const [audioFile, setAudioFile] = useState<File | null>(generatedAudio);
  const [jobId, setJobId] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ tone: 'success' | 'error' | 'loading'; message: string } | null>(null);
  const [format, setFormat] = useState<'long' | 'short'>('long');
  const [activeTab, setActiveTab] = useState<'media' | 'broll'>('media');

  const jobQuery = useJobPolling(jobId);

  useEffect(() => {
    if (generatedAudio) {
      setAudioFile(generatedAudio);
    }
  }, [generatedAudio]);

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
      setFeedback({ tone: 'success', message: 'Vídeo montado com sucesso.' });
    }

    void loadVideo();
  }, [jobQuery.data]);

  async function handleAssemble() {
    if (!audioFile) {
      setFeedback({ tone: 'error', message: 'Envie ou gere um áudio WAV antes da montagem.' });
      return;
    }
    if (!assemblyAssets.length) {
      setFeedback({ tone: 'error', message: 'Adicione pelo menos um asset ao assembly.' });
      return;
    }

    try {
      setFeedback({ tone: 'loading', message: 'Enviando arquivos e iniciando montagem...' });
      const formData = new FormData();
      formData.append('audio', audioFile, audioFile.name);

      const manifest = assemblyAssets.map((asset) =>
        asset.source === 'upload'
          ? {
              type: 'upload',
              filename: asset.filename,
            }
          : {
              type: 'server',
              filename: asset.filename,
              path: asset.path,
            },
      );

      assemblyAssets.forEach((asset) => {
        if (asset.source === 'upload' && asset.file) {
          formData.append('images', asset.file, asset.file.name);
        }
      });

      formData.append('manifest', JSON.stringify(manifest));
      formData.append('format', format);

      const data = await createAssembleJob(formData);
      setJobId(data.job_id);
      setFeedback({ tone: 'loading', message: `Job ${data.job_id.slice(0, 8)} iniciado.` });
    } catch (error) {
      setFeedback({ tone: 'error', message: getErrorMessage(error, 'Falha ao montar vídeo.') });
    }
  }

  return (
    <section className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[0.84fr_1.16fr]">
        <div className="space-y-5 rounded-[32px] border border-[var(--border)] bg-[linear-gradient(180deg,rgba(14,16,20,0.96),rgba(8,10,12,0.96))] p-6">
          <div>
            <p className="text-xs uppercase tracking-[0.32em] text-[var(--amber)]">Stage 4</p>
            <h3 className="mt-3 font-display text-5xl uppercase tracking-[0.08em] text-[var(--text)]">Video Assembly</h3>
            <p className="mt-3 text-sm text-[var(--text2)]">Upload de assets, manifesto ordenado e polling em `/media/assemble/status/{'{id}'}`.</p>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setActiveTab('media')}
              className={`rounded-full px-4 py-2 text-sm ${activeTab === 'media' ? 'bg-[var(--amber)]/10 text-[var(--amber)] border border-[var(--amber)]' : 'border border-[var(--border2)] text-[var(--text2)]'}`}
            >
              Mídias
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('broll')}
              className={`rounded-full px-4 py-2 text-sm ${activeTab === 'broll' ? 'bg-[var(--amber)]/10 text-[var(--amber)] border border-[var(--amber)]' : 'border border-[var(--border2)] text-[var(--text2)]'}`}
            >
              B-Roll
            </button>
          </div>

          {activeTab === 'media' ? (
            <FileUpload
              onFiles={addAssemblyUploads}
              accept="image/*,video/*"
              multiple
              title="Upload de assets"
              description="Arraste imagens e vídeos locais. A ordem final pode ser ajustada na lista ao lado."
            />
          ) : (
            <div className="rounded-[28px] border border-[var(--border)] bg-[var(--bg2)] p-5 text-sm text-[var(--text2)]">
              <p>Os clips baixados em B-Roll Search entram automaticamente nesta fila.</p>
              <Link to="/broll" className="mt-4 inline-flex rounded-full border border-[var(--blue)] bg-[var(--blue)]/10 px-4 py-2 text-[var(--blue)]">
                Abrir B-Roll Search
              </Link>
            </div>
          )}

          <div className="rounded-[24px] border border-[var(--border)] bg-[var(--bg2)] p-4">
            <p className="text-xs uppercase tracking-[0.24em] text-[var(--text3)]">Áudio</p>
            {audioFile ? (
              <p className="mt-3 text-sm text-[var(--text)]">{audioFile.name}</p>
            ) : (
              <p className="mt-3 text-sm text-[var(--text2)]">Nenhum áudio em memória.</p>
            )}
            <label className="mt-4 inline-flex cursor-pointer rounded-full border border-[var(--border2)] px-4 py-2 text-sm text-[var(--text)]">
              Subir WAV manualmente
              <input
                type="file"
                accept="audio/wav"
                className="hidden"
                onChange={(event) => {
                  const nextFile = event.target.files?.[0];
                  if (nextFile) {
                    setAudioFile(nextFile);
                  }
                }}
              />
            </label>
          </div>

          <select
            value={format}
            onChange={(event) => setFormat(event.target.value as 'long' | 'short')}
            className="w-full rounded-2xl border border-[var(--border2)] bg-[var(--bg3)] px-4 py-3 text-sm text-[var(--text)] outline-none focus:border-[var(--amber)]"
          >
            <option value="long">Formato Longo 16:9</option>
            <option value="short">Formato Short 9:16</option>
          </select>

          <button
            type="button"
            onClick={() => void handleAssemble()}
            className="rounded-full border border-[var(--amber)] bg-[var(--amber)]/10 px-4 py-3 text-sm text-[var(--amber)] transition hover:bg-[var(--amber)]/20"
          >
            Montar Vídeo
          </button>

          {feedback ? <Alert tone={feedback.tone} message={feedback.message} /> : null}

          {jobQuery.data ? (
            <ProgressBar
              value={jobQuery.data.progress * 100}
              label={jobQuery.data.status === 'done' ? 'Montagem concluída' : 'Montagem em andamento'}
            />
          ) : null}
        </div>

        <div className="space-y-5 rounded-[32px] border border-[var(--border)] bg-[var(--bg2)] p-6">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.32em] text-[var(--amber)]">Fila de Assets</p>
              <p className="mt-2 text-sm text-[var(--text2)]">Uploads locais e B-Rolls baixados compartilham a mesma ordem de render.</p>
            </div>
          </div>

          {assemblyAssets.length ? (
            <div className="space-y-3">
              {assemblyAssets.map((asset, index) => (
                <div key={asset.id} className="rounded-2xl border border-[var(--border)] bg-[var(--bg3)]/60 p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm text-[var(--text)]">{index + 1}. {asset.filename}</p>
                      <p className="mt-1 text-xs uppercase tracking-[0.2em] text-[var(--text3)]">{asset.source}</p>
                    </div>
                    <div className="flex gap-2">
                      <button type="button" onClick={() => moveAssemblyAsset(index, -1)} className="rounded-full border border-[var(--border2)] px-3 py-1 text-xs text-[var(--text2)]">↑</button>
                      <button type="button" onClick={() => moveAssemblyAsset(index, 1)} className="rounded-full border border-[var(--border2)] px-3 py-1 text-xs text-[var(--text2)]">↓</button>
                      <button type="button" onClick={() => removeAssemblyAsset(asset.id)} className="rounded-full border border-[var(--border2)] px-3 py-1 text-xs text-[var(--red)]">Remover</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="Sem assets" description="Faça upload local ou baixe clips de B-Roll para compor a linha do tempo." />
          )}

          {videoUrl && jobQuery.data?.download_url ? <VideoPlayer url={videoUrl} downloadUrl={jobQuery.data.download_url} title="Vídeo Final" /> : null}
        </div>
      </div>
    </section>
  );
}
