/**
 * Cluster Mapping interface for BattyCoda
 * 
 * Implements drag-and-drop mapping between unsupervised clusters and call types
 */

// Store the currently selected cluster
let selectedClusterId = null;

// Main initialization function - called after script is loaded
function initClusterMapping() {
    console.log("initClusterMapping called");
    
    // Add a slight delay to ensure all elements are properly loaded
    setTimeout(function() {
        console.log("Initializing mapping interface after delay");
        
        // Initialize cluster boxes for drag and drop
        initializeDragAndDrop();
        
        // Initialize existing mappings
        initializeExistingMappings();
        
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
        initializeClusterPreviewModal();
    }, 300);
}

// Initialize when loaded
initClusterMapping();

/**
 * Initialize drag and drop functionality
 */
function initializeDragAndDrop() {
    console.log("Initializing drag and drop functionality");
    
    // Initialize draggable for cluster boxes
    $('.cluster-box').each(function() {
        // Add draggable behavior
        $(this).attr('draggable', 'true');
        
        // Add click handler
        $(this).on('click', function() {
            console.log("Cluster box clicked");
            // Get the cluster ID
            const clusterId = $(this).data('cluster-id');
            console.log("Cluster ID: " + clusterId);
            
            // Highlight the selected cluster
            $('.cluster-box').removeClass('selected');
            $(this).addClass('selected');
            
            // Store the selected cluster ID
            selectedClusterId = clusterId;
            
            // Show the preview modal
            $('#clusterPreviewModal').modal('show');
            
            // Load the cluster details
            loadClusterDetails(clusterId);
        });
        
        // Add drag handlers
        $(this).on('dragstart', function(e) {
            console.log("Drag started");
            e.originalEvent.dataTransfer.setData('text/plain', $(this).data('cluster-id'));
            $(this).addClass('dragging');
        });
        
        $(this).on('dragend', function() {
            console.log("Drag ended");
            $(this).removeClass('dragging');
        });
    });
    
    console.log("Found " + $('.cluster-box').length + " cluster boxes");
    console.log("Found " + $('.mapping-container').length + " mapping containers");
    
    // Initialize drop areas
    $('.mapping-container').each(function() {
        const callId = $(this).data('call-id');
        console.log("Setting up drop for call ID: " + callId);
        
        // Add drop handlers
        $(this).on('dragover', function(e) {
            e.preventDefault();
            console.log("Drag over call ID: " + $(this).data('call-id'));
            $(this).addClass('drop-hover');
        });
        
        $(this).on('dragleave', function() {
            console.log("Drag left call ID: " + $(this).data('call-id'));
            $(this).removeClass('drop-hover');
        });
        
        $(this).on('drop', function(e) {
            e.preventDefault();
            console.log("Drop on call ID: " + $(this).data('call-id'));
            $(this).removeClass('drop-hover');
            
            // Get the cluster ID from the dragged element
            const clusterId = e.originalEvent.dataTransfer.getData('text/plain');
            console.log("Dropped cluster ID: " + clusterId);
            
            // Create the mapping
            createMapping(clusterId, callId);
        });
    });
}

/**
 * Initialize existing mappings on page load
 */
function initializeExistingMappings() {
    // Initialize existing mappings
    existingMappings.forEach(mapping => {
        // Find the cluster
        const clusterBox = $(`.cluster-box[data-cluster-id="${mapping.cluster_id}"]`);
        if (clusterBox.length === 0) return;
        
        // Get cluster info
        const clusterNum = clusterBox.data('cluster-num');
        const clusterLabel = clusterBox.find('h5').text().trim();
        const clusterColor = clusterBox.find('.color-indicator').css('background-color');
        
        // Add the mapping to the appropriate container
        addMappingToContainer(
            mapping.cluster_id, 
            clusterNum,
            clusterLabel, 
            clusterColor, 
            mapping.call_id, 
            mapping.confidence,
            mapping.id
        );
        
        // Update the call badge count
        updateCallBadgeCount(mapping.call_id);
    });
}

/**
 * Add a mapping to the container
 */
function addMappingToContainer(clusterId, clusterNum, clusterLabel, clusterColor, callId, confidence, mappingId) {
    // Find the container
    const container = $(`.mapping-container[data-call-id="${callId}"]`);
    if (container.length === 0) return;
    
    // Hide the instruction text
    container.find('.mapping-instruction').hide();
    
    // Create a unique ID for the mapping element
    const mappingElementId = `mapping-${clusterId}-${callId}`;
    
    // Check if this mapping already exists
    if ($(`#${mappingElementId}`).length > 0) {
        // Update the confidence instead
        $(`#${mappingElementId} .confidence-value`).text(`${Math.round(confidence * 100)}%`);
        $(`#${mappingElementId} .confidence-slider`).val(confidence);
        return;
    }
    
    // Create the mapping element
    const mappingElement = $(`
        <div id="${mappingElementId}" class="mapping-item" data-cluster-id="${clusterId}" data-call-id="${callId}" data-mapping-id="${mappingId || ''}">
            <div class="d-flex align-items-center">
                <span class="drag-handle"><i class="fa fa-grip-lines"></i></span>
                <span class="color-indicator" style="background-color: ${clusterColor};"></span>
                <span class="cluster-name">${clusterLabel || `Cluster ${clusterNum}`}</span>
            </div>
            <div class="mapping-controls d-flex align-items-center">
                <span class="confidence-value mr-2">${Math.round(confidence * 100)}%</span>
                <input type="range" class="confidence-slider" min="0" max="1" step="0.01" value="${confidence}">
                <button type="button" class="btn btn-sm btn-danger remove-mapping ml-2">
                    <i class="fa fa-times"></i>
                </button>
            </div>
        </div>
    `);
    
    // Add the mapping element to the container
    container.find('.mapped-clusters').append(mappingElement);
    
    // Add event handlers
    mappingElement.find('.confidence-slider').on('input', function() {
        const newConfidence = parseFloat($(this).val());
        mappingElement.find('.confidence-value').text(`${Math.round(newConfidence * 100)}%`);
        
        // Update the mapping in the database
        updateMappingConfidence(mappingElement.data('mapping-id'), newConfidence);
    });
    
    mappingElement.find('.remove-mapping').on('click', function() {
        // Delete the mapping
        deleteMapping(mappingElement.data('mapping-id'));
        
        // Remove the element
        mappingElement.remove();
        
        // If this was the last mapping, show the instruction text
        if (container.find('.mapping-item').length === 0) {
            container.find('.mapping-instruction').show();
        }
        
        // Update the call badge count
        updateCallBadgeCount(callId);
    });
}

/**
 * Create a mapping between a cluster and a call type
 */
function createMapping(clusterId, callId) {
    console.log("Creating mapping between cluster " + clusterId + " and call " + callId);
    
    // Get the cluster info
    const clusterBox = $(`.cluster-box[data-cluster-id="${clusterId}"]`);
    if (clusterBox.length === 0) {
        console.error("Could not find cluster box with ID " + clusterId);
        return;
    }
    
    const clusterNum = clusterBox.data('cluster-num');
    const clusterLabel = clusterBox.find('h5').text().trim();
    const clusterColor = clusterBox.find('.color-indicator').css('background-color');
    
    console.log("Cluster details: ", {
        id: clusterId,
        num: clusterNum,
        label: clusterLabel,
        color: clusterColor
    });
    
    // Default confidence
    const confidence = 0.7;
    
    // Verify CSRF token
    const csrfToken = $('input[name=csrfmiddlewaretoken]').val();
    console.log("CSRF Token present: " + (csrfToken ? "Yes" : "No"));
    
    // Make an AJAX request to create the mapping
    $.ajax({
        url: '/clustering/create-mapping/',
        type: 'POST',
        data: {
            cluster_id: clusterId,
            call_id: callId,
            confidence: confidence,
            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
        },
        beforeSend: function(xhr, settings) {
            // Include CSRF token in the request headers as a fallback
            if (!this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", $('input[name=csrfmiddlewaretoken]').val());
            }
        },
        success: function(data) {
            console.log("AJAX success response: ", data);
            
            if (data.status === 'success') {
                // Add the mapping to the container
                addMappingToContainer(
                    clusterId, 
                    clusterNum,
                    clusterLabel, 
                    clusterColor, 
                    callId, 
                    confidence,
                    data.mapping_id
                );
                
                // Update the call badge count
                updateCallBadgeCount(callId, data.new_count);
                
                // Show a success message
                toastr.success('Mapping created successfully');
            } else {
                console.error("API returned error: ", data.message);
                toastr.error(`Failed to create mapping: ${data.message}`);
            }
        },
        error: function(xhr, status, error) {
            console.error("AJAX error: ", {
                status: status,
                error: error,
                response: xhr.responseText
            });
            toastr.error('Failed to create mapping. Please try again.');
        }
    });
}

/**
 * Update a mapping's confidence
 */
function updateMappingConfidence(mappingId, confidence) {
    // Don't update if there's no mapping ID (not yet saved)
    if (!mappingId) return;
    
    // Make an AJAX request to update the mapping
    $.ajax({
        url: '/clustering/update-mapping-confidence/',
        type: 'POST',
        data: {
            mapping_id: mappingId,
            confidence: confidence,
            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
        },
        beforeSend: function(xhr, settings) {
            // Include CSRF token in the request headers as a fallback
            if (!this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", $('input[name=csrfmiddlewaretoken]').val());
            }
        },
        success: function(data) {
            if (data.status === 'success') {
                // Success quietly
            } else {
                toastr.error(`Failed to update confidence: ${data.message}`);
            }
        },
        error: function() {
            toastr.error('Failed to update confidence. Please try again.');
        }
    });
}

/**
 * Delete a mapping
 */
function deleteMapping(mappingId) {
    // Don't delete if there's no mapping ID (not yet saved)
    if (!mappingId) return;
    
    // Make an AJAX request to delete the mapping
    $.ajax({
        url: '/clustering/delete-cluster-mapping/',
        type: 'POST',
        data: {
            mapping_id: mappingId,
            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
        },
        beforeSend: function(xhr, settings) {
            // Include CSRF token in the request headers as a fallback
            if (!this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", $('input[name=csrfmiddlewaretoken]').val());
            }
        },
        success: function(data) {
            if (data.status === 'success') {
                // Success quietly
                updateCallBadgeCount(data.call_id, data.new_count);
            } else {
                toastr.error(`Failed to delete mapping: ${data.message}`);
            }
        },
        error: function() {
            toastr.error('Failed to delete mapping. Please try again.');
        }
    });
}

/**
 * Update the badge count for a call
 */
function updateCallBadgeCount(callId, count) {
    // Find the badge
    const badge = $(`.cluster-count-badge[data-call-id="${callId}"]`);
    if (badge.length === 0) return;
    
    // If count is provided, use it
    if (count !== undefined) {
        badge.text(count);
        return;
    }
    
    // Otherwise, count the mappings
    const mappingCount = $(`.mapping-container[data-call-id="${callId}"] .mapping-item`).length;
    badge.text(mappingCount);
}

/**
 * Filter clusters based on search text
 */
function filterClusters(searchText) {
    // Convert to lowercase for case-insensitive search
    searchText = searchText.toLowerCase();
    
    // Show/hide clusters based on search
    $('.cluster-box').each(function() {
        const clusterText = $(this).text().toLowerCase();
        if (clusterText.includes(searchText)) {
            $(this).show();
        } else {
            $(this).hide();
        }
    });
}

/**
 * Sort clusters based on the selected option
 */
function sortClusters(sortBy) {
    // Get all clusters
    const clusters = $('.cluster-box').toArray();
    
    // Sort the clusters
    clusters.sort((a, b) => {
        const $a = $(a);
        const $b = $(b);
        
        switch (sortBy) {
            case 'id':
                return $a.data('cluster-num') - $b.data('cluster-num');
            case 'size':
                const sizeA = parseInt($a.find('.text-muted:contains("Size")').text().split(':')[1]);
                const sizeB = parseInt($b.find('.text-muted:contains("Size")').text().split(':')[1]);
                return sizeB - sizeA; // Largest first
            case 'coherence':
                const cohA = parseFloat($a.find('.text-muted:contains("Coherence")').text().split(':')[1]) || 0;
                const cohB = parseFloat($b.find('.text-muted:contains("Coherence")').text().split(':')[1]) || 0;
                return cohB - cohA; // Highest first
            case 'label':
                const labelA = $a.find('h5').text().trim();
                const labelB = $b.find('h5').text().trim();
                return labelA.localeCompare(labelB);
            default:
                return 0;
        }
    });
    
    // Reattach the sorted clusters
    const container = $('#clusters-list');
    clusters.forEach(cluster => {
        container.append(cluster);
    });
}

/**
 * Filter species sections based on the selected species
 */
function filterSpecies(speciesId) {
    if (speciesId === 'all') {
        // Show all species
        $('.species-section').show();
    } else {
        // Show only the selected species
        $('.species-section').hide();
        $(`.species-section[data-species-id="${speciesId}"]`).show();
    }
}

/**
 * Initialize the cluster preview modal
 */
function initializeClusterPreviewModal() {
    $('#clusterPreviewModal').on('show.bs.modal', function() {
        // Clear the form
        $('.cluster-preview-id').text('Loading...');
        $('.cluster-preview-description').text('');
        $('.cluster-preview-size').text('');
        $('.cluster-preview-coherence').text('');
        $('.representative-spectrogram').html('<div class="spinner-border text-primary"></div>');
        $('.representative-audio-player').attr('src', '');
        
        // Clear and populate the mapping call select
        const selectElement = $('#mapping-call-select');
        selectElement.empty();
        selectElement.append('<option value="">Select a call type to map to...</option>');
        
        // Add all call options
        $('.call-box').each(function() {
            const callId = $(this).find('.mapping-container').data('call-id');
            const callName = $(this).find('h6').text().trim();
            const speciesName = $(this).closest('.species-section').find('h5').text().trim();
            
            selectElement.append(`<option value="${callId}">${speciesName}: ${callName}</option>`);
        });
    });
    
    // Add click handler for the create mapping button
    $('#create-mapping-btn').on('click', function() {
        const callId = $('#mapping-call-select').val();
        
        if (!callId || !selectedClusterId) {
            toastr.error('Please select a call type');
            return;
        }
        
        // Create the mapping
        createMapping(selectedClusterId, callId);
        
        // Close the modal
        $('#clusterPreviewModal').modal('hide');
    });
}

/**
 * Load cluster details for the preview modal
 */
function loadClusterDetails(clusterId) {
    // Get the cluster info
    const clusterBox = $(`.cluster-box[data-cluster-id="${clusterId}"]`);
    if (clusterBox.length === 0) return;
    
    const clusterNum = clusterBox.data('cluster-num');
    const clusterLabel = clusterBox.find('h5').text().trim();
    
    // Update the modal with initial info
    $('.cluster-preview-id').text(clusterLabel || `Cluster ${clusterNum}`);
    $('.cluster-preview-description').text(clusterBox.find('small:not(.text-muted)').text().trim());
    
    // Get size and coherence
    const sizeText = clusterBox.find('.text-muted:contains("Size")').text();
    const coherenceText = clusterBox.find('.text-muted:contains("Coherence")').text();
    
    if (sizeText) {
        $('.cluster-preview-size').text(sizeText.split(':')[1].trim());
    }
    
    if (coherenceText) {
        $('.cluster-preview-coherence').text(coherenceText.split(':')[1].trim());
    }
    
    // Load the details from the API
    $.getJSON(`/clustering/get-cluster-data/?cluster_id=${clusterId}`, function(data) {
        if (data.status === 'success') {
            // Update details from API
            $('.cluster-preview-id').text(data.label || `Cluster ${data.cluster_id}`);
            $('.cluster-preview-description').text(data.description || '');
            $('.cluster-preview-size').text(data.size);
            $('.cluster-preview-coherence').text(data.coherence ? data.coherence.toFixed(4) : 'N/A');
            
            // Update representative sample
            if (data.representative_spectrogram_url) {
                $('.representative-spectrogram').html(`
                    <img src="${data.representative_spectrogram_url}" class="img-fluid" alt="Representative Spectrogram">
                `);
                
                // Update audio player
                if (data.representative_audio_url) {
                    $('.representative-audio-player').attr('src', data.representative_audio_url);
                }
            } else {
                $('.representative-spectrogram').html('<div class="alert alert-info">No representative sample available</div>');
                $('.representative-audio-player').attr('src', '');
            }
        } else {
            // Show an error
            $('.representative-spectrogram').html(`<div class="alert alert-danger">Failed to load cluster details: ${data.message}</div>`);
        }
    }).fail(function() {
        $('.representative-spectrogram').html('<div class="alert alert-danger">Failed to load cluster details. Please try again.</div>');
    });
}