import { buyerApiClient as apiClient } from './client';

export const cartsApi = {
  createItem: (cartId: string, data: any) => apiClient.post(`/carts/${cartId}/items`, data),
  createCart: (data: any) => apiClient.post('/carts', data),
  getCart: (cartId: string) => apiClient.get(`/carts/${cartId}`),
};
