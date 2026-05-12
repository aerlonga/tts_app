import { apiClient } from './client';
import type { HealthDetailsResponse, HealthResponse } from '@/types/health';

export async function getHealth() {
  const { data } = await apiClient.get<HealthResponse>('/health');
  return data;
}

export async function getHealthDetails() {
  const { data } = await apiClient.get<HealthDetailsResponse>('/health/details');
  return data;
}
