// Data loading and caching
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
