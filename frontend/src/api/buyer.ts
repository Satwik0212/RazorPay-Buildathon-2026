import { buyerApiClient } from './client';

export const buyerApi = {
  parseIntent: (query: string) => buyerApiClient.post('/buyer/intents', { text: query }),
  searchCatalogue: (params: any) => buyerApiClient.post('/catalogue/search', params),
};
