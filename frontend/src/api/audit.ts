import { apiClient } from './client';

export const auditApi = {
  getAuditTimeline: () => apiClient.get('/merchant/audit'),
};
