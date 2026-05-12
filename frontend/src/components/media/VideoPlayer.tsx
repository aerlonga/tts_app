import { Download } from 'lucide-react';

interface VideoPlayerProps {
  url: string;
  downloadUrl?: string | null;
  title?: string;
}

export function VideoPlayer({ url, downloadUrl, title = 'Preview' }: VideoPlayerProps) {
  return (
    <div className="rounded-[24px] border border-[var(--border)] bg-[var(--bg2)] p-4">
      <p className="mb-3 text-sm uppercase tracking-[0.24em] text-[var(--text2)]">{title}</p>
      <video controls className="aspect-video w-full rounded-2xl bg-black">
        <source src={url} type="video/mp4" />
      </video>
      {downloadUrl ? (
        <a
          href={downloadUrl}
          className="mt-3 inline-flex items-center gap-2 rounded-full border border-[var(--amber)] bg-[var(--amber)]/10 px-4 py-2 text-sm text-[var(--amber)] transition hover:bg-[var(--amber)]/20"
        >
          <Download className="h-4 w-4" />
          Baixar MP4
        </a>
      ) : null}
    </div>
  );
}
