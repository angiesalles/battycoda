/**
 * Cluster Explorer API Configuration
 *
 * Centralizes all API endpoint URLs used by the cluster explorer.
 * This makes it easier to maintain, test, and potentially configure endpoints.
 */

/**
 * API endpoints for cluster explorer operations
 */
export const API_ENDPOINTS = {
  /** Update cluster label and description */
  UPDATE_CLUSTER_LABEL: '/clustering/update-cluster-label/',

  /** Get cluster details (size, coherence, mappings, representative sample) */
  GET_CLUSTER_DATA: '/clustering/get-cluster-data/',

  /** Get cluster members (segments in a cluster) */
  GET_CLUSTER_MEMBERS: '/clustering/get-cluster-members/',

  /** Get segment details (spectrogram, audio, timing) */
  GET_SEGMENT_DATA: '/clustering/get-segment-data/',
};

/**
 * Build a URL with query parameters
 * @param {string} endpoint - Base endpoint URL
 * @param {Object} params - Query parameters as key-value pairs
 * @returns {string} Full URL with query string
 */
export function buildUrl(endpoint, params = {}) {
  const queryString = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join('&');

  return queryString ? `${endpoint}?${queryString}` : endpoint;
}
