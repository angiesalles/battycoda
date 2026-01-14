/**
 * Cluster Mapping Drag and Drop Module
 *
 * Handles drag and drop functionality for cluster-to-call mapping.
 */

import { setSelectedClusterId } from './state.js';
import { addMappingToContainer, updateCallBadgeCount } from './initialization.js';

/**
 * Initialize drag and drop functionality
 * @param {Function} loadClusterDetails - Function to load cluster details
 * @param {Function} createMappingFn - Function to create mapping
 */
export function initializeDragAndDrop(loadClusterDetails, createMappingFn) {
  const $ = window.jQuery;
  if (!$) return;

  console.log('Initializing drag and drop functionality');

  // Initialize draggable for cluster boxes
  $('.cluster-box').each(function () {
    $(this).attr('draggable', 'true');

    $(this).on('click', function () {
      console.log('Cluster box clicked');
      const clusterId = $(this).data('cluster-id');
      console.log('Cluster ID: ' + clusterId);

      $('.cluster-box').removeClass('selected');
      $(this).addClass('selected');

      setSelectedClusterId(clusterId);

      const modal = new window.bootstrap.Modal(document.getElementById('clusterPreviewModal'));
      modal.show();

      loadClusterDetails(clusterId);
    });

    $(this).on('dragstart', function (e) {
      console.log('Drag started');
      e.originalEvent.dataTransfer.setData('text/plain', $(this).data('cluster-id'));
      $(this).addClass('dragging');
    });

    $(this).on('dragend', function () {
      console.log('Drag ended');
      $(this).removeClass('dragging');
    });
  });

  console.log('Found ' + $('.cluster-box').length + ' cluster boxes');
  console.log('Found ' + $('.mapping-container').length + ' mapping containers');

  // Initialize drop areas
  $('.mapping-container').each(function () {
    const callId = $(this).data('call-id');
    console.log('Setting up drop for call ID: ' + callId);

    $(this).on('dragover', function (e) {
      e.preventDefault();
      console.log('Drag over call ID: ' + $(this).data('call-id'));
      $(this).addClass('drop-hover');
    });

    $(this).on('dragleave', function () {
      console.log('Drag left call ID: ' + $(this).data('call-id'));
      $(this).removeClass('drop-hover');
    });

    $(this).on('drop', function (e) {
      e.preventDefault();
      console.log('Drop on call ID: ' + $(this).data('call-id'));
      $(this).removeClass('drop-hover');

      const clusterId = e.originalEvent.dataTransfer.getData('text/plain');
      console.log('Dropped cluster ID: ' + clusterId);

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
  if (!$) return;

  console.log('Creating mapping between cluster ' + clusterId + ' and call ' + callId);

  const clusterBox = $(`.cluster-box[data-cluster-id="${clusterId}"]`);
  if (clusterBox.length === 0) {
    console.error('Could not find cluster box with ID ' + clusterId);
    return;
  }

  const clusterNum = clusterBox.data('cluster-num');
  const clusterLabel = clusterBox.find('h5').text().trim();
  const clusterColor = clusterBox.find('.color-indicator').css('background-color');

  console.log('Cluster details: ', {
    id: clusterId,
    num: clusterNum,
    label: clusterLabel,
    color: clusterColor,
  });

  const confidence = 0.7;
  const csrfToken = $('input[name=csrfmiddlewaretoken]').val();
  console.log('CSRF Token present: ' + (csrfToken ? 'Yes' : 'No'));

  $.ajax({
    url: '/clustering/create-mapping/',
    type: 'POST',
    data: {
      cluster_id: clusterId,
      call_id: callId,
      confidence: confidence,
      csrfmiddlewaretoken: csrfToken,
    },
    beforeSend: function (xhr) {
      xhr.setRequestHeader('X-CSRFToken', csrfToken);
    },
    success: function (data) {
      console.log('AJAX success response: ', data);

      if (data.status === 'success') {
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

        if (window.toastr) {
          window.toastr.success('Mapping created successfully');
        }
      } else {
        console.error('API returned error: ', data.message);
        if (window.toastr) {
          window.toastr.error('Failed to create mapping: ' + data.message);
        }
      }
    },
    error: function (xhr, status, error) {
      console.error('AJAX error: ', {
        status: status,
        error: error,
        response: xhr.responseText,
      });
      if (window.toastr) {
        window.toastr.error('Failed to create mapping. Please try again.');
      }
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
  if (!$ || !mappingId) return;

  const csrfToken = $('input[name=csrfmiddlewaretoken]').val();

  $.ajax({
    url: '/clustering/update-mapping-confidence/',
    type: 'POST',
    data: {
      mapping_id: mappingId,
      confidence: confidence,
      csrfmiddlewaretoken: csrfToken,
    },
    beforeSend: function (xhr) {
      xhr.setRequestHeader('X-CSRFToken', csrfToken);
    },
    success: function (data) {
      if (data.status !== 'success' && window.toastr) {
        window.toastr.error('Failed to update confidence: ' + data.message);
      }
    },
    error: function () {
      if (window.toastr) {
        window.toastr.error('Failed to update confidence. Please try again.');
      }
    },
  });
}

/**
 * Delete a mapping
 * @param {number} mappingId - Mapping ID to delete
 */
export function deleteMapping(mappingId) {
  const $ = window.jQuery;
  if (!$ || !mappingId) return;

  const csrfToken = $('input[name=csrfmiddlewaretoken]').val();

  $.ajax({
    url: '/clustering/delete-mapping/',
    type: 'POST',
    data: {
      mapping_id: mappingId,
      csrfmiddlewaretoken: csrfToken,
    },
    beforeSend: function (xhr) {
      xhr.setRequestHeader('X-CSRFToken', csrfToken);
    },
    success: function (data) {
      if (data.status === 'success') {
        updateCallBadgeCount(data.call_id, data.new_count);
      } else if (window.toastr) {
        window.toastr.error('Failed to delete mapping: ' + data.message);
      }
    },
    error: function () {
      if (window.toastr) {
        window.toastr.error('Failed to delete mapping. Please try again.');
      }
    },
  });
}
