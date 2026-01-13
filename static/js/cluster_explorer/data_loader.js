// Data loading and caching
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
                if (typeof toastr !== 'undefined') {
                    toastr.success('Cluster label updated successfully');
                } else {
                    alert('Cluster label updated successfully');
                }

                // Select the cluster again to refresh the view
                selectCluster(selectedClusterId);
            } else {
                if (typeof toastr !== 'undefined') {
                    toastr.error(`Failed to update label: ${data.message}`);
                } else {
                    alert(`Failed to update label: ${data.message}`);
                }
            }
        },
        error: function() {
            if (typeof toastr !== 'undefined') {
                toastr.error('Failed to update cluster label. Please try again.');
            } else {
                alert('Failed to update cluster label. Please try again.');
            }
        },
        complete: function() {
            // Restore the button
            saveBtn.html(originalText);
            saveBtn.attr('disabled', false);
        }
    });
}
