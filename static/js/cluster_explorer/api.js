/**
 * Cluster Explorer API Configuration
 *
 * Centralizes all API endpoint URLs used by the cluster explorer.
 * URLs are read from data attributes in the template for flexibility.
 */

/**
 * Get API endpoints from the config element
 * Falls back to hardcoded values if config element is not found (for tests)
 * @returns {Object} API endpoints
 */
function getApiEndpoints() {
  const configElement = document.getElementById('cluster-explorer-config');

  if (configElement) {
    return {
      UPDATE_CLUSTER_LABEL: configElement.dataset.apiUpdateClusterLabel,
      GET_CLUSTER_DATA: configElement.dataset.apiGetClusterData,
      GET_CLUSTER_MEMBERS: configElement.dataset.apiGetClusterMembers,
      GET_SEGMENT_DATA: configElement.dataset.apiGetSegmentData,
    };
  }

  // Fallback for tests or if config element is missing
  console.warn('cluster-explorer-config element not found, using fallback URLs');
  return {
    UPDATE_CLUSTER_LABEL: '/clustering/update-cluster-label/',
    GET_CLUSTER_DATA: '/clustering/get-cluster-data/',
    GET_CLUSTER_MEMBERS: '/clustering/get-cluster-members/',
    GET_SEGMENT_DATA: '/clustering/get-segment-data/',
  };
}

/**
 * API endpoints for cluster explorer operations
 * Lazily initialized on first access
 */
let _endpoints = null;
export const API_ENDPOINTS = new Proxy(
  {},
  {
    get(target, prop) {
      if (!_endpoints) {
        _endpoints = getApiEndpoints();
      }
      return _endpoints[prop];
    },
  }
);

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
