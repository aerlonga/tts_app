import { Download } from 'lucide-react';

interface AudioPlayerProps {
  url: string;
  fileName: string;
}

export function AudioPlayer({ url, fileName }: AudioPlayerProps) {
  return (
    <div className="rounded-[24px] border border-[var(--border)] bg-[var(--bg2)] p-4">
      <audio controls className="w-full">
        <source src={url} type="audio/wav" />
      </audio>
      <a
        href={url}
        download={fileName}
        className="mt-3 inline-flex items-center gap-2 rounded-full border border-[var(--amber)] bg-[var(--amber)]/10 px-4 py-2 text-sm text-[var(--amber)] transition hover:bg-[var(--amber)]/20"
      >
        <Download className="h-4 w-4" />
        Baixar WAV
      </a>
    </div>
  );
}
