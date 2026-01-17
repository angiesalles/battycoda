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
 * Data from Django template (via DOM elements, not window globals):
 * - #cluster-data: JSON script tag containing clusters array
 * - #cluster-explorer-config: Element with data-is-project-scope attribute
 */

// Import all modules
import {
  getSelectedClusterId,
  setSelectedClusterId,
  getClusters,
  setClusters,
  getIsProjectScope,
  setIsProjectScope,
  getJQuery,
  setJQuery,
} from './state.js';
import { initializeVisualization, createLegend, updateVisualization } from './visualization.js';
import { selectCluster, loadClusterDetails, loadClusterMembers } from './interactions.js';
import { loadSegmentDetails, initializeControls } from './controls.js';
import { saveClusterLabel } from './data_loader.js';

/**
 * Initialize the cluster explorer
 * @param {Array} clusters - Cluster data from Django template
 * @param {Object} options - Optional configuration
 * @param {boolean} options.isProjectScope - Whether this is a project-scoped clustering run
 * @param {Function} options.jQuery - jQuery instance (for dependency injection in tests)
 */
export function initClusterExplorer(clusters, options = {}) {
  // Store jQuery if provided via options (for dependency injection)
  if (options.jQuery) {
    setJQuery(options.jQuery);
  }

  const $ = getJQuery();
  if (!$) {
    console.error('[ClusterExplorer] jQuery is not available. Cannot initialize cluster explorer.');
    return;
  }
  if (!clusters) {
    console.error('[ClusterExplorer] No clusters data provided. Cannot initialize cluster explorer.');
    return;
  }

  // Store clusters in state module
  setClusters(clusters);

  // Store project scope in state module
  // Check options first, then fall back to reading from DOM config element
  let projectScope = false;
  if (options.isProjectScope !== undefined) {
    projectScope = options.isProjectScope;
  } else {
    const configEl = document.getElementById('cluster-explorer-config');
    if (configEl) {
      projectScope = configEl.dataset.isProjectScope === 'true';
    }
  }
  setIsProjectScope(projectScope);

  // Initialize the visualization
  initializeVisualization(clusters);

  // Set up control event handlers
  initializeControls();

  // Clean up any existing event handlers to prevent duplicates on re-initialization
  $('#save-cluster-label').off('click');
  $(document).off('click', '.view-segment-btn');

  // Set up save button
  $('#save-cluster-label').on('click', function () {
    saveClusterLabel(function (clusterId) {
      // Re-initialize visualization and re-select the cluster
      initializeVisualization(getClusters());
      selectCluster(clusterId);
    });
  });

  // Load segment details when a segment is clicked
  $(document).on('click', '.view-segment-btn', function () {
    const segmentId = $(this).data('segment-id');
    loadSegmentDetails(segmentId);
  });
}

/**
 * Auto-initialize if clusters data is available on page load.
 * Reads cluster data from a JSON script tag (#cluster-data) in the DOM.
 */
function autoInitialize() {
  const $ = window.jQuery;
  if (!$) {
    console.warn('[ClusterExplorer] jQuery not available during auto-initialization. Skipping.');
    return;
  }

  // Try to read clusters from JSON script tag in DOM
  const clusterDataEl = document.getElementById('cluster-data');
  if (clusterDataEl) {
    try {
      const clusters = JSON.parse(clusterDataEl.textContent);
      if (clusters && Array.isArray(clusters)) {
        initClusterExplorer(clusters);
        return;
      }
    } catch (e) {
      console.error('[ClusterExplorer] Failed to parse cluster data from #cluster-data:', e);
    }
  }

  console.debug('[ClusterExplorer] No cluster data found (#cluster-data element). Auto-initialization skipped.');
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
  getClusters,
  setClusters,
  getIsProjectScope,
  setIsProjectScope,
  getJQuery,
  setJQuery,
  initializeVisualization,
  createLegend,
  updateVisualization,
  selectCluster,
  loadClusterDetails,
  loadClusterMembers,
  loadSegmentDetails,
  saveClusterLabel,
};
