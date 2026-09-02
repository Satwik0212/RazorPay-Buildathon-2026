import { apiClient, buyerApiClient } from './client';
import type { Campaign, CampaignStatusUpdate } from '../types';

export const campaignsApi = {
  generateCampaigns: () => apiClient.post<Campaign[]>('/campaigns/generate'),
  listCampaigns: () => apiClient.get<Campaign[]>('/campaigns'),
  getCampaign: (id: string) => apiClient.get<Campaign>(`/campaigns/${id}`),
  updateStatus: (id: string, data: CampaignStatusUpdate) => apiClient.patch<Campaign>(`/campaigns/${id}/status`, data),
  getActiveCampaigns: (merchantId: string) => buyerApiClient.get<Campaign[]>(`/buyer/campaigns?merchant_id=${merchantId}`),
};
