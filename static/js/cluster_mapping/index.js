/**
 * Cluster Mapping Module
 *
 * Interface for mapping audio clusters to call types. Enables drag-and-drop
 * assignment of clusters to known call types with confidence scores.
 *
 * Dependencies:
 * - jQuery (loaded via CDN as window.jQuery)
 * - Bootstrap 4/5 JS (for modals)
 * - Toastr (for notifications, optional)
 *
 * Expected page data (from Django template):
 * - JSON script tag with id="existing-mappings-data" containing mappings array
 * - CSRF token available via csrf_data.html include or page-data element
 */

// Import all modules
import { getSelectedClusterId, setSelectedClusterId } from './state.js';
import {
  initializeExistingMappings,
  addMappingToContainer,
  updateCallBadgeCount,
} from './initialization.js';
import {
  initializeDragAndDrop,
  createMapping,
  updateMappingConfidence,
  deleteMapping,
} from './drag_drop.js';
import { filterClusters, sortClusters, filterSpecies } from './filtering.js';
import { initializeClusterPreviewModal, loadClusterDetails } from './modal_handlers.js';
import { getJsonData, setupJQueryCsrf } from '../utils/page-data.js';

/**
 * Initialize the cluster mapping interface
 * @param {Array} existingMappings - Array of existing mapping data from Django template
 */
export function initClusterMapping(existingMappings) {
  const $ = window.jQuery;
  if (!$) {
    console.error('[ClusterMapping] jQuery is not available. Cannot initialize cluster mapping.');
    return;
  }

  console.log('Initializing cluster mapping interface');

  // Initialize modal handlers
  initializeClusterPreviewModal(createMapping);

  // Initialize drag and drop
  initializeDragAndDrop(loadClusterDetails, createMapping);

  // Initialize existing mappings
  if (existingMappings && existingMappings.length > 0) {
    initializeExistingMappings(
      existingMappings,
      function (clusterId, clusterNum, clusterLabel, clusterColor, callId, confidence, mappingId) {
        addMappingToContainer(
          clusterId,
          clusterNum,
          clusterLabel,
          clusterColor,
          callId,
          confidence,
          mappingId,
          updateMappingConfidence,
          deleteMapping,
          updateCallBadgeCount
        );
      },
      updateCallBadgeCount
    );
  }

  // Clean up existing handlers to prevent duplicates on re-initialization
  $('#cluster-search').off('input');
  $('#cluster-sort').off('change');
  $('#species-filter').off('change');

  // Set up search input
  $('#cluster-search').on('input', function () {
    filterClusters($(this).val());
  });

  // Set up sort dropdown
  $('#cluster-sort').on('change', function () {
    sortClusters($(this).val());
  });

  // Set up species filter
  $('#species-filter').on('change', function () {
    filterSpecies($(this).val());
  });

  console.log('Cluster mapping interface initialized');
}

/**
 * Load existing mappings from JSON data element
 * Converts camelCase keys to snake_case for backward compatibility
 * @returns {Array} Array of mapping objects with snake_case keys
 */
function loadExistingMappingsData() {
  const existingMappingsData = getJsonData('existing-mappings-data');
  if (existingMappingsData && Array.isArray(existingMappingsData)) {
    // Convert camelCase to snake_case for backward compatibility
    return existingMappingsData.map((m) => ({
      id: m.id,
      cluster_id: m.clusterId,
      call_id: m.callId,
      confidence: m.confidence,
      species_name: m.speciesName,
      call_name: m.callName,
    }));
  }
  return [];
}

/**
 * Auto-initialize if existingMappings data is available on page load
 */
function autoInitialize() {
  const $ = window.jQuery;
  if (!$) {
    console.warn('[ClusterMapping] jQuery not available during auto-initialization. Skipping.');
    return;
  }

  // Set up CSRF for jQuery AJAX requests
  setupJQueryCsrf();

  // Load existing mappings from JSON data element
  const existingMappings = loadExistingMappingsData();

  // Also set on window for backward compatibility with other scripts
  window.existingMappings = existingMappings;

  // Initialize the mapping interface
  initClusterMapping(existingMappings);
}

// Auto-initialize on DOMContentLoaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function () {
    if (typeof window.jQuery !== 'undefined') {
      window.jQuery(document).ready(autoInitialize);
    }
  });
} else {
  if (typeof window.jQuery !== 'undefined') {
    window.jQuery(document).ready(autoInitialize);
  }
}

// Export all functions for external use
export {
  getSelectedClusterId,
  setSelectedClusterId,
  initializeExistingMappings,
  addMappingToContainer,
  updateCallBadgeCount,
  initializeDragAndDrop,
  createMapping,
  updateMappingConfidence,
  deleteMapping,
  filterClusters,
  sortClusters,
  filterSpecies,
  initializeClusterPreviewModal,
  loadClusterDetails,
};

// Expose key functions globally for Django template usage
window.initClusterMapping = initClusterMapping;
window.createMapping = createMapping;
window.filterClusters = filterClusters;
window.sortClusters = sortClusters;
window.filterSpecies = filterSpecies;

// Create ClusterMapping namespace for backward compatibility
window.ClusterMapping = {
  initClusterMapping,
  createMapping,
  filterClusters,
  sortClusters,
  filterSpecies,
  loadClusterDetails,
  updateCallBadgeCount,
  getSelectedClusterId,
  setSelectedClusterId,
};
