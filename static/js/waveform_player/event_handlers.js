/**
 * BattyCoda Waveform Player - Event Handlers Module
 * 
 * Handles all event listener setup and management for the waveform player
 */

export class EventHandlers {
    constructor(player) {
        this.player = player;
    }

    /**
     * Set up all event listeners
     */
    setupEventListeners() {
        this.setupAudioEventListeners();
        this.setupControlEventListeners();
        this.setupZoomEventListeners();
        this.player.setupSpeedEventListeners();
        this.setupSelectionEventListeners();
        this.setupWindowEventListeners();
    }

    /**
     * Set up audio player event listeners
     */
    setupAudioEventListeners() {
        if (!this.player.audioPlayer) return;
        
        let lastScrollUpdateTime = 0;
        
        // Flag to track if this is the first timeupdate after a manual seek
        let isFirstUpdate = true;
        let lastClickTime = 0;
        
        this.player.audioPlayer.addEventListener('timeupdate', () => {
            this.player.currentTime = this.player.audioPlayer.currentTime;
            this.player.updateTimeDisplay();
            
            // Redraw the current view to update the playback cursor
            this.player.redrawCurrentView();
            
            const now = performance.now();
            const timeSinceLastClick = now - lastClickTime;
            const isAfterManualSeek = timeSinceLastClick < 500; // Within 0.5 seconds of a click
            
            // Check if we're in a recording selection process
            if (this.player.allowSelection && this.player.selectionStart !== null && this.player.selectionEnd === null) {
                // If we're playing and hit a segment boundary, stop the selection process
                if (this.player.isPlaying) {
                    if (this.player.isTimeInSegment(this.player.currentTime)) {
                        // We've entered an existing segment - can't make selection here
                        this.player.selectionStart = null;
                        this.player.updateSelectionDisplay();
                        this.player.redrawCurrentView();
                        if (this.player.setStartBtn) this.player.setStartBtn.disabled = false;
                        if (this.player.setEndBtn) this.player.setEndBtn.disabled = true;
                    }
                }
            }
            
            // Smooth scrolling when zoomed in during playback (but not right after manual seeks)
            if (this.player.zoomLevel > 1 && this.player.isPlaying) {
                const currentRatio = this.player.currentTime / this.player.duration;
                const visibleDuration = 1 / this.player.zoomLevel;
                const currentCenter = this.player.zoomOffset + visibleDuration / 2;
                const distanceFromCenter = Math.abs(currentRatio - currentCenter);
                
                // Only scroll if the playhead is getting close to the edge of the visible area
                const scrollThreshold = visibleDuration * 0.3; // Start scrolling when 30% from edge
                
                if (distanceFromCenter > scrollThreshold && !isAfterManualSeek) {
                    // Smoothly update the target zoom offset
                    this.player.targetZoomOffset = Math.max(0, Math.min(
                        currentRatio - visibleDuration / 2,
                        1 - visibleDuration
                    ));
                    
                    // Only update if enough time has passed or if we're significantly off target
                    if (Math.abs(this.player.targetZoomOffset - this.player.zoomOffset) > 0.01 || (now - lastScrollUpdateTime > 250)) {
                        this.player.animateScroll();
                        lastScrollUpdateTime = now;
                    }
                }
            }
        });

        this.player.audioPlayer.addEventListener('play', () => {
            this.player.isPlaying = true;
            this.player.updatePlayButtons();
        });

        this.player.audioPlayer.addEventListener('pause', () => {
            this.player.isPlaying = false;
            this.player.updatePlayButtons();
        });

        this.player.audioPlayer.addEventListener('ended', () => {
            this.player.isPlaying = false;
            this.player.updatePlayButtons();
        });
        
        this.player.audioPlayer.addEventListener('loadedmetadata', () => {
            this.player.duration = this.player.audioPlayer.duration;
            if (this.player.totalTimeEl) this.player.totalTimeEl.textContent = this.player.duration.toFixed(2) + 's';
        });
        
        this.player.audioPlayer.addEventListener('canplay', () => {
            if (this.player.loadingEl) this.player.loadingEl.style.display = 'none';
        });
    }

    /**
     * Set up control button event listeners
     */
    setupControlEventListeners() {
        // Play button
        if (this.player.playBtn) {
            this.player.playBtn.addEventListener('click', () => {
                this.player.audioPlayer.play();
            });
        }
        
        // Pause button
        if (this.player.pauseBtn) {
            this.player.pauseBtn.addEventListener('click', () => {
                this.player.audioPlayer.pause();
            });
        }
        
        // Stop button
        if (this.player.stopBtn) {
            this.player.stopBtn.addEventListener('click', () => {
                this.player.audioPlayer.pause();
                this.player.audioPlayer.currentTime = 0;
                this.player.currentTime = 0;
                this.player.updateTimeDisplay();
                this.player.redrawCurrentView();
            });
        }
        
        // Progress container click
        if (this.player.progressContainer) {
            this.player.progressContainer.addEventListener('click', (e) => {
                const rect = this.player.progressContainer.getBoundingClientRect();
                const clickX = e.clientX - rect.left;
                const width = rect.width;
                const clickRatio = clickX / width;
                
                // Update audio player time
                this.player.audioPlayer.currentTime = clickRatio * this.player.duration;
                this.player.currentTime = this.player.audioPlayer.currentTime;
                
                // Let the timeupdate handler handle this gradually during playback
                
                this.player.updateTimeDisplay();
                this.player.redrawCurrentView();
            });
        }
    }

    /**
     * Set up zoom button event listeners
     */
    setupZoomEventListeners() {
        if (!this.player.showZoom) return;
        
        // Zoom in button
        if (this.player.zoomInBtn) {
            this.player.zoomInBtn.addEventListener('click', () => {
                // Calculate the current center time based on zoom offset
                const visibleDuration = this.player.duration / this.player.zoomLevel;
                const currentCenterTime = (this.player.zoomOffset + (visibleDuration / this.player.duration) * 0.5) * this.player.duration;
                
                // Double the zoom level
                this.player.zoomLevel = Math.min(this.player.zoomLevel * 2, 32);
                
                // Calculate new visible duration and adjust offset to keep the same center
                const newVisibleDuration = this.player.duration / this.player.zoomLevel;
                this.player.zoomOffset = Math.max(0, Math.min(
                    currentCenterTime / this.player.duration - (newVisibleDuration / this.player.duration) * 0.5, 
                    1 - newVisibleDuration / this.player.duration
                ));
                
                // Update all displays
                this.player.redrawCurrentView();
                this.player.drawTimeline();
                this.player.updateTimeDisplay();
            });
        }
        
        // Zoom out button
        if (this.player.zoomOutBtn) {
            this.player.zoomOutBtn.addEventListener('click', () => {
                // Calculate the current center time
                const visibleDuration = this.player.duration / this.player.zoomLevel;
                const currentCenterTime = (this.player.zoomOffset + (visibleDuration / this.player.duration) * 0.5) * this.player.duration;
                
                // Halve the zoom level
                this.player.zoomLevel = Math.max(this.player.zoomLevel / 2, 1);
                
                // Adjust offset to maintain center, but only if we're not at zoom level 1
                if (this.player.zoomLevel > 1) {
                    const newVisibleDuration = this.player.duration / this.player.zoomLevel;
                    this.player.zoomOffset = Math.max(0, Math.min(
                        currentCenterTime / this.player.duration - (newVisibleDuration / this.player.duration) * 0.5,
                        1 - newVisibleDuration / this.player.duration
                    ));
                } else {
                    this.player.zoomOffset = 0;
                }
                
                // Update all displays
                this.player.redrawCurrentView();
                this.player.drawTimeline();
                this.player.updateTimeDisplay();
            });
        }
        
        // Reset zoom button
        if (this.player.resetZoomBtn) {
            this.player.resetZoomBtn.addEventListener('click', () => {
                this.player.zoomLevel = 1;
                this.player.zoomOffset = 0;
                
                // Update all displays
                this.player.redrawCurrentView();
                this.player.drawTimeline();
                this.player.updateTimeDisplay();
            });
        }
    }

    /**
     * Set up selection button event listeners
     */
    setupSelectionEventListeners() {
        if (!this.player.allowSelection) return;
        
        // Set start button
        if (this.player.setStartBtn) {
            this.player.setStartBtn.addEventListener('click', () => {
                // Only allow setting start if not in a segment
                if (this.player.isTimeInSegment(this.player.currentTime)) {
                    return;
                }
                
                this.player.selectionStart = this.player.currentTime;
                this.player.selectionEnd = null;
                this.player.updateSelectionDisplay();
                this.player.redrawCurrentView();
                
                // Update button states
                this.player.setStartBtn.disabled = false;  // Allow changing start point
            });
            
            // Regularly check if we're inside a segment and update button state
            setInterval(() => {
                if (this.player.setStartBtn) {
                    this.player.setStartBtn.disabled = this.player.isTimeInSegment(this.player.currentTime);
                }
            }, 100);
        }
        
        // Set end button
        if (this.player.setEndBtn) {
            this.player.setEndBtn.addEventListener('click', () => {
                // Only proceed if we have a start time
                if (this.player.selectionStart !== null && this.player.currentTime > this.player.selectionStart) {
                    // Check if there are any segments between start and current time
                    const segmentBetween = this.player.segments.some(segment => {
                        const segStart = segment.onset;
                        const segEnd = segment.offset;
                        // Return true if this segment overlaps with our proposed selection
                        return (segStart <= this.player.currentTime && segEnd >= this.player.selectionStart) ||
                               (segStart >= this.player.selectionStart && segStart <= this.player.currentTime);
                    });
                    
                    if (segmentBetween) {
                        // Find the nearest segment boundary after our start time
                        const boundaryTime = this.player.findNearestSegmentBoundary(this.player.selectionStart, 'forward');
                        if (boundaryTime !== null && boundaryTime > this.player.selectionStart) {
                            this.player.selectionEnd = Math.min(boundaryTime - 0.001, this.player.currentTime);
                        } else {
                            // No safe boundary found, can't complete selection
                            return;
                        }
                    } else {
                        this.player.selectionEnd = this.player.currentTime;
                    }
                    
                    this.player.updateSelectionDisplay();
                    this.player.redrawCurrentView();
                    
                    // Reset button states after completing a selection
                    this.player.setStartBtn.disabled = this.player.isTimeInSegment(this.player.currentTime);
                    this.player.setEndBtn.disabled = true;
                }
            });
        }
        
        // Set end button state based on selection progress
        setInterval(() => {
            if (this.player.setEndBtn) {
                if (this.player.selectionStart !== null && this.player.selectionEnd === null) {
                    // We have a start time but no end time
                    // Check if current time is valid for ending selection
                    const hasValidEnd = this.player.currentTime > this.player.selectionStart;
                    
                    // Check if there are any segments between start and current time
                    const segmentBetween = this.player.segments.some(segment => {
                        const segStart = segment.onset;
                        const segEnd = segment.offset;
                        // Return true if this segment overlaps with our proposed selection
                        return (segStart <= this.player.currentTime && segEnd >= this.player.selectionStart) ||
                               (segStart >= this.player.selectionStart && segStart <= this.player.currentTime);
                    });
                    
                    this.player.setEndBtn.disabled = !hasValidEnd || segmentBetween;
                } else {
                    this.player.setEndBtn.disabled = true;
                }
            }
        }, 100);
    }

    /**
     * Set up window event listeners
     */
    setupWindowEventListeners() {
        // Window resize handler to redraw canvas
        window.addEventListener('resize', () => {
            // Debounce resize events
            setTimeout(() => {
                this.player.redrawCurrentView();
                this.player.drawTimeline();
            }, 250);
        });
    }

    /**
     * Animate smooth scrolling when zoomed in
     */
    animateScroll() {
        // Cancel any existing animation
        if (this.player.animationFrameId) {
            cancelAnimationFrame(this.player.animationFrameId);
        }
        
        const startOffset = this.player.zoomOffset;
        const targetOffset = this.player.targetZoomOffset;
        const offsetDiff = targetOffset - startOffset;
        const startTime = performance.now();
        const duration = 150; // Animation duration in ms
        
        const step = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Use easing function for smooth animation
            const eased = 1 - Math.pow(1 - progress, 3); // Ease-out cubic
            
            // Update zoom offset
            this.player.zoomOffset = startOffset + (offsetDiff * eased);
            
            // Redraw
            this.player.redrawCurrentView();
            this.player.drawTimeline();
            this.player.updateTimeDisplay();
            
            // Continue animation if not complete
            if (progress < 1) {
                this.player.animationFrameId = requestAnimationFrame(step);
            }
        };
        
        this.player.animationFrameId = requestAnimationFrame(step);
    }
}