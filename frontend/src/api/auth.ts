import { apiClient } from './client';

export const authApi = {
  login: (data: any) => apiClient.post('/auth/login', data),
  register: (data: any) => apiClient.post('/auth/register', data),
  getMe: () => apiClient.get('/auth/me'),
  /**
   * Returns the merchant_id of the CURRENTLY AUTHENTICATED user.
   * Does NOT auto-login as any fallback/demo account.
   * Returns null if the user is not authenticated or not a merchant.
   */
  getOrInitMerchantId: async (): Promise<string | null> => {
    try {
      const meRes = await authApi.getMe();
      return meRes.data.merchant_id ?? null;
    } catch {
      // Token invalid or network error – caller must handle (redirect to login)
      return null;
    }
  }
};

