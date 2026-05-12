import { apiClient } from './client';
import type {
  AssetSearchRequest,
  AssetSearchResponse,
  BrollDownloadRequest,
  BrollDownloadResponse,
} from '@/types/media';

export async function searchBroll(payload: AssetSearchRequest) {
  const { data } = await apiClient.post<AssetSearchResponse>('/broll/search', payload);
  return data;
}

export async function downloadBroll(payload: BrollDownloadRequest) {
  const { data } = await apiClient.post<BrollDownloadResponse>('/broll/download', payload);
  return data;
}
