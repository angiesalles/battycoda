/**
 * Cluster Mapping Initialization Module
 *
 * Functions for initializing mappings and managing mapping containers.
 */

/**
 * Initialize existing mappings on page load
 * @param {Array} existingMappings - Array of existing mapping data
 * @param {Function} addMappingToContainer - Function to add mapping to UI
 * @param {Function} updateCallBadgeCount - Function to update badge count
 */
export function initializeExistingMappings(
  existingMappings,
  addMappingToContainer,
  updateCallBadgeCount
) {
  const $ = window.jQuery;
  if (!$) return;

  existingMappings.forEach(function (mapping) {
    const clusterBox = $(`.cluster-box[data-cluster-id="${mapping.cluster_id}"]`);
    if (clusterBox.length === 0) return;

    const clusterNum = clusterBox.data('cluster-num');
    const clusterLabel = clusterBox.find('h5').text().trim();
    const clusterColor = clusterBox.find('.color-indicator').css('background-color');

    addMappingToContainer(
      mapping.cluster_id,
      clusterNum,
      clusterLabel,
      clusterColor,
      mapping.call_id,
      mapping.confidence,
      mapping.id
    );

    updateCallBadgeCount(mapping.call_id);
  });
}

/**
 * Add a mapping to the container
 * @param {number} clusterId - Cluster ID
 * @param {number} clusterNum - Cluster number
 * @param {string} clusterLabel - Cluster label
 * @param {string} clusterColor - Cluster color
 * @param {number} callId - Call type ID
 * @param {number} confidence - Confidence value (0-1)
 * @param {number} mappingId - Mapping ID (if existing)
 * @param {Function} updateMappingConfidence - Function to update confidence
 * @param {Function} deleteMapping - Function to delete mapping
 * @param {Function} updateCallBadgeCount - Function to update badge count
 */
export function addMappingToContainer(
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
) {
  const $ = window.jQuery;
  if (!$) return;

  const container = $(`.mapping-container[data-call-id="${callId}"]`);
  if (container.length === 0) return;

  container.find('.mapping-instruction').hide();

  const mappingElementId = `mapping-${clusterId}-${callId}`;

  if ($(`#${mappingElementId}`).length > 0) {
    $(`#${mappingElementId} .confidence-value`).text(Math.round(confidence * 100) + '%');
    $(`#${mappingElementId} .confidence-slider`).val(confidence);
    return;
  }

  const mappingElement = $(
    `<div id="${mappingElementId}" class="mapping-item" data-cluster-id="${clusterId}" data-call-id="${callId}" data-mapping-id="${mappingId || ''}">
            <div class="d-flex align-items-center">
                <span class="drag-handle"><i class="fa fa-grip-lines"></i></span>
                <span class="color-indicator" style="background-color: ${clusterColor};"></span>
                <span class="cluster-name">${clusterLabel || 'Cluster ' + clusterNum}</span>
            </div>
            <div class="mapping-controls d-flex align-items-center">
                <span class="confidence-value mr-2">${Math.round(confidence * 100)}%</span>
                <input type="range" class="confidence-slider" min="0" max="1" step="0.01" value="${confidence}">
                <button type="button" class="btn btn-sm btn-danger remove-mapping ml-2">
                    <i class="fa fa-times"></i>
                </button>
            </div>
        </div>`
  );

  container.find('.mapped-clusters').append(mappingElement);

  mappingElement.find('.confidence-slider').on('input', function () {
    const newConfidence = parseFloat($(this).val());
    mappingElement.find('.confidence-value').text(Math.round(newConfidence * 100) + '%');
    if (updateMappingConfidence) {
      updateMappingConfidence(mappingElement.data('mapping-id'), newConfidence);
    }
  });

  mappingElement.find('.remove-mapping').on('click', function () {
    if (deleteMapping) {
      deleteMapping(mappingElement.data('mapping-id'));
    }
    mappingElement.remove();

    if (container.find('.mapping-item').length === 0) {
      container.find('.mapping-instruction').show();
    }

    if (updateCallBadgeCount) {
      updateCallBadgeCount(callId);
    }
  });
}

/**
 * Update the badge count for a call
 * @param {number} callId - Call type ID
 * @param {number} [count] - Specific count to set (optional)
 */
export function updateCallBadgeCount(callId, count) {
  const $ = window.jQuery;
  if (!$) return;

  const badge = $(`.cluster-count-badge[data-call-id="${callId}"]`);
  if (badge.length === 0) return;

  if (count !== undefined) {
    badge.text(count);
    return;
  }

  const mappingCount = $(`.mapping-container[data-call-id="${callId}"] .mapping-item`).length;
  badge.text(mappingCount);
}
