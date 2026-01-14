/**
 * Cluster Mapping interface for BattyCoda
 *
 * Implements drag-and-drop mapping between unsupervised clusters and call types
 * Uses the ClusterMapping namespace from the module files
 */
(function(ClusterMapping) {
    'use strict';

    // Main initialization function - called after all module scripts are loaded
    function initClusterMapping() {
        console.log("initClusterMapping called");

        setTimeout(function() {
            console.log("Initializing mapping interface after delay");

            // Initialize drag and drop
            ClusterMapping.initializeDragAndDrop(
                ClusterMapping.loadClusterDetails,
                createMapping,
                ClusterMapping.setSelectedClusterId
            );

            // Initialize existing mappings
            ClusterMapping.initializeExistingMappings(
                existingMappings,
                addMappingToContainer,
                ClusterMapping.updateCallBadgeCount
            );

            // Set up cluster search
            $('#cluster-search').on('input', function() {
                ClusterMapping.filterClusters($(this).val());
            });

            // Set up cluster sorting
            $('#cluster-sort').on('change', function() {
                ClusterMapping.sortClusters($(this).val());
            });

            // Set up species filtering
            $('#species-filter').on('change', function() {
                ClusterMapping.filterSpecies($(this).val());
            });

            // Initialize cluster preview modal
            ClusterMapping.initializeClusterPreviewModal(createMapping, function() {
                return ClusterMapping.selectedClusterId;
            });
        }, 300);
    }

    // Wrapper functions to pass correct dependencies
    function createMapping(clusterId, callId) {
        ClusterMapping.createMapping(clusterId, callId, addMappingToContainer, ClusterMapping.updateCallBadgeCount);
    }

    function addMappingToContainer(clusterId, clusterNum, clusterLabel, clusterColor, callId, confidence, mappingId) {
        ClusterMapping.addMappingToContainer(
            clusterId, clusterNum, clusterLabel, clusterColor, callId, confidence, mappingId,
            ClusterMapping.updateMappingConfidence,
            deleteMapping,
            ClusterMapping.updateCallBadgeCount
        );
    }

    function deleteMapping(mappingId) {
        ClusterMapping.deleteMapping(mappingId, ClusterMapping.updateCallBadgeCount);
    }

    // Initialize when loaded
    initClusterMapping();

})(window.ClusterMapping = window.ClusterMapping || {});
