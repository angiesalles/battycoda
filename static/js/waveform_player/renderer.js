/**
 * BattyCoda Waveform Player - Waveform Renderer
 * 
 * Responsible for drawing the waveform visualization
 */

import { CanvasInteractions } from './canvas_interactions.js';

export class WaveformRenderer {
    /**
     * Create a new WaveformRenderer
     * @param {Object} player - The parent WaveformPlayer instance
     */
    constructor(player) {
        this.player = player;
        this.canvasInteractions = new CanvasInteractions(player);
    }
    
    /**
     * Draw the waveform visualization
     */
    draw() {
        const player = this.player;
        if (!player.waveformData || !player.waveformContainer) {
            console.log('WaveformRenderer.draw(): Missing data or container', {
                hasData: !!player.waveformData,
                hasContainer: !!player.waveformContainer
            });
            return;
        }
        
        // Calculate visible duration for consistency
        const visibleDuration = player.duration / player.zoomLevel;
        const visibleStartTime = player.zoomOffset * player.duration;
        const visibleEndTime = Math.min(visibleStartTime + visibleDuration, player.duration);
        
        // Get or create persistent waveform canvas
        let canvas = player.waveformContainer.querySelector('canvas.waveform-canvas');
        if (!canvas) {
            canvas = document.createElement('canvas');
            canvas.id = `${player.containerId}-waveform-canvas`;
            canvas.className = 'waveform-canvas';
            canvas.style.position = 'absolute';
            canvas.style.top = '0';
            canvas.style.left = '0';
            canvas.style.width = '100%';
            canvas.style.height = '100%';
            player.waveformContainer.appendChild(canvas);
            
            // Setup event handlers only once when canvas is created
            console.log('WaveformRenderer.draw(): Setting up canvas event handlers');
            this.canvasInteractions.setupCanvasHandlers(canvas, canvas.width, visibleStartTime, visibleDuration);
        }
        
        // Update canvas dimensions (may have changed due to resize)
        canvas.width = player.waveformContainer.clientWidth;
        canvas.height = player.waveformContainer.clientHeight;
        
        console.log('WaveformRenderer.draw(): Canvas dimensions', {
            containerWidth: player.waveformContainer.clientWidth,
            containerHeight: player.waveformContainer.clientHeight,
            canvasWidth: canvas.width,
            canvasHeight: canvas.height
        });
        
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
        
        // Update interaction parameters for current view (always needed)
        this.canvasInteractions.updateViewParameters(width, visibleStartTime, visibleDuration);
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
     * Show the waveform view
     */
    show() {
        if (this.player.waveformContainer) {
            this.player.waveformContainer.style.display = 'block';
        }
    }
    
    /**
     * Hide the waveform view
     */
    hide() {
        if (this.player.waveformContainer) {
            // Remove only waveform canvas elements, but preserve spectrogram canvas
            const waveformCanvases = this.player.waveformContainer.querySelectorAll('canvas.waveform-canvas, canvas:not([class])');
            waveformCanvases.forEach(canvas => canvas.remove());
            this.player.waveformContainer.style.backgroundColor = 'transparent';
        }
    }
}
