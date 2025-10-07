/**
 * Modal and preview logic for cluster mapping
 */

/**
 * Initialize the cluster preview modal
 */
export function initializeClusterPreviewModal(createMapping, selectedClusterId) {
    $('#clusterPreviewModal').on('show.bs.modal', function() {
        $('.cluster-preview-id').text('Loading...');
        $('.cluster-preview-description').text('');
        $('.cluster-preview-size').text('');
        $('.cluster-preview-coherence').text('');
        $('.representative-spectrogram').html('<div class="spinner-border text-primary"></div>');
        $('.representative-audio-player').attr('src', '');

        const selectElement = $('#mapping-call-select');
        selectElement.empty();
        selectElement.append('<option value="">Select a call type to map to...</option>');

        $('.call-box').each(function() {
            const callId = $(this).find('.mapping-container').data('call-id');
            const callName = $(this).find('h6').text().trim();
            const speciesName = $(this).closest('.species-section').find('h5').text().trim();

            selectElement.append(`<option value="${callId}">${speciesName}: ${callName}</option>`);
        });
    });

    $('#create-mapping-btn').on('click', function() {
        const callId = $('#mapping-call-select').val();

        if (!callId || !selectedClusterId) {
            toastr.error('Please select a call type');
            return;
        }

        createMapping(selectedClusterId, callId);

        $('#clusterPreviewModal').modal('hide');
    });
}

/**
 * Load cluster details for the preview modal
 */
export function loadClusterDetails(clusterId) {
    const clusterBox = $(`.cluster-box[data-cluster-id="${clusterId}"]`);
    if (clusterBox.length === 0) return;

    const clusterNum = clusterBox.data('cluster-num');
    const clusterLabel = clusterBox.find('h5').text().trim();

    $('.cluster-preview-id').text(clusterLabel || `Cluster ${clusterNum}`);
    $('.cluster-preview-description').text(clusterBox.find('small:not(.text-muted)').text().trim());

    const sizeText = clusterBox.find('.text-muted:contains("Size")').text();
    const coherenceText = clusterBox.find('.text-muted:contains("Coherence")').text();

    if (sizeText) {
        $('.cluster-preview-size').text(sizeText.split(':')[1].trim());
    }

    if (coherenceText) {
        $('.cluster-preview-coherence').text(coherenceText.split(':')[1].trim());
    }

    $.getJSON(`/clustering/get-cluster-data/?cluster_id=${clusterId}`, function(data) {
        if (data.status === 'success') {
            $('.cluster-preview-id').text(data.label || `Cluster ${data.cluster_id}`);
            $('.cluster-preview-description').text(data.description || '');
            $('.cluster-preview-size').text(data.size);
            $('.cluster-preview-coherence').text(data.coherence ? data.coherence.toFixed(4) : 'N/A');

            if (data.representative_spectrogram_url) {
                $('.representative-spectrogram').html(`
                    <img src="${data.representative_spectrogram_url}" class="img-fluid" alt="Representative Spectrogram">
                `);

                if (data.representative_audio_url) {
                    $('.representative-audio-player').attr('src', data.representative_audio_url);
                }
            } else {
                $('.representative-spectrogram').html('<div class="alert alert-info">No representative sample available</div>');
                $('.representative-audio-player').attr('src', '');
            }
        } else {
            $('.representative-spectrogram').html(`<div class="alert alert-danger">Failed to load cluster details: ${data.message}</div>`);
        }
    }).fail(function() {
        $('.representative-spectrogram').html('<div class="alert alert-danger">Failed to load cluster details. Please try again.</div>');
    });
}
