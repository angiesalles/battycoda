/**
 * Cluster Mapping State Module
 *
 * Manages shared state for the cluster mapping interface.
 */

// Currently selected cluster ID
let selectedClusterId = null;

// Cached API URLs
let apiUrls = null;

/**
 * Get API URLs from the page-data element
 * Falls back to hardcoded values if not found (for tests)
 * @returns {Object} API URLs
 */
export function getApiUrls() {
  if (apiUrls) return apiUrls;

  const pageData = document.getElementById('page-data');
  if (pageData) {
    apiUrls = {
      getClusterData: pageData.dataset.apiGetClusterData,
      createMapping: pageData.dataset.apiCreateMapping,
      updateMappingConfidence: pageData.dataset.apiUpdateMappingConfidence,
      deleteMapping: pageData.dataset.apiDeleteMapping,
    };
  } else {
    // Fallback for tests
    console.warn('page-data element not found, using fallback URLs');
    apiUrls = {
      getClusterData: '/clustering/get-cluster-data/',
      createMapping: '/clustering/create-mapping/',
      updateMappingConfidence: '/clustering/update-mapping-confidence/',
      deleteMapping: '/clustering/delete-mapping/',
    };
  }

  return apiUrls;
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
