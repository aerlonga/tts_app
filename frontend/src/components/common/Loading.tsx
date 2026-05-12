import { LoaderCircle } from 'lucide-react';

interface LoadingProps {
  label?: string;
}

export function Loading({ label = 'Carregando...' }: LoadingProps) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-[var(--border)] bg-[var(--bg2)] px-4 py-3 text-sm text-[var(--text2)]">
      <LoaderCircle className="h-4 w-4 animate-spin text-[var(--amber)]" />
      <span>{label}</span>
    </div>
  );
}
