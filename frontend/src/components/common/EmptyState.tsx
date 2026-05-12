interface EmptyStateProps {
  title: string;
  description: string;
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="rounded-[28px] border border-dashed border-[var(--border2)] bg-[var(--bg2)]/60 px-6 py-8 text-center">
      <p className="font-display text-2xl uppercase tracking-[0.18em] text-[var(--text)]">{title}</p>
      <p className="mx-auto mt-2 max-w-xl text-sm text-[var(--text2)]">{description}</p>
    </div>
  );
}
