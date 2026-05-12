import { AlertTriangle, CheckCircle2, Info, LoaderCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

type AlertTone = 'info' | 'success' | 'error' | 'loading';

const toneMap: Record<AlertTone, { icon: typeof Info; className: string }> = {
  info: {
    icon: Info,
    className: 'border-[var(--blue)]/30 bg-[var(--blue)]/10 text-[var(--text)]',
  },
  success: {
    icon: CheckCircle2,
    className: 'border-[var(--green)]/30 bg-[var(--green)]/10 text-[var(--text)]',
  },
  error: {
    icon: AlertTriangle,
    className: 'border-[var(--red)]/30 bg-[var(--red)]/10 text-[var(--text)]',
  },
  loading: {
    icon: LoaderCircle,
    className: 'border-[var(--amber)]/30 bg-[var(--amber)]/10 text-[var(--text)]',
  },
};

interface AlertProps {
  tone?: AlertTone;
  message: string;
  className?: string;
}

export function Alert({ tone = 'info', message, className }: AlertProps) {
  const Icon = toneMap[tone].icon;
  return (
    <div className={cn('flex items-start gap-3 rounded-2xl border px-4 py-3 text-sm', toneMap[tone].className, className)}>
      <Icon className={cn('mt-0.5 h-4 w-4 shrink-0', tone === 'loading' && 'animate-spin')} />
      <p>{message}</p>
    </div>
  );
}
