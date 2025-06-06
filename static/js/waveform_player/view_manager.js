/**
 * BattyCoda Waveform Player - View Manager
 * 
 * Handles switching between waveform and spectrogram views
 */

export class ViewManager {
    /**
     * Create a new ViewManager
     * @param {WaveformPlayer} player - The parent player instance
     */
    constructor(player) {
        this.player = player;
        this.viewMode = 'waveform';
        this.spectrogramUrl = null;
        this.spectrogramInitialized = false;
    }
    
    /**
     * Initialize spectrogram support
     * @param {string} spectrogramUrl - URL of the spectrogram image
     */
    initializeSpectrogram(spectrogramUrl) {
        this.spectrogramUrl = spectrogramUrl;
        if (spectrogramUrl) {
            this.player.spectrogramRenderer.initialize(spectrogramUrl);
            this.spectrogramInitialized = true;
        }
    }
    
    /**
     * Switch between waveform and spectrogram view modes
     * @param {string} mode - 'waveform' or 'spectrogram'
     */
    setViewMode(mode) {
        if (mode === this.viewMode) return;
        
        // Don't switch to spectrogram if it's not available
        if (mode === 'spectrogram' && !this.spectrogramInitialized) {
            console.warn('Spectrogram not available');
            return;
        }
        
        this.viewMode = mode;
        
        if (mode === 'spectrogram') {
            // Show spectrogram, hide waveform
            this.hideWaveform();
            this.showSpectrogram();
        } else {
            // Show waveform, hide spectrogram
            this.hideSpectrogram();
            this.showWaveform();
        }
        
        // Update the display
        this.redraw();
    }
    
    /**
     * Get the current view mode
     * @returns {string} Current view mode ('waveform' or 'spectrogram')
     */
    getViewMode() {
        return this.viewMode;
    }
    
    /**
     * Check if spectrogram is available
     * @returns {boolean} True if spectrogram is available
     */
    isSpectrogramAvailable() {
        return this.spectrogramInitialized && this.spectrogramUrl;
    }
    
    /**
     * Show the waveform view
     */
    showWaveform() {
        if (this.player.waveformContainer) {
            this.player.waveformContainer.style.display = 'block';
        }
        // Make sure waveform renderer is showing
        this.player.waveformRenderer.show();
    }
    
    /**
     * Hide the waveform view
     */
    hideWaveform() {
        if (this.player.waveformRenderer) {
            this.player.waveformRenderer.hide();
        }
    }
    
    /**
     * Show the spectrogram view
     */
    showSpectrogram() {
        if (this.spectrogramInitialized) {
            this.player.spectrogramRenderer.show();
        }
    }
    
    /**
     * Hide the spectrogram view
     */
    hideSpectrogram() {
        if (this.spectrogramInitialized) {
            this.player.spectrogramRenderer.hide();
        }
    }
    
    /**
     * Redraw the current view
     */
    redraw() {
        if (this.viewMode === 'spectrogram' && this.spectrogramInitialized) {
            this.player.spectrogramRenderer.update();
        } else {
            this.player.drawWaveform();
        }
        this.player.drawTimeline();
    }
    
    /**
     * Handle zoom changes - update both views
     * @param {number} newZoomLevel - New zoom level
     * @param {number} newZoomOffset - New zoom offset
     */
    handleZoomChange(newZoomLevel, newZoomOffset) {
        this.player.zoomLevel = newZoomLevel;
        this.player.zoomOffset = newZoomOffset;
        this.redraw();
    }
    
    /**
     * Handle selection changes - update both views
     */
    handleSelectionChange() {
        this.redraw();
        this.player.updateSelectionDisplay();
    }
    
    /**
     * Handle playback position changes - update both views
     */
    handlePlaybackUpdate() {
        this.redraw();
        this.player.updateTimeDisplay();
    }
    
    /**
     * Handle window resize - update both views
     */
    handleResize() {
        if (this.spectrogramInitialized) {
            this.player.spectrogramRenderer.resize();
        }
        this.redraw();
    }
}