import type { TimelineSegment } from '@/types/media';
import { formatDuration } from '@/lib/utils';

interface TimelineViewProps {
  segments: TimelineSegment[];
}

export function TimelineView({ segments }: TimelineViewProps) {
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {segments.map((segment) => (
        <div key={segment.slot_index} className="rounded-2xl border border-[var(--border)] bg-[var(--bg3)]/70 p-4">
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--amber)]">Slot {segment.slot_index + 1}</p>
          <p className="mt-2 text-sm text-[var(--text)]">
            {segment.asset_kind} / {segment.motion_preset}
          </p>
          <p className="mt-1 text-sm text-[var(--text2)]">{formatDuration(segment.duration_seconds)}</p>
        </div>
      ))}
    </div>
  );
}
