import { buyerApiClient as apiClient } from './client';

export const quotesApi = {
  createQuote: (cartId: string) => apiClient.post('/quotes', { cart_id: cartId }),
};
