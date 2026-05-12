import { useQuery } from '@tanstack/react-query';
import { getAssembleStatus } from '@/api/media';
import { resolveApiUrl } from '@/api/client';
import type { AssembleStatusResponse } from '@/types/media';

type JobPollingState = (AssembleStatusResponse & { download_url: string | null }) | null;

export function useJobPolling(jobId: string | null) {
  return useQuery<JobPollingState>({
    queryKey: ['assemble-job', jobId],
    queryFn: async () => {
      if (!jobId) {
        return null;
      }
      const data = await getAssembleStatus(jobId);
      return {
        ...data,
        download_url: data.download_url ? resolveApiUrl(data.download_url) : null,
      };
    },
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const state = query.state.data as JobPollingState;
      if (!state || state.status === 'processing') {
        return 3000;
      }
      return false;
    },
  });
}
