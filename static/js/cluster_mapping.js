/**
 * Cluster Mapping interface for BattyCoda
 *
 * Implements drag-and-drop mapping between unsupervised clusters and call types
 */

import { selectedClusterId, setSelectedClusterId, initializeExistingMappings, addMappingToContainer as addMappingToContainerBase, updateCallBadgeCount } from './cluster_mapping/initialization.js';
import { initializeDragAndDrop, createMapping as createMappingBase, updateMappingConfidence, deleteMapping as deleteMappingBase } from './cluster_mapping/drag_drop.js';
import { initializeClusterPreviewModal, loadClusterDetails } from './cluster_mapping/modal_handlers.js';
import { filterClusters, sortClusters, filterSpecies } from './cluster_mapping/filtering.js';

// Main initialization function - called after script is loaded
function initClusterMapping() {
    console.log("initClusterMapping called");

    setTimeout(function() {
        console.log("Initializing mapping interface after delay");

        // Initialize drag and drop
        initializeDragAndDrop(loadClusterDetails, createMapping, setSelectedClusterId);

        // Initialize existing mappings
        initializeExistingMappings(existingMappings, addMappingToContainer, updateCallBadgeCount);

        // Set up cluster search
        $('#cluster-search').on('input', function() {
            filterClusters($(this).val());
        });

        // Set up cluster sorting
        $('#cluster-sort').on('change', function() {
            sortClusters($(this).val());
        });

        // Set up species filtering
        $('#species-filter').on('change', function() {
            filterSpecies($(this).val());
        });

        // Initialize cluster preview modal
        initializeClusterPreviewModal(createMapping, selectedClusterId);
    }, 300);
}

// Wrapper functions to pass correct dependencies
function createMapping(clusterId, callId) {
    createMappingBase(clusterId, callId, addMappingToContainer, updateCallBadgeCount);
}

function addMappingToContainer(clusterId, clusterNum, clusterLabel, clusterColor, callId, confidence, mappingId) {
    addMappingToContainerBase(clusterId, clusterNum, clusterLabel, clusterColor, callId, confidence, mappingId, updateMappingConfidence, deleteMapping, updateCallBadgeCount);
}

function deleteMapping(mappingId) {
    deleteMappingBase(mappingId, updateCallBadgeCount);
}

// Initialize when loaded
initClusterMapping();
