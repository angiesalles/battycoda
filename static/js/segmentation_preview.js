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
        
        // Initialize waveform player with segments
        initializePreviewWaveform(data);
        
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
    
    function initializePreviewWaveform(data) {
        console.log('Initializing preview waveform with data:', data);
        
        // Set up audio source if available
        const audioPlayer = document.getElementById('previewAudioPlayer');
        if (data.audio_url) {
            // Store base URL for dynamic updates
            window.baseAudioUrl = data.audio_url;
            updateAudioUrl();
            audioPlayer.style.display = 'block';
            console.log('Audio player set up with URL:', data.audio_url);
            
            // Set up audio controls
            setupAudioControls();
        } else {
            // Hide audio player if no audio URL
            audioPlayer.style.display = 'none';
            console.log('No audio URL provided');
        }
        
        // Set up view toggle functionality
        setupViewToggle(data);
        
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
            
            // Draw simple waveform representation
            drawPreviewWaveform(canvas, data);
            
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
    
    function drawPreviewWaveform(canvas, data) {
        console.log('Drawing preview waveform...');
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        console.log('Canvas context and dimensions:', ctx, width, height);
        
        // Clear the canvas
        ctx.fillStyle = '#f8f9fa';
        ctx.fillRect(0, 0, width, height);
        console.log('Canvas cleared');
        
        // Draw a simple timeline background instead of fake waveform
        const centerY = height / 2;
        
        // Draw main timeline
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(0, centerY);
        ctx.lineTo(width, centerY);
        ctx.stroke();
        
        // Draw time tick marks every second
        ctx.strokeStyle = '#666';
        ctx.lineWidth = 1;
        const timeRange = data.preview_end - data.preview_start;
        const secondsInRange = Math.ceil(timeRange);
        
        for (let i = 0; i <= secondsInRange; i++) {
            const x = (i / timeRange) * width;
            const tickHeight = (i % 5 === 0) ? 20 : 10; // Longer ticks every 5 seconds
            
            ctx.beginPath();
            ctx.moveTo(x, centerY - tickHeight);
            ctx.lineTo(x, centerY + tickHeight);
            ctx.stroke();
            
            // Add second labels
            if (i % 2 === 0 || timeRange <= 10) { // Show every 2 seconds, or every second if 10s or less
                ctx.fillStyle = '#666';
                ctx.font = '10px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(`${(data.preview_start + i).toFixed(0)}s`, x, centerY + 35);
            }
        }
        
        // Draw segment markers
        if (data.segments && data.segments.length > 0) {
            const timeRange = data.preview_end - data.preview_start;
            
            data.segments.forEach((segment, index) => {
                // Calculate positions relative to preview window
                const startX = ((segment.onset - data.preview_start) / timeRange) * width;
                const endX = ((segment.offset - data.preview_start) / timeRange) * width;
                
                // Only draw if segment is within the visible range
                if (startX >= 0 && startX <= width) {
                    // Draw segment boundary lines
                    ctx.strokeStyle = '#007bff';
                    ctx.lineWidth = 2;
                    
                    // Start line
                    ctx.beginPath();
                    ctx.moveTo(startX, 10);
                    ctx.lineTo(startX, height - 10);
                    ctx.stroke();
                    
                    // End line (if within bounds)
                    if (endX <= width) {
                        ctx.beginPath();
                        ctx.moveTo(endX, 10);
                        ctx.lineTo(endX, height - 10);
                        ctx.stroke();
                        
                        // Draw segment highlight
                        ctx.fillStyle = 'rgba(0, 123, 255, 0.2)';
                        ctx.fillRect(startX, 10, endX - startX, height - 20);
                    }
                    
                    // Draw segment label
                    ctx.fillStyle = '#007bff';
                    ctx.font = '12px Arial';
                    ctx.fillText(`S${index + 1}`, startX + 2, 25);
                }
            });
        }
    }
    
    // Audio control functions
    function setupAudioControls() {
        const pitchControl = document.getElementById('pitchControl');
        const volumeControl = document.getElementById('volumeControl');
        const pitchValue = document.getElementById('pitchValue');
        const volumeValue = document.getElementById('volumeValue');
        
        if (pitchControl && volumeControl) {
            pitchControl.addEventListener('input', function() {
                pitchValue.textContent = this.value + 'x';
                updateAudioUrl();
            });
            
            volumeControl.addEventListener('input', function() {
                volumeValue.textContent = this.value + 'x';
                updateAudioUrl();
            });
        }
    }
    
    function updateAudioUrl() {
        if (!window.baseAudioUrl) return;
        
        const pitchControl = document.getElementById('pitchControl');
        const volumeControl = document.getElementById('volumeControl');
        const audioPlayer = document.getElementById('previewAudioPlayer');
        
        if (pitchControl && volumeControl && audioPlayer) {
            const pitchValue = pitchControl.value;
            const volumeValue = volumeControl.value;
            
            // Add pitch_shift and loudness parameters to the base URL
            const url = new URL(window.baseAudioUrl, window.location.origin);
            url.searchParams.set('pitch_shift', pitchValue);
            url.searchParams.set('loudness', volumeValue);
            
            audioPlayer.src = url.toString();
            console.log('Updated audio URL:', url.toString());
        }
    }
});