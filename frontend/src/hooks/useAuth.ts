import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getAuthStatus, login, logout } from '@/api/auth';

const authKey = ['auth-status'];

export function useAuth() {
  const queryClient = useQueryClient();

  const statusQuery = useQuery({
    queryKey: authKey,
    queryFn: getAuthStatus,
    retry: false,
  });

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: (data) => {
      queryClient.setQueryData(authKey, data);
    },
  });

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: (data) => {
      queryClient.setQueryData(authKey, data);
    },
  });

  return {
    ...statusQuery,
    login: loginMutation.mutateAsync,
    logout: logoutMutation.mutateAsync,
    loginPending: loginMutation.isPending,
    logoutPending: logoutMutation.isPending,
  };
}
