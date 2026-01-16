/**
 * BattyCoda Waveform Player - Core Player Class
 *
 * Main player class that orchestrates all waveform player functionality
 */

import { WaveformRenderer } from './renderer.js';
import { TimelineRenderer } from './timeline.js';
import { SpectrogramDataRenderer } from './spectrogram_data_renderer.js';
import { OverlayRenderer } from './overlay_renderer.js';
import { ViewManager } from './view_manager.js';
import { EventHandlers } from './event_handlers.js';
import { UIState } from './ui_state.js';
import { DataManager } from './data_manager.js';
import { SeekHandler } from './seek_handler.js';
import { PlayRegionHandler } from './play_region_handler.js';


/**
 * WaveformPlayer class - encapsulates waveform player functionality
 */
export class WaveformPlayer {
  /**
   * Create a new WaveformPlayer instance
   * @param {string} containerId - ID of the container element
   * @param {number} recordingId - ID of the recording
   * @param {boolean} allowSelection - Whether to allow selecting regions
   * @param {boolean} showZoom - Whether to show zoom controls
   * @param {Array} [segmentsData] - Optional array of segments to display
   */
  constructor(containerId, recordingId, allowSelection, showZoom, segmentsData) {
    // Configuration
    this.containerId = containerId;
    this.recordingId = recordingId;
    this.allowSelection = allowSelection;
    this.showZoom = showZoom;

    // DOM elements
    this.initDomElements();

    // State
    this.currentTime = 0;
    this.duration = parseFloat(this.totalTimeEl?.textContent) || 0;
    this.isPlaying = false;
    this.waveformData = null;
    this.segments = segmentsData || [];
    this.zoomLevel = 1;
    this.zoomOffset = 0;
    this.selectionStart = null;
    this.selectionEnd = null;
    this.animationFrameId = null;
    this.targetZoomOffset = this.zoomOffset;

    // Renderers
    this.waveformRenderer = new WaveformRenderer(this);
    this.timelineRenderer = new TimelineRenderer(this);
    this.spectrogramDataRenderer = new SpectrogramDataRenderer(containerId, recordingId, this);
    this.overlayRenderer = new OverlayRenderer(this);

    // View manager
    this.viewManager = new ViewManager(this);

    // Modules
    this.eventHandlers = new EventHandlers(this);
    this.uiState = new UIState(this);
    this.dataManager = new DataManager(this);
    this.seekHandler = new SeekHandler(this);
    this.playRegionHandler = new PlayRegionHandler(this);
  }

  /**
   * Initialize DOM element references
   */
  initDomElements() {
    const id = this.containerId;

    this.container = document.getElementById(id);
    if (!this.container) return;

    this.audioPlayer = document.getElementById(`${id}-audio`);
    this.playBtn = document.getElementById(`${id}-play-btn`);
    this.pauseBtn = document.getElementById(`${id}-pause-btn`);
    this.stopBtn = document.getElementById(`${id}-stop-btn`);
    this.progressBar = document.getElementById(`${id}-progress-bar`);
    this.progressContainer = document.getElementById(`${id}-progress-container`);
    this.currentTimeEl = document.getElementById(`${id}-current-time`);
    this.totalTimeEl = document.getElementById(`${id}-total-time`);
    this.waveformContainer = document.getElementById(id);
    this.timelineContainer = document.getElementById(`${id}-timeline`);
    this.speed1xBtn = document.getElementById(`${id}-speed-1x`);
    this.speedSlowBtn = document.getElementById(`${id}-speed-slow`);
    this.loadingEl = document.getElementById(`${id}-loading`);
    this.statusEl = document.getElementById(`${id}-status`);

    // Zoom controls (optional)
    if (this.showZoom) {
      this.zoomInBtn = document.getElementById(`${id}-zoom-in-btn`);
      this.zoomOutBtn = document.getElementById(`${id}-zoom-out-btn`);
      this.resetZoomBtn = document.getElementById(`${id}-reset-zoom-btn`);
    }

    // Selection controls (optional)
    if (this.allowSelection) {
      this.setStartBtn = document.getElementById(`${id}-set-start-btn`);
      this.setEndBtn = document.getElementById(`${id}-set-end-btn`);
      this.selectionRangeEl = document.getElementById(`${id}-selection-range`);
    }
  }

  /**
   * Initialize the waveform player
   */
  initialize() {
    this.eventHandlers.setupEventListeners();
    this.loadWaveformData();
    this.uiState.updateTimeDisplay();
    if (this.allowSelection) this.uiState.updateSelectionDisplay();
    this.uiState.updatePlayButtons();
  }

  setPlaybackRate(rate) {
    if (this.audioPlayer) {
      this.audioPlayer.playbackRate = rate;
    }
  }

  /**
   * Load waveform data from the server
   */
  async loadWaveformData() {
    try {
      // Update status
      if (this.statusEl) this.statusEl.textContent = 'Loading...';

      console.log('Loading waveform data for recording:', this.recordingId);
      const response = await fetch(`/recordings/${this.recordingId}/waveform-data/`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log('Waveform data response:', data);

      // Set duration if provided
      if (data.duration !== undefined && data.duration !== null) {
        this.duration = data.duration;
        if (this.totalTimeEl) this.totalTimeEl.textContent = this.duration.toFixed(2) + 's';
      }

      if (data.success) {
        this.waveformData = data.waveform;
        console.log('Waveform data loaded successfully:', {
          dataLength: this.waveformData ? this.waveformData.length : 0,
          duration: this.duration,
        });

        // Hide loading indicator
        if (this.loadingEl) this.loadingEl.style.display = 'none';

        // Update status
        if (this.statusEl) {
          this.statusEl.textContent = '';
        }

        // Draw the current view (waveform will be hidden if in spectrogram mode)
        this.redrawCurrentView();
        this.drawTimeline();
      } else {
        throw new Error(data.error || 'Failed to load waveform data');
      }
    } catch (error) {
      console.error('Error loading waveform data:', error);

      // Hide loading indicator
      if (this.loadingEl) this.loadingEl.style.display = 'none';

      // Update status with error
      if (this.statusEl) {
        this.statusEl.textContent = 'Error loading waveform';
      }

      // Show a basic waveform container even if loading fails
      if (this.waveformContainer) {
        this.waveformContainer.style.height = '150px';
        this.waveformContainer.style.backgroundColor = '#f0f0f0';
        this.waveformContainer.style.border = '1px solid #ddd';
      }
    }
  }

  /**
   * Draw the waveform (delegates to renderer)
   */
  drawWaveform() {
    this.waveformRenderer.draw();
  }

  /**
   * Redraw the current view (respects view mode)
   */
  redrawCurrentView() {
    if (this.viewManager) {
      this.viewManager.redraw();
    } else {
      // Fallback for cases where ViewManager isn't available yet
      this.drawWaveform();
    }
  }

  /**
   * Draw the timeline (delegates to renderer)
   */
  drawTimeline() {
    this.timelineRenderer.draw();
  }

  // Delegation methods for backwards compatibility and external access

  /**
   * Update the time display and progress bar
   */
  updateTimeDisplay() {
    return this.uiState.updateTimeDisplay();
  }

  /**
   * Update the selection display
   */
  updateSelectionDisplay() {
    return this.uiState.updateSelectionDisplay();
  }

  /**
   * Update play button states
   */
  updatePlayButtons() {
    return this.uiState.updatePlayButtons();
  }

  /**
   * Get the current selection
   */
  getSelection() {
    return this.dataManager.getSelection();
  }

  /**
   * Check if a given time is within any existing segment
   */
  isTimeInSegment(time) {
    return this.dataManager.isTimeInSegment(time);
  }

  /**
   * Find the nearest segment boundary from a given time
   */
  findNearestSegmentBoundary(time, direction = 'forward') {
    return this.dataManager.findNearestSegmentBoundary(time, direction);
  }

  /**
   * Set segments for the waveform
   */
  setSegments(newSegments) {
    return this.dataManager.setSegments(newSegments);
  }

  /**
   * Redraw segments on the waveform
   */
  redrawSegments() {
    return this.dataManager.redrawSegments();
  }

  /**
   * Seek to a specific time and ensure it's visible in the viewport
   * @param {number} time - Time in seconds to seek to
   */
  seek(time) {
    return this.seekHandler.seek(time);
  }

  /**
   * Play a region of audio from start to end time
   * @param {number} start - Start time in seconds
   * @param {number} end - End time in seconds
   */
  playRegion(start, end) {
    return this.playRegionHandler.playRegion(start, end);
  }

  /**
   * Animate smooth scrolling when zoomed in
   */
  animateScroll() {
    return this.eventHandlers.animateScroll();
  }
}
