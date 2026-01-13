// UI controls
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

/**
 * Initialize event handlers
 */
$(document).ready(function() {
    // Handle save button click
    $('#save-cluster-label').click(function() {
        saveClusterLabel();
    });

    // Handle segment view button click
    $(document).on('click', '.view-segment-btn', function() {
        const segmentId = $(this).data('segment-id');
        loadSegmentDetails(segmentId);
    });

    // Handle point size changes
    $('#point-size').on('input', function() {
        const size = parseInt($(this).val());
        d3.selectAll('.cluster-point')
            .attr('r', d => d.id === selectedClusterId ? size * 1.5 : size);
    });

    // Handle opacity changes
    $('#cluster-opacity').on('input', function() {
        const opacity = parseFloat($(this).val());
        d3.selectAll('.cluster-point')
            .attr('opacity', opacity);
    });
});
