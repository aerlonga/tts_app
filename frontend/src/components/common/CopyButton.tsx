import { Copy } from 'lucide-react';
import { copyToClipboard } from '@/lib/utils';

interface CopyButtonProps {
  text: string;
  label?: string;
}

export function CopyButton({ text, label = 'Copiar' }: CopyButtonProps) {
  return (
    <button
      type="button"
      onClick={() => void copyToClipboard(text)}
      className="inline-flex items-center gap-2 rounded-full border border-[var(--border2)] bg-[var(--bg3)] px-3 py-1.5 text-xs font-medium text-[var(--text)] transition hover:border-[var(--amber)] hover:text-[var(--amber)]"
    >
      <Copy className="h-3.5 w-3.5" />
      {label}
    </button>
  );
}
