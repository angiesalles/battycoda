/**
 * Cluster Explorer Module
 *
 * Interactive visualization and exploration of audio segment clusters using D3.js.
 * Allows users to explore clustering results, view segment details, and update labels.
 *
 * Dependencies:
 * - D3.js (bundled via npm for tree-shaking benefits)
 * - jQuery (loaded via CDN as window.jQuery)
 *
 * Global data expected from Django template:
 * - window.clusters: Array of cluster objects
 * - window.isProjectScope: Boolean indicating project-level clustering
 */

// Import all modules
import { getSelectedClusterId, setSelectedClusterId } from './state.js';
import { initializeVisualization, createLegend, updateVisualization } from './visualization.js';
import { selectCluster, loadClusterDetails, loadClusterMembers } from './interactions.js';
import { loadSegmentDetails, initializeControls } from './controls.js';
import { saveClusterLabel } from './data_loader.js';

/**
 * Initialize the cluster explorer
 * @param {Array} clusters - Cluster data from Django template
 */
export function initClusterExplorer(clusters) {
  const $ = window.jQuery;
  if (!$ || !clusters) return;

  // Store clusters globally for other components
  window.clusters = clusters;

  // Initialize the visualization
  initializeVisualization(clusters);

  // Set up control event handlers
  initializeControls();

  // Set up save button
  $('#save-cluster-label').on('click', function () {
    saveClusterLabel(function (clusterId) {
      // Re-initialize visualization and re-select the cluster
      initializeVisualization(window.clusters);
      selectCluster(clusterId);
    });
  });

  // Set up controls
  $('#point-size').on('input', updateVisualization);
  $('#cluster-opacity').on('input', updateVisualization);

  // Load segment details when a segment is clicked
  $(document).on('click', '.view-segment-btn', function () {
    const segmentId = $(this).data('segment-id');
    loadSegmentDetails(segmentId);
  });
}

/**
 * Auto-initialize if clusters data is available on page load
 */
function autoInitialize() {
  const $ = window.jQuery;
  if (!$) return;

  // Check if clusters data is available
  if (typeof window.clusters !== 'undefined' && window.clusters) {
    initClusterExplorer(window.clusters);
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
  initializeVisualization,
  createLegend,
  updateVisualization,
  selectCluster,
  loadClusterDetails,
  loadClusterMembers,
  loadSegmentDetails,
  saveClusterLabel,
};

// Expose key functions globally for Django template usage
window.initClusterExplorer = initClusterExplorer;
window.selectCluster = selectCluster;
window.loadSegmentDetails = loadSegmentDetails;
window.saveClusterLabel = saveClusterLabel;
window.initializeVisualization = initializeVisualization;
