import { apiClient } from './client';
import type { BuyerPersona } from '../types';

export const personasApi = {
  getPersonas: () => apiClient.get<BuyerPersona[]>('/buyer-personas'),
};
