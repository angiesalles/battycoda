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
 * Global data expected from Django template:
 * - existingMappings: Array of existing mapping objects
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

/**
 * Initialize the cluster mapping interface
 * @param {Array} existingMappings - Array of existing mapping data from Django template
 */
export function initClusterMapping(existingMappings) {
  const $ = window.jQuery;
  if (!$) return;

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
 * Auto-initialize if existingMappings data is available on page load
 */
function autoInitialize() {
  const $ = window.jQuery;
  if (!$) return;

  // Check if existingMappings data is available
  if (typeof window.existingMappings !== 'undefined') {
    initClusterMapping(window.existingMappings);
  } else {
    // Still initialize without existing mappings
    initClusterMapping([]);
  }
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
