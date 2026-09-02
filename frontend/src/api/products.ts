import { apiClient } from './client';
import type { Product } from '../types';

export const productsApi = {
  getProducts: (params?: any) => apiClient.get('/products', { params }),
  getCategories: () => apiClient.get<string[]>('/products/categories'),
  createProduct: (data: any) => apiClient.post('/products', data),
  updateProduct: (id: string, data: any) => apiClient.patch(`/products/${id}`, data),
  deactivateProduct: (id: string) => apiClient.delete(`/products/${id}`),
  reactivateProduct: (id: string) => apiClient.patch(`/products/${id}/reactivate`),
  getInventory: (id: string) => apiClient.get(`/products/${id}/inventory`),
  updateInventory: (id: string, quantity: number) => apiClient.patch(`/products/${id}/inventory`, { available_quantity: quantity }),
};
