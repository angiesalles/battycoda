// User interaction handlers
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
