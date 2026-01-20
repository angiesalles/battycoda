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
  selectedClusterIds: { value: [], boolean: false },
});

// Export generated getters/setters
export const {
  getSelectedClusterId,
  setSelectedClusterId,
  getSelectedClusterIds,
  setSelectedClusterIds,
} = state;

/**
 * Toggle a cluster's selection state for bulk operations
 * @param {number} clusterId - Cluster ID to toggle
 * @returns {boolean} True if cluster is now selected, false if deselected
 */
export function toggleClusterSelection(clusterId) {
  const selected = getSelectedClusterIds();
  const index = selected.indexOf(clusterId);
  if (index === -1) {
    setSelectedClusterIds([...selected, clusterId]);
    return true;
  } else {
    setSelectedClusterIds(selected.filter((id) => id !== clusterId));
    return false;
  }
}

/**
 * Clear all selected clusters
 */
export function clearClusterSelection() {
  setSelectedClusterIds([]);
}

/**
 * Check if a cluster is selected
 * @param {number} clusterId - Cluster ID to check
 * @returns {boolean} True if cluster is selected
 */
export function isClusterSelected(clusterId) {
  return getSelectedClusterIds().includes(clusterId);
}

/**
 * API URLs for cluster mapping operations
 * Lazily initialized on first access from DOM config element
 */
export const API_URLS = createApiConfig(
  'page-data',
  {
    getClusterData: 'apiGetClusterData',
    createMapping: 'apiCreateMapping',
    bulkCreateMappings: 'apiBulkCreateMappings',
    updateMappingConfidence: 'apiUpdateMappingConfidence',
    deleteMapping: 'apiDeleteMapping',
  },
  {
    // Fallback URLs for tests
    getClusterData: '/clustering/get-cluster-data/',
    createMapping: '/clustering/create-mapping/',
    bulkCreateMappings: '/clustering/bulk-create-mappings/',
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
    bulkCreateMappings: API_URLS.bulkCreateMappings,
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
