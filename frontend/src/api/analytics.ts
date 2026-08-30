import { apiClient } from './client';
import type { MerchantOverviewAnalytics } from '../types';

export const analyticsApi = {
  getOverview: () => apiClient.get<MerchantOverviewAnalytics>('/analytics/overview'),
};

