/**
 * API response type definitions for BattyCoda
 *
 * These types define the structure of API responses from the Django backend.
 */

/**
 * Standard API success response
 */
export interface ApiSuccessResponse<T = unknown> {
  status: 'success';
  data?: T;
  message?: string;
}

/**
 * Standard API error response
 */
export interface ApiErrorResponse {
  status: 'error';
  message: string;
  errors?: Record<string, string[]>;
}

/**
 * Generic API response (success or error)
 */
export type ApiResponse<T = unknown> = ApiSuccessResponse<T> | ApiErrorResponse;

/**
 * Paginated API response
 */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * Cluster data response from API
 */
export interface ClusterDataResponse {
  id: number;
  label: string | null;
  description: string | null;
  size: number;
  coherence_score: number | null;
  vis_x: number;
  vis_y: number;
  is_labeled: boolean;
  created_at: string;
}

/**
 * Cluster members response
 */
export interface ClusterMembersResponse {
  cluster_id: number;
  cluster_label: string | null;
  members: ClusterMemberResponse[];
}

/**
 * Individual cluster member
 */
export interface ClusterMemberResponse {
  segment_id: number;
  onset: number;
  offset: number;
  recording_id: number;
  recording_name: string;
  confidence: number;
  spectrogram_url?: string;
}

/**
 * Update cluster label request
 */
export interface UpdateClusterLabelRequest {
  cluster_id: number;
  label: string;
  description?: string;
}

/**
 * Update cluster label response
 */
export interface UpdateClusterLabelResponse {
  status: 'success' | 'error';
  message?: string;
}

/**
 * Recording upload response
 */
export interface RecordingUploadResponse {
  status: 'success' | 'error';
  recording_id?: number;
  message?: string;
  errors?: string[];
}

/**
 * Classification result from API
 */
export interface ClassificationResultResponse {
  segment_id: number;
  predicted_call: string;
  confidence: number;
  probabilities: Record<string, number>;
}

/**
 * Segmentation status response
 */
export interface SegmentationStatusResponse {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  message?: string;
  segments?: number;
}

/**
 * Task response
 */
export interface TaskResponse {
  id: number;
  segment_id: number;
  recording_id: number;
  recording_name: string;
  onset: number;
  offset: number;
  status: string;
  spectrogram_url: string;
  audio_url: string;
  possible_calls: CallResponse[];
}

/**
 * Call response (for dropdowns, etc.)
 */
export interface CallResponse {
  id: number;
  short_name: string;
  long_name: string | null;
}

/**
 * Species response
 */
export interface SpeciesResponse {
  id: number;
  name: string;
  scientific_name: string | null;
  calls: CallResponse[];
}
