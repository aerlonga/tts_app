import { apiClient } from './client';
import type { UsageByFeatureItem, UsageSummaryResponse } from '@/types/usage';

export async function getUsageSummary(startDate?: string, endDate?: string) {
  const { data } = await apiClient.get<UsageSummaryResponse>('/usage/summary', {
    params: {
      start_date: startDate,
      end_date: endDate,
    },
  });
  return data;
}

export async function getUsageByFeature(startDate?: string, endDate?: string) {
  const { data } = await apiClient.get<UsageByFeatureItem[]>('/usage/by-feature', {
    params: {
      start_date: startDate,
      end_date: endDate,
    },
  });
  return data;
}
