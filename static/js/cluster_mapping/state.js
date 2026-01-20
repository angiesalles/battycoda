/**
 * Cluster Mapping State Module
 *
 * Manages shared state for the cluster mapping interface.
 */

import { createApiConfig } from '../clustering/shared/api-config.js';

// Currently selected cluster ID
let selectedClusterId = null;

/**
 * API URLs for cluster mapping operations
 * Lazily initialized on first access from DOM config element
 */
export const API_URLS = createApiConfig(
  'page-data',
  {
    getClusterData: 'apiGetClusterData',
    createMapping: 'apiCreateMapping',
    updateMappingConfidence: 'apiUpdateMappingConfidence',
    deleteMapping: 'apiDeleteMapping',
  },
  {
    // Fallback URLs for tests
    getClusterData: '/clustering/get-cluster-data/',
    createMapping: '/clustering/create-mapping/',
    updateMappingConfidence: '/clustering/update-mapping-confidence/',
    deleteMapping: '/clustering/delete-mapping/',
  }
);

/**
 * Get API URLs (for backward compatibility)
 * @returns {Object} API URLs
 * @deprecated Use API_URLS directly instead
 */
export function getApiUrls() {
  return {
    getClusterData: API_URLS.getClusterData,
    createMapping: API_URLS.createMapping,
    updateMappingConfidence: API_URLS.updateMappingConfidence,
    deleteMapping: API_URLS.deleteMapping,
  };
}

/**
 * Get the currently selected cluster ID
 * @returns {number|null} Selected cluster ID
 */
export function getSelectedClusterId() {
  return selectedClusterId;
}

/**
 * Set the selected cluster ID
 * @param {number|null} id - Cluster ID to select
 */
export function setSelectedClusterId(id) {
  selectedClusterId = id;
}

/**
 * Reset state (for testing)
 */
export function resetState() {
  selectedClusterId = null;
}
