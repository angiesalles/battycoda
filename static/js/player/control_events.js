/**
 * BattyCoda Waveform Player - UI Control Event Handlers
 *
 * Handles control buttons, zoom, and speed event listeners
 */

export class ControlEvents {
    constructor(player) {
        this.player = player;
    }

    /**
     * Set up all control event listeners
     */
    setup() {
        this.setupControlButtons();
        this.setupZoomControls();
        this.setupSpeedControls();
        this.setupWindowEvents();
    }

    /**
     * Set up control button event listeners
     */
    setupControlButtons() {
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
                this.player.seek(0);
            });
        }

        // Progress container click
        if (this.player.progressContainer) {
            this.player.progressContainer.addEventListener('click', (e) => {
                const rect = this.player.progressContainer.getBoundingClientRect();
                const clickX = e.clientX - rect.left;
                const width = rect.width;
                const clickRatio = clickX / width;

                this.player.seek(clickRatio * this.player.duration);
            });
        }
    }

    /**
     * Set up zoom button event listeners
     */
    setupZoomControls() {
        if (!this.player.showZoom) return;

        // Zoom in button
        if (this.player.zoomInBtn) {
            this.player.zoomInBtn.addEventListener('click', () => {
                // Calculate the current center time based on zoom offset
                const visibleDuration = this.player.duration / this.player.zoomLevel;
                const currentCenterTime = (this.player.zoomOffset + (visibleDuration / this.player.duration) * 0.5) * this.player.duration;

                // Double the zoom level
                this.player.zoomLevel = Math.min(this.player.zoomLevel * 2, 1000);

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
     * Set up speed control event listeners
     */
    setupSpeedControls() {
        // Delegate to the player's method
        if (this.player.setupSpeedEventListeners) {
            this.player.setupSpeedEventListeners();
        }
    }

    /**
     * Set up window event listeners
     */
    setupWindowEvents() {
        // Window resize handler to redraw canvas
        window.addEventListener('resize', () => {
            // Debounce resize events
            setTimeout(() => {
                this.player.redrawCurrentView();
                this.player.drawTimeline();
            }, 250);
        });
    }
}
