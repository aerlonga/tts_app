import { create } from 'zustand';
import type { ScriptPromptItem, TimelineSegment } from '@/types/media';

export interface AssemblyAsset {
  id: string;
  source: 'upload' | 'server';
  filename: string;
  file?: File;
  path?: string;
  previewUrl?: string;
  slot_index?: number;
  asset_kind?: TimelineSegment['asset_kind'];
  duration_seconds?: number;
  motion_preset?: string;
  overlay_text?: string | null;
}

interface AppStoreState {
  selectedVoice: string;
  language: 'pt' | 'en';
  scriptDraft: string;
  imagePrompts: ScriptPromptItem[];
  ttsText: string;
  generatedAudio: File | null;
  assemblyAssets: AssemblyAsset[];
  setSelectedVoice: (voice: string) => void;
  setLanguage: (language: 'pt' | 'en') => void;
  setScriptBundle: (payload: { script: string; prompts: ScriptPromptItem[] }) => void;
  setTtsText: (text: string) => void;
  setGeneratedAudio: (file: File | null) => void;
  addAssemblyUploads: (files: File[]) => void;
  addServerAsset: (asset: Omit<AssemblyAsset, 'id' | 'source'>) => void;
  moveAssemblyAsset: (index: number, direction: -1 | 1) => void;
  removeAssemblyAsset: (id: string) => void;
  clearAssemblyAssets: () => void;
}

function toAssetId() {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

export const useAppStore = create<AppStoreState>((set) => ({
  selectedVoice: 'Charon',
  language: 'pt',
  scriptDraft: '',
  imagePrompts: [],
  ttsText: '',
  generatedAudio: null,
  assemblyAssets: [],
  setSelectedVoice: (voice) => set({ selectedVoice: voice }),
  setLanguage: (language) => set({ language }),
  setScriptBundle: ({ script, prompts }) =>
    set({
      scriptDraft: script,
      ttsText: script,
      imagePrompts: prompts,
    }),
  setTtsText: (text) => set({ ttsText: text }),
  setGeneratedAudio: (file) => set({ generatedAudio: file }),
  addAssemblyUploads: (files) =>
    set((state) => ({
      assemblyAssets: [
        ...state.assemblyAssets,
        ...files.map((file) => ({
          id: toAssetId(),
          source: 'upload' as const,
          filename: file.name,
          file,
          previewUrl: URL.createObjectURL(file),
        })),
      ],
    })),
  addServerAsset: (asset) =>
    set((state) => ({
      assemblyAssets: [
        ...state.assemblyAssets,
        {
          id: toAssetId(),
          source: 'server',
          ...asset,
        },
      ],
    })),
  moveAssemblyAsset: (index, direction) =>
    set((state) => {
      const nextIndex = index + direction;
      if (nextIndex < 0 || nextIndex >= state.assemblyAssets.length) {
        return state;
      }
      const nextAssets = [...state.assemblyAssets];
      const [item] = nextAssets.splice(index, 1);
      nextAssets.splice(nextIndex, 0, item);
      return { assemblyAssets: nextAssets };
    }),
  removeAssemblyAsset: (id) =>
    set((state) => ({
      assemblyAssets: state.assemblyAssets.filter((asset) => asset.id !== id),
    })),
  clearAssemblyAssets: () => set({ assemblyAssets: [] }),
}));
