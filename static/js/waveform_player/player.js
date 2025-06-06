/**
 * BattyCoda Waveform Player - Core Player Class
 * 
 * Main player class that orchestrates all waveform player functionality
 */

import { WaveformRenderer } from './renderer.js';
import { TimelineRenderer } from './timeline.js';
import { SpectrogramRenderer } from './spectrogram_renderer.js';
import { ViewManager } from './view_manager.js';
import { EventHandlers } from './event_handlers.js';
import { UIState } from './ui_state.js';
import { DataManager } from './data_manager.js';

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
        this.spectrogramRenderer = new SpectrogramRenderer(this);
        
        // View manager
        this.viewManager = new ViewManager(this);
        
        // Modules
        this.eventHandlers = new EventHandlers(this);
        this.uiState = new UIState(this);
        this.dataManager = new DataManager(this);
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
        this.speed1xBtn  = document.getElementById(`${id}-speed-1x`);
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
                    duration: this.duration
                });
                
                // Hide loading indicator
                if (this.loadingEl) this.loadingEl.style.display = 'none';
                
                // Update status
                if (this.statusEl) {
                    this.statusEl.textContent = '';
                }
                
                // Ensure waveform is visible and draw
                this.viewManager.showWaveform();
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
<<<<<<< HEAD
     * Set up all event listeners
     */
    setupEventListeners() {
        this.setupAudioEventListeners();
        this.setupControlEventListeners();
        this.setupZoomEventListeners();
        this.setupSpeedEventListeners();
        this.setupSelectionEventListeners();
        this.setupWindowEventListeners();
    }
    
    /**
     * Set up audio player event listeners
     */
    setupAudioEventListeners() {
        if (!this.audioPlayer) return;
        
        let lastScrollUpdateTime = 0;
        
        // Flag to track if this is the first timeupdate after a manual seek
        let isFirstUpdate = true;
        let lastClickTime = 0;
        
        this.audioPlayer.addEventListener('timeupdate', () => {
            this.currentTime = this.audioPlayer.currentTime;
            this.updateTimeDisplay();
            
            const now = performance.now();
            const timeSinceLastClick = now - lastClickTime;
            const isAfterManualSeek = timeSinceLastClick < 500; // Within 0.5 seconds of a click
            
            // Check if we're in a recording selection process
            if (this.allowSelection && this.selectionStart !== null && this.selectionEnd === null) {
                // If we're playing through segments while making a selection, handle segment collisions
                if (this.isPlaying) {
                    // Check if current position is inside any existing segment
                    if (this.isTimeInSegment(this.currentTime)) {
                        // Stop the selection at the segment boundary we just entered
                        this.selectionEnd = this.findNearestSegmentBoundary(this.currentTime, 'backward');
                        this.updateSelectionDisplay();
                        this.drawWaveform();
                        
                        // Reset selection buttons state
                        if (this.setStartBtn) this.setStartBtn.disabled = false;
                        if (this.setEndBtn) this.setEndBtn.disabled = true;
                    }
                }
            }
            
            // For more reliable playback following, start recentering sooner
            // Also track if the cursor is near the edge of the visible area
            if (this.zoomLevel > 1 && this.isPlaying) {
                const visibleDuration = this.duration / this.zoomLevel;
                
                // Center the view on current time, with bounds checking
                const targetCenter = this.currentTime / this.duration;
                const halfVisibleDuration = visibleDuration / 2 / this.duration;
                
                // Calculate new offset (start of visible window)
                // This centers the playhead in the visible area
                this.targetZoomOffset = Math.max(0, Math.min(
                    targetCenter - halfVisibleDuration,
                    1 - visibleDuration / this.duration
                ));
                
                // Only update if significant change or enough time has passed
                if (Math.abs(this.targetZoomOffset - this.zoomOffset) > 0.01 || (now - lastScrollUpdateTime > 250)) {
                    // Move gradually toward the target position to create a smooth scrolling effect
                    // Apply a step toward the target position (easing)
                    const step = 0.3; // Adjusted for faster centering during playback
                    this.zoomOffset += (this.targetZoomOffset - this.zoomOffset) * step;
                    
                    this.drawWaveform();
                    this.drawTimeline();
                    lastScrollUpdateTime = now;
                    return; // Skip the drawWaveform below to avoid double draws
                }
            }
            
            // Just update waveform (for cursor) if we didn't do a full redraw above
            this.drawWaveform();
        });
        
        // Track clicks to avoid recentering right after a manual seek
        this.audioPlayer.addEventListener('seeking', () => {
            lastClickTime = performance.now();
        });
        
        this.audioPlayer.addEventListener('play', () => {
            this.isPlaying = true;
            this.updatePlayButtons();
        });
        
        this.audioPlayer.addEventListener('pause', () => {
            this.isPlaying = false;
            this.updatePlayButtons();
        });
        
        this.audioPlayer.addEventListener('ended', () => {
            this.isPlaying = false;
            this.updatePlayButtons();
        });
    }
    
    /**
     * Set up control button event listeners
     */
    setupControlEventListeners() {
        // Play button
        if (this.playBtn) {
            this.playBtn.addEventListener('click', () => {
                this.audioPlayer.play();
            });
        }
        
        // Pause button
        if (this.pauseBtn) {
            this.pauseBtn.addEventListener('click', () => {
                this.audioPlayer.pause();
            });
        }
        
        // Stop button
        if (this.stopBtn) {
            this.stopBtn.addEventListener('click', () => {
                this.audioPlayer.pause();
                this.audioPlayer.currentTime = 0;
                this.currentTime = 0;
                this.updateTimeDisplay();
                this.drawWaveform();
            });
        }
        
        // Progress container click
        if (this.progressContainer) {
            this.progressContainer.addEventListener('click', (e) => {
                const rect = this.progressContainer.getBoundingClientRect();
                const offsetX = e.clientX - rect.left;
                const clickPosition = offsetX / rect.width;
                
                // Set current time based on click position (progress bar always shows full duration)
                this.currentTime = clickPosition * this.duration;
                this.audioPlayer.currentTime = this.currentTime;
                
                // We no longer immediately center on clicked position
                // Let the timeupdate handler handle this gradually during playback
                
                this.updateTimeDisplay();
                this.drawWaveform();
            });
        }
    }
    
    /**
     * Set up zoom button event listeners
     */
    setupZoomEventListeners() {
        if (!this.showZoom) return;
        
        // Zoom in button
        if (this.zoomInBtn) {
            this.zoomInBtn.addEventListener('click', () => {
                // Store the current center position
                const oldZoomLevel = this.zoomLevel;
                const oldVisibleDuration = this.duration / oldZoomLevel;
                const oldCenterTime = this.currentTime;
                
                // Calculate where the current position is as a fraction of the visible area
                const relativePosition = (oldCenterTime - (this.zoomOffset * this.duration)) / oldVisibleDuration;
                
                // Update zoom level
                this.zoomLevel = Math.min(this.zoomLevel * 1.5, 10);
                
                // Calculate new visible duration
                const newVisibleDuration = this.duration / this.zoomLevel;
                
                // Calculate new offset to keep position centered
                this.zoomOffset = Math.max(0, Math.min(
                    oldCenterTime / this.duration - (newVisibleDuration / this.duration) * 0.5, 
                    1 - newVisibleDuration / this.duration
                ));
                
                // Update all displays
                this.drawWaveform();
                this.drawTimeline();
                this.updateTimeDisplay();
            });
        }
        
        // Zoom out button
        if (this.zoomOutBtn) {
            this.zoomOutBtn.addEventListener('click', () => {
                // Store the current center position
                const oldCenterTime = this.currentTime;
                
                // Update zoom level
                this.zoomLevel = Math.max(this.zoomLevel / 1.5, 1);
                
                // If we're back to zoom level 1, reset offset
                if (this.zoomLevel === 1) {
                    this.zoomOffset = 0;
                } else {
                    // Otherwise recalculate offset to keep current position visible
                    const newVisibleDuration = this.duration / this.zoomLevel;
                    this.zoomOffset = Math.max(0, Math.min(
                        oldCenterTime / this.duration - (newVisibleDuration / this.duration) * 0.5,
                        1 - newVisibleDuration / this.duration
                    ));
                }
                
                // Update all displays
                this.drawWaveform();
                this.drawTimeline();
                this.updateTimeDisplay();
            });
        }
        
        // Reset zoom button
        if (this.resetZoomBtn) {
            this.resetZoomBtn.addEventListener('click', () => {
                this.zoomLevel = 1;
                this.zoomOffset = 0;
                
                // Update all displays
                this.drawWaveform();
                this.drawTimeline();
                this.updateTimeDisplay();
            });
        }
    }

    setupSpeedEventListeners() {
    const updateActive = (activeBtn, inactiveBtn) => {
        activeBtn.classList.add('active');
        inactiveBtn.classList.remove('active');
    };

    if (this.speed1xBtn && this.speedSlowBtn && this.audioPlayer) {
        // Normal speed
        this.speed1xBtn.addEventListener('click', () => {
            this.audioPlayer.playbackRate = 1.0;
            updateActive(this.speed1xBtn, this.speedSlowBtn);
        });

        // 1⁄8 speed
        this.speedSlowBtn.addEventListener('click', () => {
            this.audioPlayer.playbackRate = 0.125;
            updateActive(this.speedSlowBtn, this.speed1xBtn);
        });
    }
}
    
    /**
     * Set up selection button event listeners
     */
    setupSelectionEventListeners() {
        if (!this.allowSelection) return;
        
        // Set start button
        if (this.setStartBtn) {
            this.setStartBtn.addEventListener('click', () => {
                // Check if current position overlaps with any existing segments
                if (this.isTimeInSegment(this.currentTime)) {
                    console.log('Cannot start selection inside an existing segment');
                    return; // Don't allow setting start point inside existing segment
                }
                
                // Start a new selection - clear any existing selection
                this.selectionStart = this.currentTime;
                this.selectionEnd = null;
                this.updateSelectionDisplay();
                this.drawWaveform();
                
                // Update button states
                this.setStartBtn.disabled = false;  // Allow changing start point
            });
            
            // Regularly check if we're inside a segment and update button state
            setInterval(() => {
                if (this.setStartBtn) {
                    this.setStartBtn.disabled = this.isTimeInSegment(this.currentTime);
                }
            }, 200);
        }
        
        // Set end button
        if (this.setEndBtn) {
            // Disable end button initially until start is set
            this.setEndBtn.disabled = true;
            
            this.setEndBtn.addEventListener('click', () => {
                // Only set end if there's a start point and current time is after it
                if (this.selectionStart !== null && this.currentTime > this.selectionStart) {
                    // Check if there's an existing segment between start and current time
                    const segmentBetween = this.segments.some(segment => {
                        const segStart = segment.start || segment.onset;
                        const segEnd = segment.end || segment.offset;
                        
                        // Check if any segment overlaps with our selection
                        return (segStart <= this.currentTime && segEnd >= this.selectionStart) ||
                               (segStart >= this.selectionStart && segStart <= this.currentTime);
                    });
                    
                    if (segmentBetween) {
                        // Find nearest segment boundary before current position
                        const boundaryTime = this.findNearestSegmentBoundary(this.currentTime, 'backward');
                        if (boundaryTime !== null && boundaryTime > this.selectionStart) {
                            // Use the segment boundary as our end point
                            this.selectionEnd = boundaryTime;
                        } else {
                            console.log('Cannot end selection - overlaps with existing segment');
                            return;
                        }
                    } else {
                        // Normal case - no overlap
                        this.selectionEnd = this.currentTime;
                    }
                    
                    this.updateSelectionDisplay();
                    this.drawWaveform();
                    
                    // Reset button states after completing a selection
                    this.setStartBtn.disabled = this.isTimeInSegment(this.currentTime);
                    this.setEndBtn.disabled = true;
                }
            });
            
            // We need to regularly update end button state based on playhead position
            this.audioPlayer.addEventListener('timeupdate', () => {
                if (this.selectionStart !== null && this.selectionEnd === null) {
                    // Check two conditions:
                    // 1. If we're to the right of the start point
                    // 2. If current position is inside any existing segment
                    const afterStart = this.currentTime > this.selectionStart;
                    const insideSegment = this.isTimeInSegment(this.currentTime);
                    
                    // Check if there's an overlap between our selection start and current time
                    const hasOverlap = this.segments.some(segment => {
                        const segStart = segment.start || segment.onset;
                        const segEnd = segment.end || segment.offset;
                        return (segStart <= this.currentTime && segEnd >= this.selectionStart) ||
                               (segStart >= this.selectionStart && segStart <= this.currentTime);
                    });
                    
                    // Only enable if we're after start, not inside a segment, and no segment overlap
                    this.setEndBtn.disabled = !afterStart || insideSegment || hasOverlap;
                } else {
                    // Disable end button if no start point or already have end point
                    this.setEndBtn.disabled = true;
                }
            });
        }
    }
    
    /**
     * Set up window event listeners
     */
    setupWindowEventListeners() {
        // Window resize event
        window.addEventListener('resize', () => {
            this.drawWaveform();
            this.drawTimeline();
        });
    }
    
    /**
     * Animate scrolling the waveform smoothly
=======
     * Animate smooth scrolling when zoomed in
>>>>>>> upstream/master
     */
    animateScroll() {
        return this.eventHandlers.animateScroll();
    }
}