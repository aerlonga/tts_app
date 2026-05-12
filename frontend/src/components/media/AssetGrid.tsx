import type { BrollClip } from '@/types/media';

interface AssetGridProps {
  clips: BrollClip[];
  onPreview: (clip: BrollClip) => void;
  onDownload: (clip: BrollClip) => void;
  busyIdentifier?: string | null;
}

export function AssetGrid({ clips, onPreview, onDownload, busyIdentifier }: AssetGridProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {clips.map((clip) => (
        <article key={clip.identifier} className="rounded-[24px] border border-[var(--border)] bg-[var(--bg2)] p-4">
          <img
            src={clip.thumb || 'https://placehold.co/640x360/141720/D4D8E2?text=No+Thumb'}
            alt={clip.title}
            className="aspect-video w-full rounded-2xl border border-[var(--border)] object-cover"
          />
          <h3 className="mt-4 text-base font-semibold text-[var(--text)]">{clip.title || clip.identifier}</h3>
          <p className="mt-1 text-xs uppercase tracking-[0.22em] text-[var(--text3)]">{clip.license || 'Sem licença informada'}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => onPreview(clip)}
              className="rounded-full border border-[var(--border2)] px-3 py-2 text-xs text-[var(--text)] transition hover:border-[var(--blue)] hover:text-[var(--blue)]"
            >
              Preview
            </button>
            <button
              type="button"
              onClick={() => onDownload(clip)}
              className="rounded-full border border-[var(--amber)] bg-[var(--amber)]/10 px-3 py-2 text-xs text-[var(--amber)] transition hover:bg-[var(--amber)]/20"
            >
              {busyIdentifier === clip.identifier ? 'Baixando...' : 'Baixar e adicionar'}
            </button>
          </div>
        </article>
      ))}
    </div>
  );
}
