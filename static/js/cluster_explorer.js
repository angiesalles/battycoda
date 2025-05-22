/**
 * Cluster Explorer visualization for BattyCoda
 * 
 * Implements interactive visualization and exploration of audio clusters
 * using D3.js
 */

// Define color scale for clusters
const colorScale = d3.scaleOrdinal(d3.schemeCategory10);

// Store the currently selected cluster
let selectedClusterId = null;

// Initialize visualization when the document is ready
$(document).ready(function() {
    // Initialize the visualization
    initializeVisualization();
    
    // Set up cluster label saving
    $('#save-cluster-label').on('click', saveClusterLabel);
    
    // Set up controls
    $('#point-size').on('input', updateVisualization);
    $('#cluster-opacity').on('input', updateVisualization);
    
    // Load segment details when a segment is clicked
    $(document).on('click', '.view-segment-btn', function() {
        const segmentId = $(this).data('segment-id');
        loadSegmentDetails(segmentId);
    });
});

/**
 * Initialize the cluster visualization
 */
function initializeVisualization() {
    // If there are no clusters, show a message
    if (clusters.length === 0) {
        $('#cluster-visualization').html('<div class="alert alert-warning">No clusters available for visualization</div>');
        return;
    }
    
    // Configure the visualization
    const width = $('#cluster-visualization').width();
    const height = 500;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    
    // Remove any existing SVG
    d3.select('#cluster-visualization svg').remove();
    
    // Create the SVG container
    const svg = d3.select('#cluster-visualization')
        .append('svg')
        .attr('width', width)
        .attr('height', height);
    
    // Create a container group for zooming
    const container = svg.append('g')
        .attr('class', 'container');
    
    // Add zoom behavior
    const zoom = d3.zoom()
        .scaleExtent([0.5, 5])
        .on('zoom', (event) => {
            container.attr('transform', event.transform);
        });
    
    svg.call(zoom);
    
    // Calculate the point size from the slider
    const pointSize = parseInt($('#point-size').val());
    const opacity = parseFloat($('#cluster-opacity').val());
    
    // Assign colors to clusters
    clusters.forEach((cluster, i) => {
        cluster.color = colorScale(i);
    });
    
    // Find the data range for x and y coordinates
    let xMin = d3.min(clusters, d => d.vis_x);
    let xMax = d3.max(clusters, d => d.vis_x);
    let yMin = d3.min(clusters, d => d.vis_y);
    let yMax = d3.max(clusters, d => d.vis_y);
    
    // Add some padding
    const padding = 0.1;
    const xRange = xMax - xMin;
    const yRange = yMax - yMin;
    xMin -= xRange * padding;
    xMax += xRange * padding;
    yMin -= yRange * padding;
    yMax += yRange * padding;
    
    // Create scales
    const xScale = d3.scaleLinear()
        .domain([xMin, xMax])
        .range([margin.left, width - margin.right]);
    
    const yScale = d3.scaleLinear()
        .domain([yMin, yMax])
        .range([height - margin.bottom, margin.top]);
    
    // Draw the cluster points
    container.selectAll('.cluster-point')
        .data(clusters)
        .enter()
        .append('circle')
        .attr('class', 'cluster-point')
        .attr('cx', d => xScale(d.vis_x))
        .attr('cy', d => yScale(d.vis_y))
        .attr('r', pointSize)
        .attr('fill', d => d.color)
        .attr('opacity', opacity)
        .attr('stroke', '#000')
        .attr('stroke-width', 1)
        .attr('cursor', 'pointer')
        .on('mouseover', function(event, d) {
            d3.select(this)
                .attr('stroke-width', 2)
                .attr('stroke', '#000');
            
            // Show a tooltip
            container.append('text')
                .attr('class', 'tooltip')
                .attr('x', xScale(d.vis_x) + 10)
                .attr('y', yScale(d.vis_y) - 10)
                .text(d.label || `Cluster ${d.cluster_id}`)
                .attr('fill', '#000')
                .attr('font-weight', 'bold');
        })
        .on('mouseout', function() {
            d3.select(this)
                .attr('stroke-width', 1);
            
            // Remove tooltip
            container.selectAll('.tooltip').remove();
        })
        .on('click', function(event, d) {
            // Select this cluster
            selectCluster(d.id);
        });
    
    // Add cluster labels for labeled clusters
    container.selectAll('.cluster-label')
        .data(clusters.filter(c => c.is_labeled))
        .enter()
        .append('text')
        .attr('class', 'cluster-label')
        .attr('x', d => xScale(d.vis_x) + 10)
        .attr('y', d => yScale(d.vis_y) + 3)
        .text(d => d.label)
        .attr('fill', '#000')
        .attr('font-size', '10px');
    
    // Create the legend
    createLegend(clusters);
}

/**
 * Create a legend for the cluster visualization
 */
function createLegend(clusters) {
    const legendDiv = $('.cluster-legend');
    legendDiv.empty();
    
    const legendHtml = $('<div class="row"></div>');
    
    clusters.forEach((cluster, i) => {
        const clusterLabel = cluster.label || `Cluster ${cluster.cluster_id}`;
        const legendItem = $(`
            <div class="col-md-3 mb-2">
                <div class="d-flex align-items-center">
                    <div style="width: 15px; height: 15px; background-color: ${cluster.color}; margin-right: 5px;"></div>
                    <small>${clusterLabel} (${cluster.size})</small>
                </div>
            </div>
        `);
        
        legendItem.on('click', () => {
            selectCluster(cluster.id);
        });
        
        legendHtml.append(legendItem);
    });
    
    legendDiv.append(legendHtml);
}

/**
 * Update the visualization based on control settings
 */
function updateVisualization() {
    const pointSize = parseInt($('#point-size').val());
    const opacity = parseFloat($('#cluster-opacity').val());
    
    d3.selectAll('.cluster-point')
        .attr('r', pointSize)
        .attr('opacity', opacity);
}

/**
 * Select a cluster and display its details
 */
function selectCluster(clusterId) {
    // Update the selection
    selectedClusterId = clusterId;
    
    // Highlight the selected cluster in the visualization
    d3.selectAll('.cluster-point')
        .attr('stroke-width', d => d.id === clusterId ? 3 : 1)
        .attr('stroke', d => d.id === clusterId ? '#fff' : '#000')
        .attr('r', d => d.id === clusterId ? parseInt($('#point-size').val()) * 1.5 : parseInt($('#point-size').val()));
    
    // Load the cluster details
    loadClusterDetails(clusterId);
    
    // Load cluster members
    loadClusterMembers(clusterId);
}

/**
 * Load cluster details from the API
 */
function loadClusterDetails(clusterId) {
    // Show the details panel
    $('.initial-message').addClass('d-none');
    $('.cluster-details').removeClass('d-none');
    
    // Show a loading indicator
    $('.cluster-details').html('<div class="text-center"><div class="spinner-border text-primary"></div><p>Loading cluster details...</p></div>');
    
    // Load the details from the API
    $.getJSON(`/clustering/get-cluster-data/?cluster_id=${clusterId}`, function(data) {
        if (data.status === 'success') {
            // Update the cluster details form
            $('.cluster-id-display').text(`Cluster ${data.cluster_id}`);
            $('#cluster-label').val(data.label || '');
            $('#cluster-description').val(data.description || '');
            
            // Update stats
            $('.cluster-size').text(data.size);
            $('.cluster-coherence').text(data.coherence ? data.coherence.toFixed(4) : 'N/A');
            
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
            
            // Update mappings
            if (data.mappings && data.mappings.length > 0) {
                $('.no-mappings').addClass('d-none');
                const mappingList = $('.mapping-list');
                mappingList.empty();
                
                data.mappings.forEach(mapping => {
                    mappingList.append(`
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${mapping.species_name}</strong>: ${mapping.call_name}
                            </div>
                            <span class="badge badge-primary badge-pill">${(mapping.confidence * 100).toFixed(0)}%</span>
                        </li>
                    `);
                });
            } else {
                $('.mapping-list').html('<li class="list-group-item no-mappings">No mappings yet</li>');
            }
        } else {
            // Show an error
            $('.cluster-details').html(`<div class="alert alert-danger">Failed to load cluster details: ${data.message}</div>`);
        }
    }).fail(function() {
        $('.cluster-details').html('<div class="alert alert-danger">Failed to load cluster details. Please try again.</div>');
    });
}

/**
 * Load cluster members from the API
 */
function loadClusterMembers(clusterId) {
    // Show the members panel
    $('.initial-members-message').addClass('d-none');
    $('.cluster-members').removeClass('d-none');
    
    // Show a loading indicator
    $('#members-table-body').html('<tr><td colspan="6" class="text-center"><div class="spinner-border text-primary"></div><p>Loading cluster members...</p></td></tr>');
    
    // Find the cluster in our data
    const cluster = clusters.find(c => c.id === clusterId);
    if (!cluster) return;
    
    // We would normally load this from an API, but for now we'll simulate it
    // In a real implementation, make an AJAX call to get the members
    
    // Simulate loading member data with a timeout
    setTimeout(() => {
        const maxMembers = 50; // Limit to avoid overwhelming the UI
        
        if (cluster.size > 0) {
            let html = '';
            // Generate sample segment data
            for (let i = 0; i < Math.min(cluster.size, maxMembers); i++) {
                const segmentId = 1000 + i;
                const onset = (Math.random() * 10).toFixed(2);
                const duration = (Math.random() * 0.5 + 0.1).toFixed(2);
                const offset = (parseFloat(onset) + parseFloat(duration)).toFixed(2);
                const confidence = (Math.random() * 0.3 + 0.7).toFixed(2);
                
                html += `
                    <tr>
                        <td>${segmentId}</td>
                        <td>${onset}</td>
                        <td>${offset}</td>
                        <td>${duration}</td>
                        <td>${confidence}</td>
                        <td>
                            <button class="btn btn-sm btn-primary view-segment-btn" data-segment-id="${segmentId}" data-toggle="modal" data-target="#segmentDetailsModal">
                                <i class="fa fa-eye"></i> View
                            </button>
                        </td>
                    </tr>
                `;
            }
            
            if (cluster.size > maxMembers) {
                html += `
                    <tr>
                        <td colspan="6" class="text-center">
                            <em>Showing ${maxMembers} of ${cluster.size} segments. Export the cluster to see all segments.</em>
                        </td>
                    </tr>
                `;
            }
            
            $('#members-table-body').html(html);
        } else {
            $('#members-table-body').html('<tr><td colspan="6" class="text-center">No segments in this cluster</td></tr>');
        }
    }, 500);
}

/**
 * Save the cluster label and description
 */
function saveClusterLabel() {
    if (!selectedClusterId) return;
    
    const label = $('#cluster-label').val();
    const description = $('#cluster-description').val();
    
    // Show a loading indicator
    const saveBtn = $('#save-cluster-label');
    const originalText = saveBtn.html();
    saveBtn.html('<span class="spinner-border spinner-border-sm"></span> Saving...');
    saveBtn.attr('disabled', true);
    
    // Make an AJAX request to update the label
    $.ajax({
        url: '/clustering/update-cluster-label/',
        type: 'POST',
        data: {
            cluster_id: selectedClusterId,
            label: label,
            description: description,
            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
        },
        success: function(data) {
            if (data.status === 'success') {
                // Update the local data
                const cluster = clusters.find(c => c.id === selectedClusterId);
                if (cluster) {
                    cluster.label = label;
                    cluster.description = description;
                    cluster.is_labeled = !!label;
                }
                
                // Update the visualization
                initializeVisualization();
                
                // Show a success message
                toastr.success('Cluster label updated successfully');
                
                // Select the cluster again to refresh the view
                selectCluster(selectedClusterId);
            } else {
                toastr.error(`Failed to update label: ${data.message}`);
            }
        },
        error: function() {
            toastr.error('Failed to update cluster label. Please try again.');
        },
        complete: function() {
            // Restore the button
            saveBtn.html(originalText);
            saveBtn.attr('disabled', false);
        }
    });
}

/**
 * Load segment details
 */
function loadSegmentDetails(segmentId) {
    // Show a loading indicator in the modal
    $('.segment-spectrogram').html('<div class="spinner-border text-primary"></div>');
    $('.segment-audio-player').attr('src', '');
    $('.segment-id').text('Loading...');
    $('.segment-recording').text('Loading...');
    $('.segment-onset').text('Loading...');
    $('.segment-offset').text('Loading...');
    $('.segment-duration').text('Loading...');
    
    // Load the segment details from the API
    $.getJSON(`/clustering/get-segment-data/?segment_id=${segmentId}`, function(data) {
        if (data.status === 'success') {
            // Update the modal
            $('.segment-id').text(data.segment_id);
            $('.segment-recording').text(data.recording_name);
            $('.segment-onset').text(data.onset.toFixed(4));
            $('.segment-offset').text(data.offset.toFixed(4));
            $('.segment-duration').text(data.duration.toFixed(4));
            
            // Update spectrogram
            $('.segment-spectrogram').html(`
                <img src="${data.spectrogram_url}" class="img-fluid" alt="Segment Spectrogram">
            `);
            
            // Update audio player
            $('.segment-audio-player').attr('src', data.audio_url);
        } else {
            // Show an error
            $('.segment-spectrogram').html(`<div class="alert alert-danger">Failed to load segment: ${data.message}</div>`);
        }
    }).fail(function() {
        $('.segment-spectrogram').html('<div class="alert alert-danger">Failed to load segment. Please try again.</div>');
    });
}