import type { ProductionPack } from '@/types/media';
import { CopyButton } from '@/components/common/CopyButton';
import { TimelineView } from './TimelineView';

interface ProductionPackPanelProps {
  pack: ProductionPack;
}

export function ProductionPackPanel({ pack }: ProductionPackPanelProps) {
  return (
    <div className="space-y-5 rounded-[24px] border border-[var(--border)] bg-[var(--bg2)] p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-[var(--amber)]">{pack.template_id}</p>
          <h4 className="mt-2 font-display text-2xl uppercase tracking-[0.1em] text-[var(--text)]">Production Pack</h4>
        </div>
        <CopyButton text={pack.flow_video_prompt} label="Copiar Flow" />
      </div>

      <div className="rounded-2xl border border-[var(--border2)] bg-[var(--bg3)]/60 p-4">
        <p className="text-xs uppercase tracking-[0.24em] text-[var(--text3)]">Flow Video Prompt</p>
        <p className="mt-2 text-sm leading-6 text-[var(--text)]">{pack.flow_video_prompt}</p>
      </div>

      <div>
        <p className="text-xs uppercase tracking-[0.24em] text-[var(--text3)]">Whisk Image Prompts</p>
        <div className="mt-3 grid gap-3">
          {pack.whisk_image_prompts.map((prompt, index) => (
            <div key={`${prompt.cue}_${index}`} className="rounded-2xl border border-[var(--border)] bg-[var(--bg3)]/60 p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-[var(--text)]">{prompt.cue || `Cena ${index + 1}`}</p>
                  <p className="mt-2 text-sm leading-6 text-[var(--text2)]">{prompt.prompt}</p>
                </div>
                <CopyButton text={prompt.prompt} />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <p className="mb-3 text-xs uppercase tracking-[0.24em] text-[var(--text3)]">Timeline 62s</p>
        <TimelineView segments={pack.timeline_segments} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-[var(--border2)] bg-[var(--bg3)]/60 p-4">
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--amber)]">Caption Text</p>
          <p className="mt-2 text-sm text-[var(--text)]">{pack.caption_text}</p>
        </div>
        <div className="rounded-2xl border border-[var(--border2)] bg-[var(--bg3)]/60 p-4">
          <p className="text-xs uppercase tracking-[0.24em] text-[var(--amber)]">CTA Text</p>
          <p className="mt-2 text-sm text-[var(--text)]">{pack.cta_text}</p>
        </div>
      </div>
    </div>
  );
}
