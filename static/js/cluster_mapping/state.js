/**
 * Cluster Mapping State Module
 *
 * Manages shared state for the cluster mapping interface using centralized state utilities.
 */

import { createStateModule } from '../clustering/shared/create-state.js';
import { createApiConfig } from '../clustering/shared/api-config.js';

/**
 * Cluster Mapping state configuration
 * Uses createStateModule for consistent getter/setter generation
 */
const state = createStateModule({
  selectedClusterId: null,
});

// Export generated getters/setters
export const { getSelectedClusterId, setSelectedClusterId } = state;

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
 * Reset state (for testing)
 */
export function resetState() {
  state.resetAll();
}
