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
    this.viewMode = 'waveform'; // Initial mode (will be switched by view toggle)
    this.spectrogramInitialized = false;
  }

  /**
   * Initialize spectrogram data rendering (HDF5-based)
   */
  async initializeSpectrogramData() {
    try {
      const success = await this.player.spectrogramDataRenderer.initialize();
      if (success) {
        this.spectrogramInitialized = true;
      } else {
        console.warn('Failed to initialize spectrogram data');
      }
      return success;
    } catch (error) {
      console.error('Error initializing spectrogram data:', error);
      return false;
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
      console.warn('Spectrogram not available - initialized:', this.spectrogramInitialized);
      return;
    }

    this.viewMode = mode;

    if (mode === 'spectrogram') {
      this.hideWaveform();
      this.showSpectrogram();
    } else {
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
    return this.spectrogramInitialized;
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
      this.player.spectrogramDataRenderer.show();
    }
  }

  /**
   * Hide the spectrogram view
   */
  hideSpectrogram() {
    if (this.spectrogramInitialized) {
      this.player.spectrogramDataRenderer.hide();
    }
  }

  /**
   * Redraw the current view
   */
  redraw() {
    if (this.viewMode === 'spectrogram' && this.spectrogramInitialized) {
      // Calculate current view parameters
      const visibleDuration = this.player.duration / this.player.zoomLevel;
      const visibleStartTime = this.player.zoomOffset * this.player.duration;
      const visibleEndTime = Math.min(visibleStartTime + visibleDuration, this.player.duration);

      this.player.spectrogramDataRenderer.updateView(
        visibleStartTime,
        visibleEndTime,
        this.player.waveformContainer?.clientWidth,
        this.player.waveformContainer?.clientHeight
      );
    } else {
      this.player.drawWaveform();
    }
    this.player.drawTimeline();

    // Draw overlay on top of whichever view is active
    this.player.overlayRenderer.draw();
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
      this.player.spectrogramDataRenderer.render();
    }
    this.redraw();
  }
}
