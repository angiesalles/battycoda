/**
 * Main segmentation preview handler
 * Handles the preview button click and makes requests to the backend
 */

import { displayPreviewResults } from './preview_display.js';

export function initializePreviewHandler() {
    const previewBtn = document.getElementById('previewBtn');
    
    if (!previewBtn) return; // Exit if preview button not found
    
    function executePreview() {
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
            console.log('Preview response:', data);
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
    }
    
    // Set up refresh callback for auto-refresh when spectrogram is generating
    window.refreshPreviewCallback = executePreview;
    
    previewBtn.addEventListener('click', executePreview);
}