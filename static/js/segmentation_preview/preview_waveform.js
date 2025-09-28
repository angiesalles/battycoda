/**
 * Preview waveform visualization
 * Handles creating and drawing the waveform canvas with segment markers
 */

import { drawPreviewVisualization } from './visualization_controller.js';

export function initializePreviewWaveform(data) {
    console.log('Initializing preview waveform with data:', data);
    
    // Set up audio source if available
    const audioPlayer = document.getElementById('previewAudioPlayer');
    if (data.audio_url) {
        audioPlayer.src = data.audio_url;
        audioPlayer.style.display = 'block';
        console.log('Audio player set up with URL:', data.audio_url);
    } else {
        // Hide audio player if no audio URL
        audioPlayer.style.display = 'none';
        console.log('No audio URL provided');
    }
    
    // Create a simple waveform visualization with segment markers
    const container = document.getElementById('previewWaveformContainer');
    if (!container) {
        console.error('Preview waveform container not found');
        return;
    }
    
    console.log('Container found, creating waveform visualization...');
    
    try {
        // Clear the container
        container.innerHTML = '';
        
        // Create canvas for drawing the waveform visualization
        const canvas = document.createElement('canvas');
        canvas.id = 'previewWaveformCanvas';
        canvas.style.width = '100%';
        canvas.style.height = '200px';
        canvas.style.border = '1px solid #dee2e6';
        canvas.style.backgroundColor = '#f8f9fa';
        
        // Set actual canvas dimensions for proper drawing
        const rect = container.getBoundingClientRect();
        canvas.width = rect.width || 800;
        canvas.height = 200;
        
        console.log('Canvas dimensions set to:', canvas.width, 'x', canvas.height);
        
        container.appendChild(canvas);
        console.log('Canvas appended to container');
        
        // Draw visualization (spectrogram or waveform)
        drawPreviewVisualization(canvas, data);
        
        console.log('Preview waveform drawn with', data.segments.length, 'segments');
    } catch (error) {
        console.error('Failed to create preview waveform:', error);
        // Show fallback message
        container.innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle"></i>
                Waveform visualization not available. See segments list below.
            </div>
        `;
    }
}