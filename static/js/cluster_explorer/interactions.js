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

    // Determine column count based on scope
    const colCount = (typeof isProjectScope !== 'undefined' && isProjectScope) ? 7 : 6;

    // Show a loading indicator
    $('#members-table-body').html(`<tr><td colspan="${colCount}" class="text-center"><div class="spinner-border text-primary"></div><p>Loading cluster members...</p></td></tr>`);

    // Load members from the API
    $.getJSON(`/clustering/get-cluster-members/?cluster_id=${clusterId}&limit=50`, function(data) {
        if (data.status === 'success') {
            const members = data.members;
            const isProject = data.is_project_scope;

            if (members && members.length > 0) {
                let html = '';

                members.forEach(member => {
                    const onset = member.onset.toFixed(3);
                    const offset = member.offset.toFixed(3);
                    const duration = member.duration.toFixed(3);
                    const confidence = member.confidence ? member.confidence.toFixed(2) : 'N/A';

                    html += '<tr>';
                    html += `<td>${member.segment_id}</td>`;

                    if (isProject) {
                        html += `<td>${member.recording_name || ''}</td>`;
                    }

                    html += `<td>${onset}</td>`;
                    html += `<td>${offset}</td>`;
                    html += `<td>${duration}</td>`;
                    html += `<td>${confidence}</td>`;
                    html += `<td>
                        <button class="btn btn-sm btn-primary view-segment-btn" data-segment-id="${member.segment_id}" data-toggle="modal" data-target="#segmentDetailsModal">
                            <i class="fa fa-eye"></i> View
                        </button>
                    </td>`;
                    html += '</tr>';
                });

                if (data.has_more) {
                    const colSpan = isProject ? 7 : 6;
                    html += `
                        <tr>
                            <td colspan="${colSpan}" class="text-center">
                                <em>Showing ${members.length} of ${data.total_size} segments. Export the cluster to see all segments.</em>
                            </td>
                        </tr>
                    `;
                }

                $('#members-table-body').html(html);
            } else {
                $('#members-table-body').html(`<tr><td colspan="${colCount}" class="text-center">No segments in this cluster</td></tr>`);
            }
        } else {
            $('#members-table-body').html(`<tr><td colspan="${colCount}" class="text-center text-danger">Failed to load members: ${data.message}</td></tr>`);
        }
    }).fail(function() {
        const colCount = (typeof isProjectScope !== 'undefined' && isProjectScope) ? 7 : 6;
        $('#members-table-body').html(`<tr><td colspan="${colCount}" class="text-center text-danger">Failed to load cluster members. Please try again.</td></tr>`);
    });
}
