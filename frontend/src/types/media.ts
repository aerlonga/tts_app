export interface EnhanceRequest {
  text: string;
  language?: string;
  generate_image_prompts?: boolean;
}

export interface EnhanceResponse {
  enhanced_text: string;
  image_prompts: ScriptPromptItem[];
}

export interface GenerateScriptRequest {
  url: string;
  language?: string;
}

export interface ScriptPromptItem {
  timestamp: string;
  cue: string;
  prompt: string;
}

export interface GenerateScriptResponse {
  script: string;
  image_prompts: ScriptPromptItem[];
  source_chars: number;
}

export interface ShortPromptItem {
  cue: string;
  prompt: string;
}

export interface WhiskPromptItem {
  cue: string;
  prompt: string;
}

export interface TimelineSegment {
  slot_index: number;
  asset_kind: 'video' | 'image';
  duration_seconds: number;
  motion_preset: string;
  overlay_text: string | null;
}

export interface ProductionPack {
  template_id: string;
  flow_video_prompt: string;
  whisk_image_prompts: WhiskPromptItem[];
  timeline_segments: TimelineSegment[];
  caption_text: string;
  cta_text: string;
}

export interface ShortItem {
  id: string;
  title: string;
  hook: string;
  script: string;
  cta: string;
  image_prompts: ShortPromptItem[];
  broll_keywords: string[];
  production_pack: ProductionPack | null;
}

export interface GenerateShortRequest {
  script: string;
  count: number;
  duration_seconds: number;
  language?: string;
}

export interface GenerateShortResponse {
  shorts: ShortItem[];
  count: number;
  duration_seconds: number;
}

export interface AssetSearchRequest {
  keywords: string[];
  collection: string;
}

export interface BrollClip {
  title: string;
  identifier: string;
  license: string;
  download_url: string;
  thumb: string;
  preview_url: string;
}

export interface AssetSearchResponse {
  clips: BrollClip[];
}

export interface BrollDownloadRequest {
  url: string;
}

export interface BrollDownloadResponse {
  local_path: string;
  filename: string;
}

export interface AssembleJobResponse {
  job_id: string;
}

export interface AssembleStatusResponse {
  status: 'processing' | 'done' | 'error';
  progress: number;
  download_url?: string | null;
  error?: string | null;
}

export interface StreamProgress {
  current: number;
  total: number;
  label: string;
}

export interface TtsLogItem {
  id: string;
  level: 'info' | 'ok' | 'warn' | 'error';
  message: string;
}
