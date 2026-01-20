/**
 * Cluster Explorer Interactions Module
 *
 * Handles cluster selection and detail loading.
 * D3 is now bundled via npm for tree-shaking benefits.
 */

import { selectAll } from 'd3-selection';
import { setSelectedClusterId, setFocusedClusterIndex, getIsProjectScope, getJQuery } from './state.js';
import { escapeHtml } from '../utils/html.js';
import { API_ENDPOINTS, buildUrl } from './api.js';
import { showErrorWithRetry, parseErrorResponse, showLoading } from '../utils/error-handling.js';

// Store last request parameters for retry functionality (reserved for future use)
let _lastClusterDetailsRequest = null;
let _lastClusterMembersRequest = null;

/**
 * Select a cluster and display its details
 * @param {number} clusterId - Cluster ID to select
 */
export function selectCluster(clusterId) {
  const $ = getJQuery();
  if (!$) {
    console.error('[ClusterExplorer] jQuery is not available. Cannot select cluster.');
    return;
  }

  if (clusterId === null || clusterId === undefined) {
    console.warn('[ClusterExplorer] Invalid cluster ID provided to selectCluster.');
    return;
  }

  // Update the selection
  setSelectedClusterId(clusterId);

  // Highlight the selected cluster in the visualization
  const pointSize = parseInt($('#point-size').val()) || 8;
  const points = selectAll('.cluster-point');

  if (!points.empty()) {
    try {
      points
        .attr('stroke-width', (d) => (d.id === clusterId ? 3 : 1))
        .attr('stroke', (d) => (d.id === clusterId ? '#fff' : '#000'))
        .attr('r', (d) => (d.id === clusterId ? pointSize * 1.5 : pointSize));
    } catch (error) {
      console.error('[ClusterExplorer] Failed to update cluster point highlighting:', error);
    }
  } else {
    console.warn('[ClusterExplorer] No cluster points found to highlight.');
  }

  // Load the cluster details
  loadClusterDetails(clusterId);

  // Load cluster members
  loadClusterMembers(clusterId);
}

/**
 * Load cluster details from the API
 * @param {number} clusterId - Cluster ID to load
 */
export function loadClusterDetails(clusterId) {
  const $ = getJQuery();
  if (!$) {
    console.error('[ClusterExplorer] jQuery is not available. Cannot load cluster details.');
    return;
  }

  // Store for retry
  _lastClusterDetailsRequest = clusterId;

  // Show the details panel
  $('.initial-message').addClass('d-none');
  $('.cluster-details').removeClass('d-none');

  // Show a loading indicator
  showLoading($('.cluster-details'), 'Loading cluster details...');

  // Load the details from the API
  $.getJSON(buildUrl(API_ENDPOINTS.GET_CLUSTER_DATA, { cluster_id: clusterId }), function (data) {
    if (data.success) {
      renderClusterDetails(data);
    } else {
      const errorMsg = data.error || 'Unknown error loading cluster details';
      showErrorWithRetry($('.cluster-details'), errorMsg, {
        errorCode: data.error_code,
        onRetry: () => loadClusterDetails(clusterId),
      });
    }
  }).fail(function (xhr) {
    const { message, errorCode } = parseErrorResponse(xhr, 'Failed to load cluster details');
    showErrorWithRetry($('.cluster-details'), message, {
      errorCode,
      onRetry: () => loadClusterDetails(clusterId),
    });
  });
}

/**
 * Render cluster details in the panel
 * @param {Object} data - Cluster data from API
 */
function renderClusterDetails(data) {
  const $ = getJQuery();

  // Build the details HTML
  const detailsHtml = `
    <h5 class="cluster-id-display">Cluster ${data.cluster_id}</h5>
    <div class="form-group">
      <label for="cluster-label">Label</label>
      <input type="text" class="form-control" id="cluster-label" value="${escapeHtml(data.label || '')}">
    </div>
    <div class="form-group">
      <label for="cluster-description">Description</label>
      <textarea class="form-control" id="cluster-description" rows="3">${escapeHtml(data.description || '')}</textarea>
    </div>
    <button id="save-cluster-label" class="btn btn-primary">
      <i class="fas fa-save"></i> Save
    </button>

    <hr>

    <div class="cluster-stats mt-3">
      <table class="table table-sm">
        <tr>
          <th>Size</th>
          <td class="cluster-size">${data.size}</td>
        </tr>
        <tr>
          <th>Coherence</th>
          <td class="cluster-coherence">${data.coherence ? data.coherence.toFixed(4) : 'N/A'}</td>
        </tr>
      </table>
    </div>

    <div class="representative-sample mt-3">
      <h6>Representative Sample</h6>
      <div class="representative-spectrogram">
        ${
          data.representative_spectrogram_url
            ? `<img src="${data.representative_spectrogram_url}" class="img-fluid" alt="Representative Spectrogram">`
            : '<div class="alert alert-info">No representative sample available</div>'
        }
      </div>
      <div class="representative-audio mt-2">
        <audio controls class="representative-audio-player" style="width: 100%;">
          <source src="${data.representative_audio_url || ''}" type="audio/wav">
          Your browser does not support the audio element.
        </audio>
      </div>
    </div>

    <div class="cluster-mappings mt-3">
      <h6>Call Type Mappings</h6>
      <ul class="mapping-list list-group"></ul>
    </div>
  `;

  $('.cluster-details').html(detailsHtml);

  // Render mappings
  if (data.mappings && data.mappings.length > 0) {
    const mappingList = $('.mapping-list');
    data.mappings.forEach((mapping) => {
      mappingList.append(`
        <li class="list-group-item d-flex justify-content-between align-items-center">
          <div>
            <strong>${escapeHtml(mapping.species_name)}</strong>: ${escapeHtml(mapping.call_name)}
          </div>
          <span class="badge badge-primary badge-pill">${(mapping.confidence * 100).toFixed(0)}%</span>
        </li>
      `);
    });
  } else {
    $('.mapping-list').html('<li class="list-group-item no-mappings">No mappings yet</li>');
  }
}

/**
 * Load cluster members from the API
 * @param {number} clusterId - Cluster ID to load members for
 */
export function loadClusterMembers(clusterId) {
  const $ = getJQuery();
  if (!$) {
    console.error('[ClusterExplorer] jQuery is not available. Cannot load cluster members.');
    return;
  }

  // Store for retry
  _lastClusterMembersRequest = clusterId;

  // Show the members panel
  $('.initial-members-message').addClass('d-none');
  $('.cluster-members').removeClass('d-none');

  // Determine column count based on scope
  const colCount = getIsProjectScope() ? 7 : 6;

  // Show a loading indicator
  $('#members-table-body').html(
    `<tr><td colspan="${colCount}" class="text-center"><div class="spinner-border text-primary"></div><p>Loading cluster members...</p></td></tr>`
  );

  // Load members from the API
  $.getJSON(
    buildUrl(API_ENDPOINTS.GET_CLUSTER_MEMBERS, { cluster_id: clusterId, limit: 50 }),
    function (data) {
      if (data.success) {
        renderClusterMembers(data);
      } else {
        const errorMsg = data.error || 'Failed to load cluster members';
        $('#members-table-body').html(
          `<tr><td colspan="${colCount}">
            <div class="alert alert-danger d-flex align-items-center mb-0">
              <div class="flex-grow-1">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${escapeHtml(errorMsg)}
                ${data.error_code ? `<small class="text-muted ms-2">(${escapeHtml(data.error_code)})</small>` : ''}
              </div>
              <button class="btn btn-sm btn-outline-danger ms-2 members-retry-btn">
                <i class="fas fa-redo"></i> Retry
              </button>
            </div>
          </td></tr>`
        );
        $('.members-retry-btn').on('click', () => loadClusterMembers(clusterId));
      }
    }
  ).fail(function (xhr) {
    const cols = getIsProjectScope() ? 7 : 6;
    const { message, errorCode } = parseErrorResponse(xhr, 'Failed to load cluster members');
    $('#members-table-body').html(
      `<tr><td colspan="${cols}">
        <div class="alert alert-danger d-flex align-items-center mb-0">
          <div class="flex-grow-1">
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${escapeHtml(message)}
            ${errorCode ? `<small class="text-muted ms-2">(${errorCode})</small>` : ''}
          </div>
          <button class="btn btn-sm btn-outline-danger ms-2 members-retry-btn">
            <i class="fas fa-redo"></i> Retry
          </button>
        </div>
      </td></tr>`
    );
    $('.members-retry-btn').on('click', () => loadClusterMembers(clusterId));
  });
}

/**
 * Render cluster members in the table
 * @param {Object} data - Members data from API
 */
function renderClusterMembers(data) {
  const $ = getJQuery();
  const members = data.members;
  const isProject = data.is_project_scope;
  const colCount = isProject ? 7 : 6;

  if (members && members.length > 0) {
    let html = '';

    members.forEach((member) => {
      const onset = member.onset.toFixed(3);
      const offset = member.offset.toFixed(3);
      const duration = member.duration.toFixed(3);
      const confidence = member.confidence ? member.confidence.toFixed(2) : 'N/A';

      html += '<tr>';
      html += `<td>${member.segment_id}</td>`;

      if (isProject) {
        html += `<td>${escapeHtml(member.recording_name || '')}</td>`;
      }

      html += `<td>${onset}</td>`;
      html += `<td>${offset}</td>`;
      html += `<td>${duration}</td>`;
      html += `<td>${confidence}</td>`;
      html += `<td>
        <button class="btn btn-sm btn-primary view-segment-btn" data-segment-id="${member.segment_id}" data-toggle="modal" data-target="#segmentDetailsModal">
          <i class="fa fa-eye"></i> View
        </button>
      </td>`;
      html += '</tr>';
    });

    if (data.has_more) {
      const colSpan = isProject ? 7 : 6;
      html += `
        <tr>
          <td colspan="${colSpan}" class="text-center">
            <em>Showing ${members.length} of ${data.total_size} segments. Export the cluster to see all segments.</em>
          </td>
        </tr>
      `;
    }

    $('#members-table-body').html(html);
  } else {
    $('#members-table-body').html(
      `<tr><td colspan="${colCount}" class="text-center">No segments in this cluster</td></tr>`
    );
  }
}

/**
 * Deselect the current cluster and reset UI
 */
export function deselectCluster() {
  const $ = getJQuery();
  if (!$) {
    console.error('[ClusterExplorer] jQuery is not available. Cannot deselect cluster.');
    return;
  }

  // Clear selection state
  setSelectedClusterId(null);
  setFocusedClusterIndex(-1);

  // Reset point styling
  const pointSize = parseInt($('#point-size').val()) || 8;
  const points = selectAll('.cluster-point');

  if (!points.empty()) {
    try {
      points
        .attr('stroke-width', 1)
        .attr('stroke', '#000')
        .attr('r', pointSize)
        .classed('focused', false);
    } catch (error) {
      console.error('[ClusterExplorer] Failed to reset cluster point styling:', error);
    }
  }

  // Hide the details panel
  $('.cluster-details').addClass('d-none');
  $('.initial-message').removeClass('d-none');

  // Hide members panel
  $('.cluster-members').addClass('d-none');
  $('.initial-members-message').removeClass('d-none');
}
