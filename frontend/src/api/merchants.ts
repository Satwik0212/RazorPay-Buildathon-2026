import { apiClient } from './client';

export const merchantsApi = {
  getMetrics: () => apiClient.get('/merchants/me/metrics'),
};
