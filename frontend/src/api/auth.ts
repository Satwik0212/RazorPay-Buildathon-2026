import { apiClient } from './client';

export const authApi = {
  login: (data: any) => apiClient.post('/auth/login', data),
  register: (data: any) => apiClient.post('/auth/register', data),
  getMe: () => apiClient.get('/auth/me'),
  getOrInitMerchantId: async (): Promise<string | null> => {
    try {
      const meRes = await authApi.getMe();
      return meRes.data.merchant_id;
    } catch {
      try {
        const loginRes = await authApi.login({ email: 'merchant@demo.com', password: 'password123' });
        localStorage.setItem('access_token', loginRes.data.access_token);
        const meRes2 = await authApi.getMe();
        return meRes2.data.merchant_id;
      } catch (e) {
        console.error('Failed to auto-init demo merchant session:', e);
        return null;
      }
    }
  }
};

