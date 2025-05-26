/**
 * BattyCoda Spectrogram Renderer
 * 
 * Handles rendering of spectrogram visualization with zoom, scroll, and selection
 */

export class SpectrogramRenderer {
    /**
     * Create a new SpectrogramRenderer
     * @param {WaveformPlayer} player - The parent player instance
     */
    constructor(player) {
        this.player = player;
        this.canvas = null;
        this.ctx = null;
        this.spectrogramImage = null;
        this.imageLoaded = false;
        this.imageWidth = 0;
        this.imageHeight = 0;
        
        // Cache for performance
        this.lastZoomLevel = null;
        this.lastZoomOffset = null;
        this.lastWidth = null;
        this.lastHeight = null;
    }
    
    /**
     * Initialize the spectrogram renderer
     * @param {string} spectrogramUrl - URL of the spectrogram image
     */
    initialize(spectrogramUrl) {
        if (!this.player.container || !spectrogramUrl) return;
        
        // Create canvas element
        this.createCanvas();
        
        // Load spectrogram image
        this.loadSpectrogramImage(spectrogramUrl);
    }
    
    /**
     * Create and setup the canvas element
     */
    createCanvas() {
        // Remove existing canvas if present
        const existingCanvas = this.player.container.querySelector('.spectrogram-canvas');
        if (existingCanvas) {
            existingCanvas.remove();
        }
        
        // Create new canvas
        this.canvas = document.createElement('canvas');
        this.canvas.id = `${this.player.containerId}-spectrogram-canvas`;
        this.canvas.className = 'spectrogram-canvas';
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.cursor = 'crosshair';
        this.canvas.style.display = 'none'; // Initially hidden
        
        // Add to container
        this.player.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    /**
     * Load the spectrogram image
     * @param {string} spectrogramUrl - URL of the spectrogram image
     */
    loadSpectrogramImage(spectrogramUrl) {
        this.spectrogramImage = new Image();
        this.spectrogramImage.onload = () => {
            this.imageLoaded = true;
            this.imageWidth = this.spectrogramImage.width;
            this.imageHeight = this.spectrogramImage.height;
            this.resize();
            this.render();
        };
        this.spectrogramImage.onerror = () => {
            console.error('Failed to load spectrogram image:', spectrogramUrl);
        };
        this.spectrogramImage.src = spectrogramUrl;
    }
    
    /**
     * Setup event listeners for interaction
     */
    setupEventListeners() {
        if (!this.canvas) return;
        
        // Mouse events for selection and playback
        this.canvas.addEventListener('click', (e) => this.handleClick(e));
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        
        // Wheel events for zoom
        this.canvas.addEventListener('wheel', (e) => this.handleWheel(e));
    }
    
    /**
     * Handle canvas resize
     */
    resize() {
        if (!this.canvas || !this.player.container) return;
        
        const rect = this.player.container.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        
        // Set canvas size
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        
        // Scale context for high DPI displays
        this.ctx.scale(dpr, dpr);
        
        // Set CSS size
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';
        
        this.render();
    }
    
    /**
     * Render the spectrogram
     */
    render() {
        if (!this.ctx || !this.imageLoaded || !this.spectrogramImage) return;
        
        const canvasWidth = this.canvas.width / (window.devicePixelRatio || 1);
        const canvasHeight = this.canvas.height / (window.devicePixelRatio || 1);
        
        // Clear canvas
        this.ctx.clearRect(0, 0, canvasWidth, canvasHeight);
        
        // Calculate viewport based on zoom and offset
        const viewportWidth = canvasWidth / this.player.zoomLevel;
        const viewportStartX = this.player.zoomOffset * this.imageWidth;
        const viewportEndX = Math.min(viewportStartX + viewportWidth * (this.imageWidth / canvasWidth), this.imageWidth);
        
        // Calculate source rectangle from image
        const srcX = viewportStartX;
        const srcY = 0;
        const srcWidth = viewportEndX - viewportStartX;
        const srcHeight = this.imageHeight;
        
        // Calculate destination rectangle on canvas
        const destX = 0;
        const destY = 0;
        const destWidth = canvasWidth;
        const destHeight = canvasHeight;
        
        // Draw the spectrogram portion
        if (srcWidth > 0 && srcHeight > 0) {
            this.ctx.drawImage(
                this.spectrogramImage,
                srcX, srcY, srcWidth, srcHeight,
                destX, destY, destWidth, destHeight
            );
        }
        
        // Draw segments overlay
        this.drawSegments();
        
        // Draw selection
        this.drawSelection();
        
        // Draw playback position
        this.drawPlaybackPosition();
    }
    
    /**
     * Draw segments overlay
     */
    drawSegments() {
        if (!this.player.segments || this.player.segments.length === 0) return;
        
        const canvasWidth = this.canvas.width / (window.devicePixelRatio || 1);
        const canvasHeight = this.canvas.height / (window.devicePixelRatio || 1);
        
        this.ctx.save();
        this.ctx.strokeStyle = '#007bff';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);
        
        this.player.segments.forEach(segment => {
            const startTime = segment.onset || 0;
            const endTime = segment.offset || 0;
            
            const startX = this.timeToX(startTime, canvasWidth);
            const endX = this.timeToX(endTime, canvasWidth);
            
            // Draw segment boundaries
            if (startX >= 0 && startX <= canvasWidth) {
                this.ctx.beginPath();
                this.ctx.moveTo(startX, 0);
                this.ctx.lineTo(startX, canvasHeight);
                this.ctx.stroke();
            }
            
            if (endX >= 0 && endX <= canvasWidth && endX !== startX) {
                this.ctx.beginPath();
                this.ctx.moveTo(endX, 0);
                this.ctx.lineTo(endX, canvasHeight);
                this.ctx.stroke();
            }
        });
        
        this.ctx.restore();
    }
    
    /**
     * Draw selection overlay
     */
    drawSelection() {
        if (this.player.selectionStart === null || this.player.selectionEnd === null) return;
        
        const canvasWidth = this.canvas.width / (window.devicePixelRatio || 1);
        const canvasHeight = this.canvas.height / (window.devicePixelRatio || 1);
        
        const startX = this.timeToX(this.player.selectionStart, canvasWidth);
        const endX = this.timeToX(this.player.selectionEnd, canvasWidth);
        
        this.ctx.save();
        this.ctx.fillStyle = 'rgba(0, 123, 255, 0.3)';
        this.ctx.fillRect(Math.min(startX, endX), 0, Math.abs(endX - startX), canvasHeight);
        this.ctx.restore();
    }
    
    /**
     * Draw playback position
     */
    drawPlaybackPosition() {
        if (!this.player.isPlaying && this.player.currentTime === 0) return;
        
        const canvasWidth = this.canvas.width / (window.devicePixelRatio || 1);
        const canvasHeight = this.canvas.height / (window.devicePixelRatio || 1);
        
        const x = this.timeToX(this.player.currentTime, canvasWidth);
        
        if (x >= 0 && x <= canvasWidth) {
            this.ctx.save();
            this.ctx.strokeStyle = '#ff0000';
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, canvasHeight);
            this.ctx.stroke();
            this.ctx.restore();
        }
    }
    
    /**
     * Convert time to X coordinate
     * @param {number} time - Time in seconds
     * @param {number} canvasWidth - Canvas width
     * @returns {number} X coordinate
     */
    timeToX(time, canvasWidth) {
        const totalDuration = this.player.duration;
        if (totalDuration === 0) return 0;
        
        // Account for zoom and offset
        const viewportDuration = totalDuration / this.player.zoomLevel;
        const viewportStartTime = this.player.zoomOffset * totalDuration;
        
        const relativeTime = time - viewportStartTime;
        return (relativeTime / viewportDuration) * canvasWidth;
    }
    
    /**
     * Convert X coordinate to time
     * @param {number} x - X coordinate
     * @param {number} canvasWidth - Canvas width
     * @returns {number} Time in seconds
     */
    xToTime(x, canvasWidth) {
        const totalDuration = this.player.duration;
        const viewportDuration = totalDuration / this.player.zoomLevel;
        const viewportStartTime = this.player.zoomOffset * totalDuration;
        
        const relativeTime = (x / canvasWidth) * viewportDuration;
        return Math.max(0, Math.min(totalDuration, viewportStartTime + relativeTime));
    }
    
    /**
     * Handle click events
     */
    handleClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const canvasWidth = rect.width;
        
        const time = this.xToTime(x, canvasWidth);
        
        // Seek to clicked position
        this.player.seekTo(time);
    }
    
    /**
     * Handle mouse down events
     */
    handleMouseDown(e) {
        if (!this.player.allowSelection) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const canvasWidth = rect.width;
        
        const time = this.xToTime(x, canvasWidth);
        this.player.selectionStart = time;
        this.player.selectionEnd = time;
        
        this.isDragging = true;
        this.render();
    }
    
    /**
     * Handle mouse move events
     */
    handleMouseMove(e) {
        if (!this.isDragging || !this.player.allowSelection) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const canvasWidth = rect.width;
        
        const time = this.xToTime(x, canvasWidth);
        this.player.selectionEnd = time;
        
        this.render();
        this.player.updateSelectionDisplay();
    }
    
    /**
     * Handle mouse up events
     */
    handleMouseUp(e) {
        this.isDragging = false;
    }
    
    /**
     * Handle wheel events for zoom
     */
    handleWheel(e) {
        e.preventDefault();
        
        const delta = e.deltaY;
        const zoomFactor = 1.1;
        
        if (delta < 0) {
            // Zoom in
            this.player.zoomLevel = Math.min(this.player.zoomLevel * zoomFactor, 20);
        } else {
            // Zoom out
            this.player.zoomLevel = Math.max(this.player.zoomLevel / zoomFactor, 1);
        }
        
        // Adjust offset to keep zoom centered on mouse position
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const mouseTimeRatio = x / rect.width;
        
        // Update offset to keep the mouse position stable
        const maxOffset = 1 - (1 / this.player.zoomLevel);
        this.player.zoomOffset = Math.max(0, Math.min(maxOffset, 
            this.player.zoomOffset + (mouseTimeRatio - 0.5) * (1 / this.player.zoomLevel - 1 / (this.player.zoomLevel / zoomFactor))));
        
        this.render();
    }
    
    /**
     * Show the spectrogram canvas
     */
    show() {
        if (this.canvas) {
            this.canvas.style.display = 'block';
            this.resize();
            this.render();
        }
    }
    
    /**
     * Hide the spectrogram canvas
     */
    hide() {
        if (this.canvas) {
            this.canvas.style.display = 'none';
        }
    }
    
    /**
     * Update the spectrogram rendering (called by player)
     */
    update() {
        this.render();
    }
}