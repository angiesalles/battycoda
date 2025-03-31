/**
 * BattyCoda Waveform Player - Waveform Renderer
 * 
 * Responsible for drawing the waveform visualization
 */

export class WaveformRenderer {
    /**
     * Create a new WaveformRenderer
     * @param {Object} player - The parent WaveformPlayer instance
     */
    constructor(player) {
        this.player = player;
    }
    
    /**
     * Draw the waveform visualization
     */
    draw() {
        const player = this.player;
        if (!player.waveformData || !player.waveformContainer) return;
        
        // Calculate visible duration for consistency
        const visibleDuration = player.duration / player.zoomLevel;
        const visibleStartTime = player.zoomOffset * player.duration;
        const visibleEndTime = Math.min(visibleStartTime + visibleDuration, player.duration);
        
        // Create canvas
        player.waveformContainer.innerHTML = '';
        const canvas = document.createElement('canvas');
        canvas.width = player.waveformContainer.clientWidth;
        canvas.height = player.waveformContainer.clientHeight;
        player.waveformContainer.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = '#1a1a1a';
        ctx.fillRect(0, 0, width, height);
        
        // Calculate visible range based on zoom
        const visibleDataPoints = player.waveformData.length / player.zoomLevel;
        const startIdx = Math.floor(player.zoomOffset * player.waveformData.length);
        const endIdx = Math.min(startIdx + visibleDataPoints, player.waveformData.length);
        
        // Draw waveform shape
        this.drawWaveformShape(ctx, width, height, startIdx, endIdx);
        
        // Draw selection if allowed
        if (player.allowSelection) {
            this.drawSelection(ctx, width, height, visibleStartTime, visibleDuration);
        }
        
        // Draw cursor at current time
        this.drawPlaybackCursor(ctx, width, height, visibleStartTime, visibleDuration);
        
        // Add click event listener to canvas for seeking
        this.addCanvasClickHandler(canvas, width, visibleStartTime, visibleDuration);
    }
    
    /**
     * Draw the waveform shape on the canvas
     */
    drawWaveformShape(ctx, width, height, startIdx, endIdx) {
        const player = this.player;
        
        // Create a gradient for the waveform
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, '#1976D2');    // Top
        gradient.addColorStop(0.5, '#42A5F5');  // Center
        gradient.addColorStop(1, '#1976D2');    // Bottom
        
        // Draw the positive part of the waveform (top half)
        ctx.beginPath();
        ctx.lineWidth = 1.5;
        
        // Start at the center line
        ctx.moveTo(0, height/2);
        
        for (let i = 0; i < width; i++) {
            const dataIdx = startIdx + Math.floor(i * (endIdx - startIdx) / width);
            if (dataIdx < player.waveformData.length) {
                // Find the value, ensure it's not below zero for the positive part
                const value = Math.max(0, player.waveformData[dataIdx]);
                // Map from -1...1 to height...0
                const y = height/2 - (value * height/2);
                ctx.lineTo(i, y);
            }
        }
        
        // Back to center line
        ctx.lineTo(width, height/2);
        
        // Close and fill the positive half
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();
        
        // Draw the negative part of the waveform (bottom half)
        ctx.beginPath();
        ctx.lineWidth = 1.5;
        
        // Start at the center line
        ctx.moveTo(0, height/2);
        
        for (let i = 0; i < width; i++) {
            const dataIdx = startIdx + Math.floor(i * (endIdx - startIdx) / width);
            if (dataIdx < player.waveformData.length) {
                // Find the value, ensure it's not above zero for the negative part
                const value = Math.min(0, player.waveformData[dataIdx]);
                // Map from -1...1 to height/2...height
                const y = height/2 + (Math.abs(value) * height/2);
                ctx.lineTo(i, y);
            }
        }
        
        // Back to center line
        ctx.lineTo(width, height/2);
        
        // Close and fill the negative half
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();
        
        // Add a line for the waveform outline
        ctx.beginPath();
        ctx.lineWidth = 1.0;
        
        // Go through all points to draw a continuous outline
        let firstPoint = true;
        
        for (let i = 0; i < width; i++) {
            const dataIdx = startIdx + Math.floor(i * (endIdx - startIdx) / width);
            if (dataIdx < player.waveformData.length) {
                const value = player.waveformData[dataIdx];
                // Map from -1...1 to height...0
                const y = height/2 - (value * height/2);
                
                if (firstPoint) {
                    ctx.moveTo(i, y);
                    firstPoint = false;
                } else {
                    ctx.lineTo(i, y);
                }
            }
        }
        
        // Draw the outline in a slightly darker blue
        ctx.strokeStyle = 'rgba(21, 101, 192, 0.7)';
        ctx.stroke();
        
        // Draw centerline
        ctx.beginPath();
        ctx.strokeStyle = '#6c757d';
        ctx.lineWidth = 0.5;
        ctx.moveTo(0, height / 2);
        ctx.lineTo(width, height / 2);
        ctx.stroke();
    }
    
    /**
     * Draw the selection area on the waveform
     */
    drawSelection(ctx, width, height, visibleStartTime, visibleDuration) {
        const player = this.player;
        
        // Handle case where both start and end are set
        if (player.selectionStart !== null && player.selectionEnd !== null) {
            // Convert selection times to x coordinates relative to visible window
            const startX = ((player.selectionStart - visibleStartTime) / visibleDuration) * width;
            const endX = ((player.selectionEnd - visibleStartTime) / visibleDuration) * width;
            
            // Check if any part of the selection is visible
            if ((startX >= 0 && startX <= width) || 
                (endX >= 0 && endX <= width) || 
                (startX < 0 && endX > width)) {
                
                // Calculate visible portion of selection
                const visibleStartX = Math.max(0, startX);
                const visibleEndX = Math.min(width, endX);
                
                // Only draw if there's a visible portion
                if (visibleEndX > visibleStartX) {
                    // Fill selection area
                    ctx.fillStyle = 'rgba(255, 193, 7, 0.3)';
                    ctx.fillRect(visibleStartX, 0, visibleEndX - visibleStartX, height);
                    
                    // Draw selection boundaries if visible
                    // Start boundary
                    if (startX >= 0 && startX <= width) {
                        ctx.beginPath();
                        ctx.strokeStyle = '#ffc107'; // Amber color 
                        ctx.lineWidth = 3; // Thicker line
                        ctx.moveTo(startX, 0);
                        ctx.lineTo(startX, height);
                        ctx.stroke();
                        
                        // Add a small highlight area
                        ctx.fillStyle = 'rgba(255, 193, 7, 0.2)'; // Semi-transparent amber
                        ctx.fillRect(startX-2, 0, 4, height);
                    }
                    
                    // End boundary
                    if (endX >= 0 && endX <= width) {
                        ctx.beginPath();
                        ctx.strokeStyle = '#dc3545'; // Bootstrap danger red
                        ctx.lineWidth = 3; // Thicker line
                        ctx.moveTo(endX, 0);
                        ctx.lineTo(endX, height);
                        ctx.stroke();
                        
                        // Add a small highlight area
                        ctx.fillStyle = 'rgba(220, 53, 69, 0.2)'; // Semi-transparent red
                        ctx.fillRect(endX-2, 0, 4, height);
                    }
                }
            }
        } 
        // Handle case where only start is set
        else if (player.selectionStart !== null) {
            const startX = ((player.selectionStart - visibleStartTime) / visibleDuration) * width;
            
            // Check if the start point is visible
            if (startX >= 0 && startX <= width) {
                // Draw a more prominent start boundary
                ctx.beginPath();
                ctx.strokeStyle = '#ffc107'; // Amber color
                ctx.lineWidth = 3; // Thicker line
                ctx.moveTo(startX, 0);
                ctx.lineTo(startX, height);
                ctx.stroke();
                
                // Add a small highlight area
                ctx.fillStyle = 'rgba(255, 193, 7, 0.2)'; // Semi-transparent amber
                ctx.fillRect(startX-2, 0, 4, height);
            }
        }
        // Handle case where only end is set
        else if (player.selectionEnd !== null) {
            const endX = ((player.selectionEnd - visibleStartTime) / visibleDuration) * width;
            
            // Check if the end point is visible
            if (endX >= 0 && endX <= width) {
                // Draw a more prominent end boundary
                ctx.beginPath();
                ctx.strokeStyle = '#dc3545'; // Bootstrap danger red 
                ctx.lineWidth = 3; // Thicker line
                ctx.moveTo(endX, 0);
                ctx.lineTo(endX, height);
                ctx.stroke();
                
                // Add a small highlight area
                ctx.fillStyle = 'rgba(220, 53, 69, 0.2)'; // Semi-transparent red
                ctx.fillRect(endX-2, 0, 4, height);
            }
        }
    }
    
    /**
     * Draw the playback cursor on the waveform
     */
    drawPlaybackCursor(ctx, width, height, visibleStartTime, visibleDuration) {
        const player = this.player;
        
        // Calculate cursor position relative to visible window
        const cursorX = ((player.currentTime - visibleStartTime) / visibleDuration) * width;

        // Draw cursor
        ctx.beginPath();
        ctx.strokeStyle = '#fd7e14';
        ctx.lineWidth = 2;
        ctx.moveTo(cursorX, 0);
        ctx.lineTo(cursorX, height);
        ctx.stroke();
    }
    
    /**
     * Add click and mousedown handlers to the waveform canvas for seeking
     */
    addCanvasClickHandler(canvas, width, visibleStartTime, visibleDuration) {
        const player = this.player;
        
        // Function to update the player position based on mouse position
        const updatePlayerPosition = (e) => {
            const rect = canvas.getBoundingClientRect();
            const x = Math.max(0, Math.min(width, e.clientX - rect.left));
            
            // Calculate time position considering zoom
            const visibleProportion = x / width;
            
            // Calculate the actual time position
            const timePos = visibleStartTime + (visibleProportion * visibleDuration);
            
            // Store current visible window before changing position
            const currentVisibleStart = visibleStartTime;
            const currentVisibleEnd = visibleStartTime + visibleDuration;
            
            // Check if the new position is outside the current visible area
            const positionOutsideView = timePos < currentVisibleStart || timePos > currentVisibleEnd;
            
            // Set current time
            player.currentTime = Math.max(0, Math.min(player.duration, timePos));
            player.audioPlayer.currentTime = player.currentTime;
            player.updateTimeDisplay();
            
            // Only adjust the view if the position is completely outside visible area
            if (positionOutsideView && player.zoomLevel > 1) {
                // Calculate new offset to make the position barely visible
                // but without centering it
                const visibleDurationRatio = visibleDuration / player.duration;
                
                if (timePos < currentVisibleStart) {
                    // If clicking to the left of visible area, show position at 25% from left edge
                    player.zoomOffset = Math.max(0, timePos / player.duration - 0.25 * visibleDurationRatio);
                } else if (timePos > currentVisibleEnd) {
                    // If clicking to the right of visible area, show position at 25% from right edge
                    player.zoomOffset = Math.min(
                        1 - visibleDurationRatio,
                        timePos / player.duration - 0.75 * visibleDurationRatio
                    );
                }
            }
            
            // Update the view
            player.drawWaveform();
            player.drawTimeline();
        };
        
        // Both click and mousedown do the same thing: immediately update position
        canvas.addEventListener('click', updatePlayerPosition);
        canvas.addEventListener('mousedown', updatePlayerPosition);
        
        // Set cursor to indicate it's clickable
        canvas.style.cursor = 'pointer';
    }
}
