import { apiClient } from './client';
import type { AuthLoginRequest, AuthStatusResponse } from '@/types/auth';

export async function getAuthStatus() {
  const { data } = await apiClient.get<AuthStatusResponse>('/auth/status');
  return data;
}

export async function login(payload: AuthLoginRequest) {
  const { data } = await apiClient.post<AuthStatusResponse>('/auth/login', payload);
  return data;
}

export async function logout() {
  const { data } = await apiClient.post<AuthStatusResponse>('/auth/logout');
  return data;
}
