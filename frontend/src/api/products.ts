import { apiClient } from './client';

export const productsApi = {
  getProducts: () => apiClient.get('/products'),
  createProduct: (data: any) => apiClient.post('/products', data),
};
