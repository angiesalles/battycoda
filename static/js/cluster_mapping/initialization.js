/**
 * Initialization functions for cluster mapping interface
 */
(function(ClusterMapping) {
    'use strict';

    // Store the currently selected cluster
    ClusterMapping.selectedClusterId = null;

    ClusterMapping.setSelectedClusterId = function(id) {
        ClusterMapping.selectedClusterId = id;
    };

    /**
     * Initialize existing mappings on page load
     */
    ClusterMapping.initializeExistingMappings = function(existingMappings, addMappingToContainer, updateCallBadgeCount) {
        existingMappings.forEach(function(mapping) {
            var clusterBox = $('.cluster-box[data-cluster-id="' + mapping.cluster_id + '"]');
            if (clusterBox.length === 0) return;

            var clusterNum = clusterBox.data('cluster-num');
            var clusterLabel = clusterBox.find('h5').text().trim();
            var clusterColor = clusterBox.find('.color-indicator').css('background-color');

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
    };

    /**
     * Add a mapping to the container
     */
    ClusterMapping.addMappingToContainer = function(clusterId, clusterNum, clusterLabel, clusterColor, callId, confidence, mappingId, updateMappingConfidence, deleteMapping, updateCallBadgeCount) {
        var container = $('.mapping-container[data-call-id="' + callId + '"]');
        if (container.length === 0) return;

        container.find('.mapping-instruction').hide();

        var mappingElementId = 'mapping-' + clusterId + '-' + callId;

        if ($('#' + mappingElementId).length > 0) {
            $('#' + mappingElementId + ' .confidence-value').text(Math.round(confidence * 100) + '%');
            $('#' + mappingElementId + ' .confidence-slider').val(confidence);
            return;
        }

        var mappingElement = $(
            '<div id="' + mappingElementId + '" class="mapping-item" data-cluster-id="' + clusterId + '" data-call-id="' + callId + '" data-mapping-id="' + (mappingId || '') + '">' +
                '<div class="d-flex align-items-center">' +
                    '<span class="drag-handle"><i class="fa fa-grip-lines"></i></span>' +
                    '<span class="color-indicator" style="background-color: ' + clusterColor + ';"></span>' +
                    '<span class="cluster-name">' + (clusterLabel || 'Cluster ' + clusterNum) + '</span>' +
                '</div>' +
                '<div class="mapping-controls d-flex align-items-center">' +
                    '<span class="confidence-value mr-2">' + Math.round(confidence * 100) + '%</span>' +
                    '<input type="range" class="confidence-slider" min="0" max="1" step="0.01" value="' + confidence + '">' +
                    '<button type="button" class="btn btn-sm btn-danger remove-mapping ml-2">' +
                        '<i class="fa fa-times"></i>' +
                    '</button>' +
                '</div>' +
            '</div>'
        );

        container.find('.mapped-clusters').append(mappingElement);

        mappingElement.find('.confidence-slider').on('input', function() {
            var newConfidence = parseFloat($(this).val());
            mappingElement.find('.confidence-value').text(Math.round(newConfidence * 100) + '%');
            updateMappingConfidence(mappingElement.data('mapping-id'), newConfidence);
        });

        mappingElement.find('.remove-mapping').on('click', function() {
            deleteMapping(mappingElement.data('mapping-id'));
            mappingElement.remove();

            if (container.find('.mapping-item').length === 0) {
                container.find('.mapping-instruction').show();
            }

            updateCallBadgeCount(callId);
        });
    };

    /**
     * Update the badge count for a call
     */
    ClusterMapping.updateCallBadgeCount = function(callId, count) {
        var badge = $('.cluster-count-badge[data-call-id="' + callId + '"]');
        if (badge.length === 0) return;

        if (count !== undefined) {
            badge.text(count);
            return;
        }

        var mappingCount = $('.mapping-container[data-call-id="' + callId + '"] .mapping-item').length;
        badge.text(mappingCount);
    };

})(window.ClusterMapping = window.ClusterMapping || {});
