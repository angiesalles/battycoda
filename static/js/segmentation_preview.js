/**
 * Segmentation Preview Functionality
 * Handles the preview of segmentation results on a 10-second audio window
 */

document.addEventListener('DOMContentLoaded', function() {
    const previewBtn = document.getElementById('previewBtn');
    const previewResultsCard = document.getElementById('previewResultsCard');
    
    if (!previewBtn) return; // Exit if preview button not found
    
    previewBtn.addEventListener('click', function() {
        // Get form data
        const formData = new FormData();
        
        // Get selected algorithm
        const selectedAlgorithm = document.querySelector('input[name="algorithm"]:checked');
        if (!selectedAlgorithm) {
            alert('Please select an algorithm first.');
            return;
        }
        
        // Add form data
        formData.append('algorithm', selectedAlgorithm.value);
        formData.append('min_duration_ms', document.getElementById('min_duration_ms').value);
        formData.append('smooth_window', document.getElementById('smooth_window').value);
        formData.append('threshold_factor', document.getElementById('threshold_factor').value);
        formData.append('start_time', document.getElementById('preview_start_time').value);
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        
        // Disable button and show loading
        previewBtn.disabled = true;
        previewBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Previewing...';
        
        // Get preview URL from data attribute or construct it
        const recordingId = previewBtn.dataset.recordingId;
        const previewUrl = `/recordings/${recordingId}/auto-segment/preview/`;
        
        // Make request
        fetch(previewUrl, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayPreviewResults(data);
            } else {
                alert('Preview failed: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while previewing segmentation.');
        })
        .finally(() => {
            // Re-enable button
            previewBtn.disabled = false;
            previewBtn.innerHTML = '<i class="fas fa-search"></i> Preview Segmentation';
        });
    });
    
    function displayPreviewResults(data) {
        // Show the results card
        previewResultsCard.style.display = 'block';
        
        // Update statistics
        document.getElementById('previewAlgorithm').textContent = data.algorithm_name + ' (' + data.algorithm_type + ')';
        document.getElementById('previewTimeRange').textContent = data.preview_start.toFixed(1) + 's - ' + data.preview_end.toFixed(1) + 's';
        document.getElementById('previewSegmentCount').textContent = data.stats.total_segments;
        document.getElementById('previewDensity').textContent = data.stats.segment_density;
        document.getElementById('previewAvgDuration').textContent = data.stats.avg_duration;
        
        // Display segments list
        const segmentsList = document.getElementById('previewSegmentsList');
        if (data.segments.length === 0) {
            segmentsList.innerHTML = '<p class="text-muted">No segments detected in this time range.</p>';
        } else {
            let html = '<div class="list-group list-group-flush">';
            data.segments.forEach((segment, index) => {
                html += `
                    <div class="list-group-item py-2">
                        <small>
                            <strong>Segment ${index + 1}:</strong> 
                            ${segment.onset.toFixed(3)}s - ${segment.offset.toFixed(3)}s 
                            (${segment.duration.toFixed(3)}s)
                        </small>
                    </div>
                `;
            });
            html += '</div>';
            segmentsList.innerHTML = html;
        }
        
        // Scroll to results
        previewResultsCard.scrollIntoView({ behavior: 'smooth' });
    }
});