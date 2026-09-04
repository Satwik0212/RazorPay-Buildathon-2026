import { buyerApiClient as apiClient } from './client';

export const cartsApi = {
  createItem: (cartId: string, data: any) => apiClient.post(`/carts/${cartId}/items`, data),
  createCart: (data: any) => apiClient.post('/carts', data),
  getCart: (cartId: string) => apiClient.get(`/carts/${cartId}`),
  updateItem: (cartId: string, itemId: string, data: { quantity: number }) => apiClient.patch(`/carts/${cartId}/items/${itemId}`, data),
  removeItem: (cartId: string, itemId: string) => apiClient.delete(`/carts/${cartId}/items/${itemId}`),
};
