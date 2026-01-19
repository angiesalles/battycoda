/**
 * BattyCoda Waveform Player - View Manager
 *
 * Handles switching between waveform and spectrogram views
 *
 * Required dependencies (injected via constructor):
 * - spectrogramDataRenderer: object with initialize(), show(), hide(), updateView(), render()
 * - waveformRenderer: object with show(), hide()
 * - overlayRenderer: object with draw()
 * - getWaveformContainer: () => HTMLElement
 * - getDuration: () => number
 * - getZoomLevel: () => number
 * - getZoomOffset: () => number
 * - setZoomLevel: (level: number) => void
 * - setZoomOffset: (offset: number) => void
 * - drawWaveform: () => void
 * - drawTimeline: () => void
 * - updateSelectionDisplay: () => void
 * - updateTimeDisplay: () => void
 */

export class ViewManager {
  /**
   * Create a new ViewManager
   * @param {Object} deps - Dependencies object
   * @param {Object} deps.spectrogramDataRenderer - Spectrogram renderer
   * @param {Object} deps.waveformRenderer - Waveform renderer
   * @param {Object} deps.overlayRenderer - Overlay renderer
   * @param {Function} deps.getWaveformContainer - Returns waveform container element
   * @param {Function} deps.getDuration - Returns audio duration
   * @param {Function} deps.getZoomLevel - Returns zoom level
   * @param {Function} deps.getZoomOffset - Returns zoom offset
   * @param {Function} deps.setZoomLevel - Sets zoom level
   * @param {Function} deps.setZoomOffset - Sets zoom offset
   * @param {Function} deps.drawWaveform - Draw waveform callback
   * @param {Function} deps.drawTimeline - Draw timeline callback
   * @param {Function} deps.updateSelectionDisplay - Update selection display callback
   * @param {Function} deps.updateTimeDisplay - Update time display callback
   */
  constructor(deps) {
    this._spectrogramDataRenderer = deps.spectrogramDataRenderer;
    this._waveformRenderer = deps.waveformRenderer;
    this._overlayRenderer = deps.overlayRenderer;
    this._getWaveformContainer = deps.getWaveformContainer;
    this._getDuration = deps.getDuration;
    this._getZoomLevel = deps.getZoomLevel;
    this._getZoomOffset = deps.getZoomOffset;
    this._setZoomLevel = deps.setZoomLevel;
    this._setZoomOffset = deps.setZoomOffset;
    this._drawWaveform = deps.drawWaveform;
    this._drawTimeline = deps.drawTimeline;
    this._updateSelectionDisplay = deps.updateSelectionDisplay;
    this._updateTimeDisplay = deps.updateTimeDisplay;

    this.viewMode = 'waveform'; // Initial mode (will be switched by view toggle)
    this.spectrogramInitialized = false;
  }

  /**
   * Initialize spectrogram data rendering (HDF5-based)
   */
  async initializeSpectrogramData() {
    try {
      const success = await this._spectrogramDataRenderer.initialize();
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
    const waveformContainer = this._getWaveformContainer();
    if (waveformContainer) {
      waveformContainer.style.display = 'block';
    }
    // Make sure waveform renderer is showing
    if (this._waveformRenderer) {
      this._waveformRenderer.show();
    }
  }

  /**
   * Hide the waveform view
   */
  hideWaveform() {
    if (this._waveformRenderer) {
      this._waveformRenderer.hide();
    }
  }

  /**
   * Show the spectrogram view
   */
  showSpectrogram() {
    if (this.spectrogramInitialized && this._spectrogramDataRenderer) {
      this._spectrogramDataRenderer.show();
    }
  }

  /**
   * Hide the spectrogram view
   */
  hideSpectrogram() {
    if (this.spectrogramInitialized && this._spectrogramDataRenderer) {
      this._spectrogramDataRenderer.hide();
    }
  }

  /**
   * Redraw the current view
   */
  redraw() {
    const duration = this._getDuration();
    const zoomLevel = this._getZoomLevel();
    const zoomOffset = this._getZoomOffset();

    if (this.viewMode === 'spectrogram' && this.spectrogramInitialized) {
      // Calculate current view parameters
      const visibleDuration = duration / zoomLevel;
      const visibleStartTime = zoomOffset * duration;
      const visibleEndTime = Math.min(visibleStartTime + visibleDuration, duration);

      const waveformContainer = this._getWaveformContainer();
      this._spectrogramDataRenderer.updateView(
        visibleStartTime,
        visibleEndTime,
        waveformContainer?.clientWidth,
        waveformContainer?.clientHeight
      );
    } else {
      this._drawWaveform();
    }
    this._drawTimeline();

    // Draw overlay on top of whichever view is active
    if (this._overlayRenderer) {
      this._overlayRenderer.draw();
    }
  }

  /**
   * Handle zoom changes - update both views
   * @param {number} newZoomLevel - New zoom level
   * @param {number} newZoomOffset - New zoom offset
   */
  handleZoomChange(newZoomLevel, newZoomOffset) {
    this._setZoomLevel(newZoomLevel);
    this._setZoomOffset(newZoomOffset);
    this.redraw();
  }

  /**
   * Handle selection changes - update both views
   */
  handleSelectionChange() {
    this.redraw();
    this._updateSelectionDisplay();
  }

  /**
   * Handle playback position changes - update both views
   */
  handlePlaybackUpdate() {
    this.redraw();
    this._updateTimeDisplay();
  }

  /**
   * Handle window resize - update both views
   */
  handleResize() {
    if (this.spectrogramInitialized && this._spectrogramDataRenderer) {
      this._spectrogramDataRenderer.render();
    }
    this.redraw();
  }
}
