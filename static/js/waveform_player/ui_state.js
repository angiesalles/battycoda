/**
 * BattyCoda Waveform Player - UI State Management
 * 
 * Handles all UI state updates and display management
 */

export class UIState {
    constructor(player) {
        this.player = player;
    }

    /**
     * Update the time display and progress bar
     */
    updateTimeDisplay() {
        // Ensure currentTime is a valid number
        const time = Number.isFinite(this.player.currentTime) ? this.player.currentTime : 0;
        if (this.player.currentTimeEl) this.player.currentTimeEl.textContent = time.toFixed(2) + 's';
        
        // Avoid division by zero if duration is not set
        const percentage = this.player.duration ? ((time / this.player.duration) * 100) : 0;
        if (this.player.progressBar) this.player.progressBar.style.width = percentage + '%';
        
        // If zoomed in, add a visual indicator of the current view in the progress bar
        if (this.player.zoomLevel > 1 && this.player.progressContainer) {
            // Remove any existing view indicator
            const existingIndicator = this.player.progressContainer.querySelector('.zoom-view-indicator');
            if (existingIndicator) {
                existingIndicator.remove();
            }
            
            // Calculate visible range as percentage of total duration
            const visibleDuration = this.player.duration / this.player.zoomLevel;
            const startPercent = (this.player.zoomOffset * this.player.duration / this.player.duration) * 100;
            const widthPercent = (visibleDuration / this.player.duration) * 100;
            
            // Create indicator element
            const indicator = document.createElement('div');
            indicator.className = 'zoom-view-indicator position-absolute';
            indicator.style.position = 'absolute';
            indicator.style.left = startPercent + '%';
            indicator.style.width = widthPercent + '%';
            indicator.style.height = '5px';
            indicator.style.bottom = '0';
            indicator.style.backgroundColor = 'rgba(255, 255, 255, 0.5)';
            indicator.style.borderRadius = '2px';
            indicator.style.pointerEvents = 'none'; // Don't interfere with clicks
            
            this.player.progressContainer.appendChild(indicator);
        } else if (this.player.progressContainer) {
            // Remove indicator if not zoomed
            const existingIndicator = this.player.progressContainer.querySelector('.zoom-view-indicator');
            if (existingIndicator) {
                existingIndicator.remove();
            }
        }
    }
    
    /**
     * Update the selection display
     */
    updateSelectionDisplay() {
        if (!this.player.allowSelection || !this.player.selectionRangeEl) return;
        
        if (this.player.selectionStart !== null && this.player.selectionEnd !== null) {
            const duration = this.player.selectionEnd - this.player.selectionStart;
            this.player.selectionRangeEl.textContent = 
                `Selected: ${this.player.selectionStart.toFixed(2)}s - ${this.player.selectionEnd.toFixed(2)}s (${duration.toFixed(2)}s)`;
        } else if (this.player.selectionStart !== null) {
            this.player.selectionRangeEl.textContent = 
                `Start: ${this.player.selectionStart.toFixed(2)}s (select end point)`;
        } else {
            this.player.selectionRangeEl.textContent = 'No selection';
        }
    }

    /**
     * Update play button states
     */
    updatePlayButtons() {
        if (this.player.isPlaying) {
            if (this.player.playBtn) this.player.playBtn.disabled = true;
            if (this.player.pauseBtn) this.player.pauseBtn.disabled = false;
            if (this.player.stopBtn) this.player.stopBtn.disabled = false;
        } else {
            if (this.player.playBtn) this.player.playBtn.disabled = false;
            if (this.player.pauseBtn) this.player.pauseBtn.disabled = true;
            if (this.player.stopBtn) this.player.stopBtn.disabled = true;
        }
    }
}