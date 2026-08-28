import { buyerApiClient as apiClient } from './client';

export const checkoutApi = {
  createOrder: (data: any) => apiClient.post('/checkout/orders', data),
};
