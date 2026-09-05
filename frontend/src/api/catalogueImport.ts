import { apiClient } from './client';

export interface MappingDisplay {
  source_column: string;
  target_field: string;
  confidence: number;
  confidence_level: 'HIGH' | 'MEDIUM' | 'LOW';
  reason: string;
}

export interface ImportPreviewResponse {
  import_job_id: string;
  status: string;
  schema_type: string;
  ai_mapper_used: boolean;
  has_low_confidence_mappings: boolean;
  total_rows: number;
  ready_row_count: number;
  needs_review_row_count: number;
  needs_fix_row_count: number;
  duplicate_row_count: number;
  excluded_row_count: number;
  mappings: MappingDisplay[];
  unmapped_source_columns: string[];
  missing_canonical_fields: string[];
  sample_normalized: Record<string, any>[];
  warnings: string[];
}

export interface ImportResultResponse {
  import_job_id: string;
  status: string;
  inserted: number;
  skipped_existing: number;
  failed: number;
  total_attempted: number;
  failed_rows: Array<{ row: number; reason: string }>;
}

export interface AnalyzedRow {
  row_index: number;
  status: 'READY' | 'NEEDS_REVIEW' | 'NEEDS_FIX' | 'DUPLICATE' | 'EXCLUDED';
  source_row: Record<string, any>;
  normalized_candidate: Record<string, any>;
  issues: Array<{ field?: string; error: string; severity: 'ERROR' | 'WARNING'; original_value?: any }>;
}

export interface ReviewListResponse {
  import_job_id: string;
  rows: AnalyzedRow[];
}

export const catalogueImportApi = {
  analyze: (file: File, onProgress?: (percent: number) => void) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post<ImportPreviewResponse>('/catalogue/import/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress?.(percent);
        }
      },
    });
  },
  getReviewRows: (import_job_id: string, status?: string) => {
    const params = status ? { status } : {};
    return apiClient.get<ReviewListResponse>(`/catalogue/import/${import_job_id}/review`, { params });
  },
  resolveRow: (import_job_id: string, row_index: number, action: 'ACCEPT' | 'EDIT' | 'EXCLUDE', updated_fields?: Record<string, any>) => {
    return apiClient.patch<{status: string, row: AnalyzedRow}>(`/catalogue/import/${import_job_id}/rows/${row_index}`, {
      action,
      updated_fields,
    });
  },
  confirm: (import_job_id: string) => {
    return apiClient.post<ImportResultResponse>('/catalogue/import/confirm', {
      import_job_id,
      confirmed: true,
    });
  },
};
