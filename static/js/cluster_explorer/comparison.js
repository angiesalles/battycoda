/**
 * Cluster Explorer Comparison Module
 *
 * Enables side-by-side comparison of two clusters.
 */

import { getJQuery, getClusters, getSelectedClusterId } from './state.js';
import { API_ENDPOINTS, buildUrl } from './api.js';
import { escapeHtml } from '../utils/html.js';
import { showLoading, showErrorWithRetry, parseErrorResponse } from '../utils/error-handling.js';

// Store comparison cluster IDs
let comparisonCluster1 = null;
let comparisonCluster2 = null;

// Cached cluster data
let cluster1Data = null;
let cluster2Data = null;

/**
 * Initialize comparison functionality
 */
export function initializeComparison() {
  const $ = getJQuery();
  if (!$) {
    console.error('[ClusterExplorer] jQuery not available. Cannot initialize comparison.');
    return;
  }

  // Set up compare button handler
  $('#compare-cluster-btn').off('click').on('click', handleCompareClick);

  // Set up modal second cluster selection
  $('#comparison-cluster-select').off('change').on('change', handleSecondClusterSelect);

  // Set up clear comparison button
  $('#clear-comparison-btn').off('click').on('click', clearComparison);

  console.debug('[ClusterExplorer] Comparison module initialized.');
}

/**
 * Handle compare button click
 */
function handleCompareClick() {
  const _$ = getJQuery();
  const selectedId = getSelectedClusterId();

  if (!selectedId) {
    window.toast?.warning('Please select a cluster first');
    return;
  }

  // Set the first cluster
  comparisonCluster1 = selectedId;
  cluster1Data = null;

  // Populate the second cluster dropdown
  populateSecondClusterDropdown(selectedId);

  // Show the modal
  const modal = new window.bootstrap.Modal(document.getElementById('clusterComparisonModal'));
  modal.show();

  // Load the first cluster data
  loadClusterForComparison(selectedId, 1);
}

/**
 * Populate the dropdown for selecting the second cluster
 * @param {number} excludeId - Cluster ID to exclude (the first cluster)
 */
function populateSecondClusterDropdown(excludeId) {
  const $ = getJQuery();
  const clusters = getClusters();

  if (!clusters) return;

  const $select = $('#comparison-cluster-select');
  $select.empty();
  $select.append('<option value="">-- Select a cluster to compare --</option>');

  clusters.forEach((cluster) => {
    if (cluster.id !== excludeId) {
      const label = cluster.label || `Cluster ${cluster.cluster_id}`;
      $select.append(`<option value="${cluster.id}">${escapeHtml(label)} (${cluster.size} segments)</option>`);
    }
  });
}

/**
 * Handle second cluster selection
 */
function handleSecondClusterSelect() {
  const $ = getJQuery();
  const selectedId = parseInt($('#comparison-cluster-select').val(), 10);

  if (!selectedId) {
    // Clear the second comparison pane
    $('#comparison-cluster-2').html(`
      <div class="text-center text-muted py-5">
        <i class="fas fa-arrow-left fa-2x mb-2"></i>
        <p>Select a cluster to compare</p>
      </div>
    `);
    comparisonCluster2 = null;
    cluster2Data = null;
    return;
  }

  comparisonCluster2 = selectedId;
  loadClusterForComparison(selectedId, 2);
}

/**
 * Load cluster data for comparison
 * @param {number} clusterId - Cluster ID to load
 * @param {number} position - 1 or 2 (which comparison pane)
 */
function loadClusterForComparison(clusterId, position) {
  const $ = getJQuery();
  const $container = $(`#comparison-cluster-${position}`);

  showLoading($container, 'Loading cluster data...');

  $.getJSON(buildUrl(API_ENDPOINTS.GET_CLUSTER_DATA, { cluster_id: clusterId }), function (data) {
    if (data.success) {
      if (position === 1) {
        cluster1Data = data;
      } else {
        cluster2Data = data;
      }
      renderComparisonPane(data, position);

      // If both clusters are loaded, update the comparison metrics
      if (cluster1Data && cluster2Data) {
        updateComparisonMetrics();
      }
    } else {
      const errorMsg = data.error || 'Failed to load cluster';
      showErrorWithRetry($container, errorMsg, {
        errorCode: data.error_code,
        onRetry: () => loadClusterForComparison(clusterId, position),
      });
    }
  }).fail(function (xhr) {
    const { message, errorCode } = parseErrorResponse(xhr, 'Failed to load cluster data');
    showErrorWithRetry($container, message, {
      errorCode,
      onRetry: () => loadClusterForComparison(clusterId, position),
    });
  });
}

/**
 * Render a comparison pane with cluster data
 * @param {Object} data - Cluster data from API
 * @param {number} position - 1 or 2
 */
function renderComparisonPane(data, position) {
  const $ = getJQuery();
  const $container = $(`#comparison-cluster-${position}`);

  const label = data.label || `Cluster ${data.cluster_id}`;
  const coherence = data.coherence ? data.coherence.toFixed(4) : 'N/A';

  const html = `
    <div class="comparison-cluster-pane">
      <h5 class="text-center mb-3">${escapeHtml(label)}</h5>

      <div class="comparison-spectrogram mb-3">
        ${
          data.representative_spectrogram_url
            ? `<img src="${data.representative_spectrogram_url}" class="img-fluid rounded" alt="Representative Spectrogram">`
            : '<div class="alert alert-info mb-0">No representative sample</div>'
        }
      </div>

      <div class="comparison-audio mb-3">
        ${
          data.representative_audio_url
            ? `<audio controls class="w-100">
                <source src="${data.representative_audio_url}" type="audio/wav">
               </audio>`
            : ''
        }
      </div>

      <table class="table table-sm table-bordered">
        <tr>
          <th>Size</th>
          <td class="text-end cluster-size-${position}">${data.size} segments</td>
        </tr>
        <tr>
          <th>Coherence</th>
          <td class="text-end cluster-coherence-${position}">${coherence}</td>
        </tr>
        <tr>
          <th>Labeled</th>
          <td class="text-end">${data.is_labeled ? '<i class="fas fa-check text-success"></i> Yes' : '<i class="fas fa-times text-muted"></i> No'}</td>
        </tr>
        <tr>
          <th>Mappings</th>
          <td class="text-end">${data.mappings ? data.mappings.length : 0}</td>
        </tr>
      </table>

      ${
        data.mappings && data.mappings.length > 0
          ? `
        <div class="mt-2">
          <strong>Mapped to:</strong>
          <ul class="list-unstyled mb-0 mt-1">
            ${data.mappings
              .map(
                (m) =>
                  `<li><small>${escapeHtml(m.species_name)}: ${escapeHtml(m.call_name)} (${(m.confidence * 100).toFixed(0)}%)</small></li>`
              )
              .join('')}
          </ul>
        </div>
      `
          : ''
      }
    </div>
  `;

  $container.html(html);
}

/**
 * Update comparison metrics between two clusters
 */
function updateComparisonMetrics() {
  const $ = getJQuery();

  if (!cluster1Data || !cluster2Data) return;

  const sizeDiff = cluster1Data.size - cluster2Data.size;
  const sizeDiffText =
    sizeDiff === 0
      ? 'Same size'
      : sizeDiff > 0
        ? `Cluster 1 is ${sizeDiff} larger`
        : `Cluster 2 is ${Math.abs(sizeDiff)} larger`;

  let coherenceDiff = '';
  if (cluster1Data.coherence && cluster2Data.coherence) {
    const diff = cluster1Data.coherence - cluster2Data.coherence;
    if (Math.abs(diff) < 0.001) {
      coherenceDiff = 'Similar coherence';
    } else if (diff > 0) {
      coherenceDiff = `Cluster 1 is ${(diff * 100).toFixed(1)}% more coherent`;
    } else {
      coherenceDiff = `Cluster 2 is ${(Math.abs(diff) * 100).toFixed(1)}% more coherent`;
    }
  }

  // Update the comparison summary
  const $summary = $('#comparison-summary');
  if ($summary.length) {
    $summary.html(`
      <div class="alert alert-info mb-0">
        <strong>Comparison:</strong>
        <ul class="mb-0 mt-1">
          <li>${sizeDiffText}</li>
          ${coherenceDiff ? `<li>${coherenceDiff}</li>` : ''}
        </ul>
      </div>
    `);
  }
}

/**
 * Clear the comparison state
 */
export function clearComparison() {
  const $ = getJQuery();

  comparisonCluster1 = null;
  comparisonCluster2 = null;
  cluster1Data = null;
  cluster2Data = null;

  $('#comparison-cluster-1').html(`
    <div class="text-center text-muted py-5">
      <i class="fas fa-project-diagram fa-2x mb-2"></i>
      <p>Select a cluster and click "Compare"</p>
    </div>
  `);

  $('#comparison-cluster-2').html(`
    <div class="text-center text-muted py-5">
      <i class="fas fa-arrow-left fa-2x mb-2"></i>
      <p>Select a cluster to compare</p>
    </div>
  `);

  $('#comparison-summary').empty();
  $('#comparison-cluster-select').val('');
}

/**
 * Get current comparison state (for external use)
 */
export function getComparisonState() {
  return {
    cluster1: comparisonCluster1,
    cluster2: comparisonCluster2,
    cluster1Data,
    cluster2Data,
  };
}
