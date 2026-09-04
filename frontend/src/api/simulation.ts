import { apiClient } from './client';
import type { SimulationResponse, Recommendation, WhatIfRequest, WhatIfResponse, CustomBuyerConfig } from '../types';

export const simulationApi = {
  runSimulation: (data: {
    scenario_count?: number;
    buyer_profiles?: string[];
    custom_buyer?: CustomBuyerConfig;
  }) => 
    apiClient.post<SimulationResponse>('/optimization/simulations', data),
  getRecommendations: () => 
    apiClient.get<Recommendation[]>('/optimization/recommendations'),
  runWhatIf: (data: WhatIfRequest) =>
    apiClient.post<WhatIfResponse>('/optimization/what-if', data),
  updateRecommendationStatus: (id: string, status: string) =>
    apiClient.patch<Recommendation>(`/optimization/recommendations/${id}/status`, { status }),
};

