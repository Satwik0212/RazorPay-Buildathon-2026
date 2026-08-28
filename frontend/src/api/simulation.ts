import { apiClient } from './client';

export const simulationApi = {
  runSimulation: (data: any) => apiClient.post('/optimization/simulations', data),
  getRecommendations: (merchantId?: string) => 
    apiClient.get(merchantId ? `/optimization/recommendations?merchant_id=${merchantId}` : '/optimization/recommendations'),
};
