interface ProgressBarProps {
  value: number;
  label: string;
  rightLabel?: string;
}

export function ProgressBar({ value, label, rightLabel }: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, value));

  return (
    <div className="rounded-[24px] border border-[var(--border)] bg-[var(--bg2)] p-4">
      <div className="mb-3 flex items-center justify-between gap-3 text-sm">
        <span className="text-[var(--text)]">{label}</span>
        <span className="text-[var(--text2)]">{rightLabel || `${Math.round(clamped)}%`}</span>
      </div>
      <div className="h-3 rounded-full bg-[var(--bg3)]">
        <div
          className="h-3 rounded-full bg-[linear-gradient(90deg,var(--amber),#f0b44b)] transition-all duration-300"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
