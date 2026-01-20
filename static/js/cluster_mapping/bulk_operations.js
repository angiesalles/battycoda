/**
 * Bulk Operations for Cluster Mapping
 *
 * Handles multi-selection and bulk mapping operations for clusters.
 */

import {
  getSelectedClusterIds,
  clearClusterSelection,
  toggleClusterSelection,
  getApiUrls,
} from './state.js';
import { addMappingToContainer, updateCallBadgeCount } from './initialization.js';
import { updateMappingConfidence, deleteMapping } from './drag_drop.js';
import { getCsrfToken } from '../utils/page-data.js';
import { parseErrorResponse, showToast } from '../utils/error-handling.js';

// Module-level flag for initialization
let isInitialized = false;

/**
 * Initialize bulk operations functionality
 */
export function initializeBulkOperations() {
  const $ = window.jQuery;
  if (!$) {
    console.error('[ClusterMapping] jQuery not available. Cannot initialize bulk operations.');
    return;
  }

  if (isInitialized) {
    console.warn('[ClusterMapping] Bulk operations already initialized.');
    return;
  }

  // Initialize bulk action toolbar handlers
  $('#bulk-map-btn').off('click').on('click', handleBulkMapClick);
  $('#clear-selection-btn').off('click').on('click', handleClearSelection);

  // Update cluster box click handlers to support multi-select
  updateClusterBoxHandlers();

  isInitialized = true;
  console.debug('[ClusterMapping] Bulk operations initialized.');
}

/**
 * Update cluster box click handlers to support Ctrl+click for multi-select
 */
function updateClusterBoxHandlers() {
  const $ = window.jQuery;

  // Add Ctrl+click handler for multi-select
  $(document).off('click.bulkSelect', '.cluster-box').on('click.bulkSelect', '.cluster-box', function (e) {
    // Only handle Ctrl+click for multi-select
    if (!e.ctrlKey && !e.metaKey) {
      return; // Let the normal click handler handle single-click
    }

    e.preventDefault();
    e.stopPropagation();

    const clusterId = $(this).data('cluster-id');
    const isNowSelected = toggleClusterSelection(clusterId);

    // Update visual state
    if (isNowSelected) {
      $(this).addClass('multi-selected');
    } else {
      $(this).removeClass('multi-selected');
    }

    // Update toolbar visibility
    updateBulkToolbar();
  });
}

/**
 * Update the bulk action toolbar visibility and count
 */
export function updateBulkToolbar() {
  const $ = window.jQuery;
  const selectedIds = getSelectedClusterIds();
  const count = selectedIds.length;

  if (count > 0) {
    $('#bulk-action-toolbar').removeClass('d-none');
    $('#bulk-selected-count').text(`${count} cluster${count > 1 ? 's' : ''} selected`);
  } else {
    $('#bulk-action-toolbar').addClass('d-none');
  }
}

/**
 * Handle bulk map button click - opens modal to select call type
 */
function handleBulkMapClick() {
  const selectedIds = getSelectedClusterIds();

  if (selectedIds.length === 0) {
    showToast('No clusters selected', 'warning');
    return;
  }

  // Show the bulk mapping modal
  const modal = new window.bootstrap.Modal(document.getElementById('bulkMappingModal'));
  modal.show();
}

/**
 * Handle clear selection button click
 */
function handleClearSelection() {
  const _$ = window.jQuery;

  clearClusterSelection();
  $('.cluster-box').removeClass('multi-selected');
  updateBulkToolbar();
}

/**
 * Create bulk mappings for selected clusters
 * @param {number} callId - Call type ID to map to
 * @param {number} confidence - Confidence value (0-1)
 */
export function bulkCreateMappings(callId, confidence = 0.7) {
  const $ = window.jQuery;
  const clusterIds = getSelectedClusterIds();

  if (clusterIds.length === 0) {
    showToast('No clusters selected', 'warning');
    return Promise.resolve({ success: false, error: 'No clusters selected' });
  }

  const apiUrls = getApiUrls();
  const csrfToken = getCsrfToken();

  return new Promise((resolve) => {
    $.ajax({
      url: apiUrls.bulkCreateMappings,
      type: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
      contentType: 'application/json',
      data: JSON.stringify({
        cluster_ids: clusterIds,
        call_id: callId,
        confidence: confidence,
      }),
      success: function (data) {
        if (data.success) {
          const createdCount = data.created_count || 0;
          const errorCount = data.errors ? data.errors.length : 0;

          // Add mapping items to the UI for each created mapping
          if (data.mappings) {
            data.mappings.forEach((mapping) => {
              const clusterBox = $(`.cluster-box[data-cluster-id="${mapping.cluster_id}"]`);
              if (clusterBox.length > 0) {
                const clusterNum = clusterBox.data('cluster-num');
                const clusterLabel = clusterBox.find('h5').text().trim();
                const clusterColor = clusterBox.find('.color-indicator').css('background-color');

                addMappingToContainer(
                  mapping.cluster_id,
                  clusterNum,
                  clusterLabel,
                  clusterColor,
                  callId,
                  confidence,
                  mapping.mapping_id,
                  updateMappingConfidence,
                  deleteMapping,
                  updateCallBadgeCount
                );
              }
            });
          }

          // Update the call badge count
          if (data.new_count !== undefined) {
            updateCallBadgeCount(callId, data.new_count);
          }

          // Show success/partial success message
          if (errorCount > 0) {
            showToast(`Created ${createdCount} mappings. ${errorCount} failed.`, 'warning');
          } else {
            showToast(`Created ${createdCount} mappings successfully`, 'success');
          }

          // Clear selection
          handleClearSelection();

          // Close modal if open
          const modalEl = document.getElementById('bulkMappingModal');
          if (modalEl) {
            const modal = window.bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
          }

          resolve(data);
        } else {
          const errorMsg = data.error || 'Unknown error';
          showToast(`Bulk mapping failed: ${errorMsg}`, 'error');
          resolve(data);
        }
      },
      error: function (xhr) {
        const { message, errorCode } = parseErrorResponse(xhr, 'Failed to create bulk mappings');
        const codeStr = errorCode ? ` (${errorCode})` : '';
        showToast(`${message}${codeStr}`, 'error');
        resolve({ success: false, error: message });
      },
    });
  });
}

/**
 * Clean up bulk operations (for re-initialization)
 */
export function cleanupBulkOperations() {
  const $ = window.jQuery;
  if ($) {
    $('#bulk-map-btn').off('click');
    $('#clear-selection-btn').off('click');
    $(document).off('click.bulkSelect', '.cluster-box');
  }
  clearClusterSelection();
  isInitialized = false;
}
