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
        
        // Use new hidden recording approach
        const recordingId = previewBtn.dataset.recordingId;
        const createPreviewUrl = `/recordings/${recordingId}/create-preview/`;
        
        // Prepare form data for hidden recording creation
        const previewFormData = new FormData();
        previewFormData.append('start_time', document.getElementById('preview_start_time').value);
        previewFormData.append('duration', '10.0');  // Fixed 10-second duration
        previewFormData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        
        // Add segmentation parameters to the request
        previewFormData.append('algorithm', selectedAlgorithm.value);
        previewFormData.append('min_duration_ms', document.getElementById('min_duration_ms').value);
        previewFormData.append('smooth_window', document.getElementById('smooth_window').value);
        previewFormData.append('threshold_factor', document.getElementById('threshold_factor').value);
        
        // Add bandpass filter parameters
        const lowFreq = document.getElementById('low_freq');
        const highFreq = document.getElementById('high_freq');
        if (lowFreq && lowFreq.value) previewFormData.append('low_freq', lowFreq.value);
        if (highFreq && highFreq.value) previewFormData.append('high_freq', highFreq.value);
        
        // Add all segmentation parameters to pass through URL fragment or store temporarily
        const segmentationParams = {
            algorithm: selectedAlgorithm.value,
            min_duration_ms: document.getElementById('min_duration_ms').value,
            smooth_window: document.getElementById('smooth_window').value,
            threshold_factor: document.getElementById('threshold_factor').value,
            low_freq: document.getElementById('low_freq')?.value || '',
            high_freq: document.getElementById('high_freq')?.value || ''
        };
        
        // Make request to create hidden recording
        fetch(createPreviewUrl, {
            method: 'POST',
            body: previewFormData
        })
        .then(response => response.json())
        .then(data => {
            console.log('Preview recording response:', data);
            if (data.success) {
                // Store segmentation parameters in sessionStorage for the preview page
                sessionStorage.setItem('segmentationPreviewParams', JSON.stringify(segmentationParams));
                
                // Open the segmentation detail view for the hidden recording
                const previewWindow = window.open(data.preview_url, '_blank');
                previewWindow.focus();
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