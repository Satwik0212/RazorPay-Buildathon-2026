import { buyerApiClient } from './client';
import type { UpsellResponse } from '../types';

export const upsellApi = {
  getProductSuggestions: (productId: string, limit: number = 5) => 
    buyerApiClient.get<UpsellResponse>(`/buyer/products/${productId}/suggestions`, {
      params: { limit }
    }),
    
  getCartSuggestions: (cartId: string, context?: string, limit: number = 5) => 
    buyerApiClient.post<UpsellResponse>(`/buyer/cart/${cartId}/upsell-suggestions`, {
      context,
      limit
    }),
};
