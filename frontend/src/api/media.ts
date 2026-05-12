import { apiClient } from './client';
import type {
  AssembleJobResponse,
  AssembleStatusResponse,
  AssetSearchRequest,
  AssetSearchResponse,
  EnhanceRequest,
  EnhanceResponse,
  GenerateScriptRequest,
  GenerateScriptResponse,
  GenerateShortRequest,
  GenerateShortResponse,
} from '@/types/media';

export async function generateScript(payload: GenerateScriptRequest) {
  const { data } = await apiClient.post<GenerateScriptResponse>('/media/generate-script', payload);
  return data;
}

export async function enhanceText(payload: EnhanceRequest) {
  const { data } = await apiClient.post<EnhanceResponse>('/media/enhance', payload);
  return data;
}

export async function generateShorts(payload: GenerateShortRequest) {
  const { data } = await apiClient.post<GenerateShortResponse>('/media/generate-short', payload);
  return data;
}

export async function searchAssets(payload: AssetSearchRequest) {
  const { data } = await apiClient.post<AssetSearchResponse>('/media/search-assets', payload);
  return data;
}

export async function createAssembleJob(formData: FormData) {
  const { data } = await apiClient.post<AssembleJobResponse>('/media/assemble', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return data;
}

export async function createGeneratedVideoJob(formData: FormData) {
  const { data } = await apiClient.post<AssembleJobResponse>('/media/generate-video', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return data;
}

export async function getAssembleStatus(jobId: string) {
  const { data } = await apiClient.get<AssembleStatusResponse>(`/media/assemble/status/${jobId}`);
  return data;
}
