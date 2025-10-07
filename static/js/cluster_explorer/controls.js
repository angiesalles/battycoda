// UI controls
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