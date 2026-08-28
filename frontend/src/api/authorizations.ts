import { buyerApiClient as apiClient } from './client';

export const authorizationsApi = {
  createAuthorization: (quoteId: string) => apiClient.post('/authorizations', { quote_id: quoteId }),
};
