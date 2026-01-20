/**
 * Cluster Mapping Drag and Drop Module
 *
 * Handles drag and drop functionality for cluster-to-call mapping.
 */

import { setSelectedClusterId, getApiUrls } from './state.js';
import { addMappingToContainer, updateCallBadgeCount } from './initialization.js';
import { getCsrfToken } from '../utils/page-data.js';
import { parseErrorResponse, showToast } from '../utils/error-handling.js';

/**
 * Initialize drag and drop functionality
 * @param {Function} loadClusterDetails - Function to load cluster details
 * @param {Function} createMappingFn - Function to create mapping
 */
export function initializeDragAndDrop(loadClusterDetails, createMappingFn) {
  const $ = window.jQuery;
  if (!$) {
    console.error('[ClusterMapping] jQuery is not available. Cannot initialize drag and drop.');
    return;
  }

  // Clean up existing handlers to prevent duplicates on re-initialization
  $('.cluster-box').off('click dragstart dragend');
  $('.mapping-container').off('dragover dragleave drop');

  // Initialize draggable for cluster boxes
  $('.cluster-box').each(function () {
    $(this).attr('draggable', 'true');

    $(this).on('click', function () {
      const clusterId = $(this).data('cluster-id');

      $('.cluster-box').removeClass('selected');
      $(this).addClass('selected');

      setSelectedClusterId(clusterId);

      const modal = new window.bootstrap.Modal(document.getElementById('clusterPreviewModal'));
      modal.show();

      loadClusterDetails(clusterId);
    });

    $(this).on('dragstart', function (e) {
      e.originalEvent.dataTransfer.setData('text/plain', $(this).data('cluster-id'));
      $(this).addClass('dragging');
    });

    $(this).on('dragend', function () {
      $(this).removeClass('dragging');
    });
  });

  // Initialize drop areas
  $('.mapping-container').each(function () {
    const callId = $(this).data('call-id');

    $(this).on('dragover', function (e) {
      e.preventDefault();
      $(this).addClass('drop-hover');
    });

    $(this).on('dragleave', function () {
      $(this).removeClass('drop-hover');
    });

    $(this).on('drop', function (e) {
      e.preventDefault();
      $(this).removeClass('drop-hover');

      const clusterId = e.originalEvent.dataTransfer.getData('text/plain');

      createMappingFn(clusterId, callId);
    });
  });
}

/**
 * Create a mapping between a cluster and a call type
 * @param {number} clusterId - Cluster ID
 * @param {number} callId - Call type ID
 */
export function createMapping(clusterId, callId) {
  const $ = window.jQuery;
  if (!$) {
    console.error('[ClusterMapping] jQuery is not available. Cannot create mapping.');
    return;
  }

  const clusterBox = $(`.cluster-box[data-cluster-id="${clusterId}"]`);
  if (clusterBox.length === 0) {
    console.error('Could not find cluster box with ID ' + clusterId);
    return;
  }

  const clusterNum = clusterBox.data('cluster-num');
  const clusterLabel = clusterBox.find('h5').text().trim();
  const clusterColor = clusterBox.find('.color-indicator').css('background-color');

  const confidence = 0.7;
  const csrfToken = getCsrfToken();
  const apiUrls = getApiUrls();

  $.ajax({
    url: apiUrls.createMapping,
    type: 'POST',
    headers: { 'X-CSRFToken': csrfToken },
    data: {
      cluster_id: clusterId,
      call_id: callId,
      confidence: confidence,
    },
    success: function (data) {
      if (data.success) {
        addMappingToContainer(
          clusterId,
          clusterNum,
          clusterLabel,
          clusterColor,
          callId,
          confidence,
          data.mapping_id,
          updateMappingConfidence,
          deleteMapping,
          updateCallBadgeCount
        );

        updateCallBadgeCount(callId, data.new_count);

        showToast('Mapping created successfully', 'success');
      } else {
        console.error('[ClusterMapping] API returned error: ', data.error);
        const errorMsg = data.error || 'Unknown error creating mapping';
        const codeStr = data.error_code ? ` (${data.error_code})` : '';
        showToast(`Failed to create mapping: ${errorMsg}${codeStr}`, 'error');
      }
    },
    error: function (xhr) {
      const { message, errorCode } = parseErrorResponse(xhr, 'Failed to create mapping');
      console.error('[ClusterMapping] AJAX error:', message, errorCode);
      const codeStr = errorCode ? ` (${errorCode})` : '';
      showToast(`${message}${codeStr}`, 'error');
    },
  });
}

/**
 * Update a mapping's confidence
 * @param {number} mappingId - Mapping ID
 * @param {number} confidence - New confidence value
 */
export function updateMappingConfidence(mappingId, confidence) {
  const $ = window.jQuery;
  if (!$) {
    console.error('[ClusterMapping] jQuery is not available. Cannot update mapping confidence.');
    return;
  }
  if (!mappingId) {
    console.warn('[ClusterMapping] No mapping ID provided. Cannot update mapping confidence.');
    return;
  }

  const apiUrls = getApiUrls();
  $.ajax({
    url: apiUrls.updateMappingConfidence,
    type: 'POST',
    headers: { 'X-CSRFToken': getCsrfToken() },
    data: {
      mapping_id: mappingId,
      confidence: confidence,
    },
    success: function (data) {
      if (!data.success) {
        const errorMsg = data.error || 'Unknown error';
        showToast(`Failed to update confidence: ${errorMsg}`, 'error');
      }
    },
    error: function (xhr) {
      const { message } = parseErrorResponse(xhr, 'Failed to update confidence');
      showToast(message, 'error');
    },
  });
}

/**
 * Delete a mapping
 * @param {number} mappingId - Mapping ID to delete
 */
export function deleteMapping(mappingId) {
  const $ = window.jQuery;
  if (!$) {
    console.error('[ClusterMapping] jQuery is not available. Cannot delete mapping.');
    return;
  }
  if (!mappingId) {
    console.warn('[ClusterMapping] No mapping ID provided. Cannot delete mapping.');
    return;
  }

  const apiUrls = getApiUrls();
  $.ajax({
    url: apiUrls.deleteMapping,
    type: 'POST',
    headers: { 'X-CSRFToken': getCsrfToken() },
    data: {
      mapping_id: mappingId,
    },
    success: function (data) {
      if (data.success) {
        updateCallBadgeCount(data.call_id, data.new_count);
        showToast('Mapping deleted', 'success');
      } else {
        const errorMsg = data.error || 'Unknown error';
        showToast(`Failed to delete mapping: ${errorMsg}`, 'error');
      }
    },
    error: function (xhr) {
      const { message } = parseErrorResponse(xhr, 'Failed to delete mapping');
      showToast(message, 'error');
    },
  });
}
