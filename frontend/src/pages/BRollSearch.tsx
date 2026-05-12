import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { downloadBroll, searchBroll } from '@/api/broll';
import { getErrorMessage } from '@/api/client';
import { Alert } from '@/components/common/Alert';
import { EmptyState } from '@/components/common/EmptyState';
import { AssetGrid } from '@/components/media/AssetGrid';
import { useAppStore } from '@/stores/appStore';
import { splitKeywords } from '@/lib/utils';
import type { BrollClip } from '@/types/media';

export function BRollSearch() {
  const addServerAsset = useAppStore((state) => state.addServerAsset);
  const assemblyAssets = useAppStore((state) => state.assemblyAssets);

  const [keywordInput, setKeywordInput] = useState('');
  const [collection, setCollection] = useState('prelinger');
  const [clips, setClips] = useState<BrollClip[]>([]);
  const [previewClip, setPreviewClip] = useState<BrollClip | null>(null);
  const [feedback, setFeedback] = useState<{ tone: 'success' | 'error' | 'loading'; message: string } | null>(null);
  const [busyIdentifier, setBusyIdentifier] = useState<string | null>(null);

  const searchMutation = useMutation({
    mutationFn: searchBroll,
    onSuccess: (data) => {
      setClips(data.clips);
      setFeedback({ tone: 'success', message: `${data.clips.length} resultados encontrados.` });
    },
    onError: (error) => {
      setFeedback({ tone: 'error', message: getErrorMessage(error, 'Falha ao buscar B-Roll.') });
    },
  });

  async function handleDownload(clip: BrollClip) {
    try {
      setBusyIdentifier(clip.identifier);
      setFeedback({ tone: 'loading', message: `Baixando ${clip.title || clip.identifier}...` });
      const data = await downloadBroll({ url: clip.download_url });
      addServerAsset({
        filename: data.filename,
        path: data.local_path,
      });
      setFeedback({ tone: 'success', message: `${data.filename} baixado e adicionado ao assembly.` });
    } catch (error) {
      setFeedback({ tone: 'error', message: getErrorMessage(error, 'Falha ao baixar asset.') });
    } finally {
      setBusyIdentifier(null);
    }
  }

  return (
    <section className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-5 rounded-[32px] border border-[var(--border)] bg-[linear-gradient(180deg,rgba(14,16,20,0.96),rgba(8,10,12,0.96))] p-6">
          <div>
            <p className="text-xs uppercase tracking-[0.32em] text-[var(--amber)]">Stage 3</p>
            <h3 className="mt-3 font-display text-5xl uppercase tracking-[0.08em] text-[var(--text)]">B-Roll Search</h3>
            <p className="mt-3 text-sm text-[var(--text2)]">
              Busca em `/broll/search` com download server-side em `/broll/download` para reaproveitar no assembly.
            </p>
          </div>

          <textarea
            value={keywordInput}
            onChange={(event) => setKeywordInput(event.target.value)}
            rows={4}
            placeholder="war archive, bunker, declassified files"
            className="w-full rounded-[24px] border border-[var(--border2)] bg-[var(--bg3)] px-4 py-4 text-sm text-[var(--text)] outline-none focus:border-[var(--amber)]"
          />

          <select
            value={collection}
            onChange={(event) => setCollection(event.target.value)}
            className="w-full rounded-2xl border border-[var(--border2)] bg-[var(--bg3)] px-4 py-3 text-sm text-[var(--text)] outline-none focus:border-[var(--amber)]"
          >
            <option value="prelinger">Prelinger</option>
            <option value="opensource_movies">Open Source Movies</option>
          </select>

          <button
            type="button"
            onClick={() => searchMutation.mutate({ keywords: splitKeywords(keywordInput), collection })}
            disabled={searchMutation.isPending || !splitKeywords(keywordInput).length}
            className="rounded-full border border-[var(--amber)] bg-[var(--amber)]/10 px-4 py-3 text-sm text-[var(--amber)] transition hover:bg-[var(--amber)]/20 disabled:opacity-50"
          >
            {searchMutation.isPending ? 'Buscando...' : 'Pesquisar'}
          </button>

          {feedback ? <Alert tone={feedback.tone} message={feedback.message} /> : null}
        </div>

        <div className="rounded-[32px] border border-[var(--border)] bg-[var(--bg2)] p-6">
          <p className="text-xs uppercase tracking-[0.32em] text-[var(--amber)]">Selecionados para Assembly</p>
          {assemblyAssets.filter((asset) => asset.source === 'server').length ? (
            <div className="mt-4 space-y-3">
              {assemblyAssets
                .filter((asset) => asset.source === 'server')
                .map((asset) => (
                  <div key={asset.id} className="rounded-2xl border border-[var(--border)] bg-[var(--bg3)]/60 px-4 py-3 text-sm text-[var(--text2)]">
                    {asset.filename}
                  </div>
                ))}
            </div>
          ) : (
            <div className="mt-4">
              <EmptyState title="Nenhum B-Roll" description="Baixe um resultado para adicioná-lo automaticamente à lista do Video Assembly." />
            </div>
          )}
        </div>
      </div>

      {clips.length ? (
        <AssetGrid clips={clips} onPreview={setPreviewClip} onDownload={(clip) => void handleDownload(clip)} busyIdentifier={busyIdentifier} />
      ) : (
        <EmptyState title="Sem resultados" description="Use palavras-chave separadas por vírgula para encontrar assets relevantes." />
      )}

      {previewClip ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" role="presentation" onClick={() => setPreviewClip(null)}>
          <div className="w-full max-w-4xl rounded-[28px] border border-[var(--border2)] bg-[var(--bg2)] p-5" onClick={(event) => event.stopPropagation()}>
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-[var(--amber)]">Preview</p>
                <h4 className="mt-2 text-xl font-semibold text-[var(--text)]">{previewClip.title || previewClip.identifier}</h4>
              </div>
              <button type="button" onClick={() => setPreviewClip(null)} className="rounded-full border border-[var(--border2)] px-3 py-2 text-xs text-[var(--text2)]">
                Fechar
              </button>
            </div>
            <iframe title={previewClip.identifier} src={previewClip.preview_url} className="mt-4 h-[420px] w-full rounded-2xl border border-[var(--border)] bg-black" />
          </div>
        </div>
      ) : null}
    </section>
  );
}
