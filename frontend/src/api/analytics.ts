import { apiClient } from './client';
import type { MerchantOverviewAnalytics, MerchantIntelligenceAnalytics } from '../types';

export const analyticsApi = {
  getIntelligence: () => apiClient.get<MerchantIntelligenceAnalytics>('/analytics/merchant-intelligence'),
  getOverview: () => apiClient.get<MerchantOverviewAnalytics>('/analytics/overview'),
  getCatalogueCompleteness: () => apiClient.get<any>('/analytics/catalogue-completeness'),
};

