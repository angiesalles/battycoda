/**
 * Preview results display handler
 * Handles updating the UI with preview results and statistics
 */

import { initializePreviewWaveform } from './preview_waveform.js';

export function displayPreviewResults(data) {
    const previewResultsCard = document.getElementById('previewResultsCard');
    
    // Show the results card
    previewResultsCard.style.display = 'block';
    
    // Update statistics
    document.getElementById('previewAlgorithm').textContent = data.algorithm_name + ' (' + data.algorithm_type + ')';
    document.getElementById('previewTimeRange').textContent = data.preview_start.toFixed(1) + 's - ' + data.preview_end.toFixed(1) + 's';
    document.getElementById('previewSegmentCount').textContent = data.stats.total_segments;
    document.getElementById('previewDensity').textContent = data.stats.segment_density;
    document.getElementById('previewAvgDuration').textContent = data.stats.avg_duration;
    
    // Store preview data globally for toggle functionality
    window.previewData = data;
    
    // Initialize waveform player with segments
    initializePreviewWaveform(data);
    
    // Setup toggle functionality
    setupVisualizationToggle(data);
    
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

function setupVisualizationToggle(data) {
    const spectrogramToggle = document.getElementById('spectrogramToggle');
    const waveformToggle = document.getElementById('waveformToggle');
    const visualizationTitle = document.getElementById('visualizationTitle');
    
    if (!spectrogramToggle || !waveformToggle) {
        console.warn('Toggle buttons not found');
        return;
    }
    
    // Remove any existing event listeners
    spectrogramToggle.replaceWith(spectrogramToggle.cloneNode(true));
    waveformToggle.replaceWith(waveformToggle.cloneNode(true));
    
    // Get fresh references after cloning
    const newSpectrogramToggle = document.getElementById('spectrogramToggle');
    const newWaveformToggle = document.getElementById('waveformToggle');
    
    // Add event listeners
    newSpectrogramToggle.addEventListener('click', function() {
        if (!this.classList.contains('active')) {
            // Switch to spectrogram
            this.classList.add('active');
            newWaveformToggle.classList.remove('active');
            visualizationTitle.textContent = 'Spectrogram';
            
            // Redraw with spectrogram
            window.currentVisualizationType = 'spectrogram';
            initializePreviewWaveform(data);
        }
    });
    
    newWaveformToggle.addEventListener('click', function() {
        if (!this.classList.contains('active')) {
            // Switch to waveform
            this.classList.add('active');
            newSpectrogramToggle.classList.remove('active');
            visualizationTitle.textContent = 'Waveform';
            
            // Redraw with waveform
            window.currentVisualizationType = 'waveform';
            initializePreviewWaveform(data);
        }
    });
    
    // Set initial state
    window.currentVisualizationType = 'spectrogram';
}